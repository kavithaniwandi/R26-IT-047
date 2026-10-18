"""Ablate severity safety layers on the NHAMCS held-out test split."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
SEED = 42
HIGH_RECALL_FLOOR = 0.90
N_BOOTSTRAP = 5000
LAYER_VARIANTS = {
    "model_only_no_safety_layers": (),
    "red_flag_only": ("red_flag",),
    "complaint_only": ("complaint",),
    "both_layers_baseline": ("red_flag", "complaint"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Path to nhamcs_2022_camp_relabeled_v2.csv")
    parser.add_argument("--out-dir", default=Path("robustness/outputs"), type=Path)
    parser.add_argument("--bootstrap", default=N_BOOTSTRAP, type=int)
    return parser.parse_args()


def predict_with_layers(sp, proba: np.ndarray, rows: pd.DataFrame, t_high: float, t_low: float, layers: tuple[str, ...]) -> np.ndarray:
    pred = sp.threshold_cascade(proba, t_high, t_low)
    if layers:
        pred = sp.apply_safety_layers(pred, rows, layers=layers)
    return pred


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "n_rows": float(len(y_true)),
        "n_high": float(np.sum(y_true == 2)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "high_recall": float(recall_score(y_true == 2, y_pred == 2, zero_division=0)),
        "high_to_low": float(np.sum((y_true == 2) & (y_pred == 0))),
        "medium_to_high": float(np.sum((y_true == 1) & (y_pred == 2))),
    }


def paired_bootstrap_intervals(
    y_true: np.ndarray,
    predictions: dict[str, np.ndarray],
    bootstrap_indices: np.ndarray,
) -> dict[str, dict[str, float]]:
    intervals = {}
    for name, pred in predictions.items():
        high_recall_values = []
        medium_to_high_values = []
        for idx in bootstrap_indices:
            y_b = y_true[idx]
            pred_b = pred[idx]
            high_recall_values.append(recall_score(y_b == 2, pred_b == 2, zero_division=0))
            medium_to_high_values.append(np.sum((y_b == 1) & (pred_b == 2)))
        intervals[name] = {
            "high_recall_ci_low": float(np.percentile(high_recall_values, 2.5)),
            "high_recall_ci_high": float(np.percentile(high_recall_values, 97.5)),
            "medium_to_high_ci_low": float(np.percentile(medium_to_high_values, 2.5)),
            "medium_to_high_ci_high": float(np.percentile(medium_to_high_values, 97.5)),
        }
    return intervals


def tune_thresholds(sp, proba: np.ndarray, rows: pd.DataFrame, y_true: np.ndarray, layers: tuple[str, ...]) -> tuple[float, float, float, float]:
    best = None
    fallback = None
    for t_high in np.arange(0.20, 0.81, 0.01):
        for t_low in np.arange(0.30, 0.81, 0.01):
            pred = predict_with_layers(sp, proba, rows, float(t_high), float(t_low), layers)
            bal = balanced_accuracy_score(y_true, pred)
            high_rec = recall_score(y_true == 2, pred == 2, zero_division=0)
            candidate = (bal, high_rec, float(t_high), float(t_low))
            if fallback is None or (high_rec, bal) > (fallback[1], fallback[0]):
                fallback = candidate
            if high_rec >= HIGH_RECALL_FLOOR and (best is None or bal > best[0]):
                best = candidate
    bal, high_rec, t_high, t_low = best if best is not None else fallback
    return t_high, t_low, bal, high_rec


def rows_for_predictions(
    y_true: np.ndarray,
    predictions: dict[str, np.ndarray],
    intervals: dict[str, dict[str, float]],
    threshold_by_variant: dict[str, tuple[float, float]],
    mode: str,
) -> list[dict[str, float | str]]:
    rows = []
    for name, pred in predictions.items():
        t_high, t_low = threshold_by_variant[name]
        rows.append(
            {
                "mode": mode,
                "variant": name,
                "t_high": t_high,
                "t_low": t_low,
                **metrics(y_true, pred),
                **intervals[name],
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    from app.models import severity_ml_service as ml
    from app.models import severity_pipeline as sp

    df = pd.read_csv(args.data, low_memory=False)
    input_cols = (
        ["symptoms", "age", "has_red_flag", "red_flag_count"]
        + [f"rf_{flag}" for flag in sp.KNOWN_FLAGS]
        + list(sp.VITAL_COLS)
    )
    df = df[df[LABEL_COL].isin(sp.LABEL_MAP)].reset_index(drop=True)
    df["y"] = df[LABEL_COL].map(sp.LABEL_MAP).astype(int)

    folds = list(
        StratifiedGroupKFold(10, shuffle=True, random_state=SEED).split(
            df, df["y"], groups=df[GROUP_COL]
        )
    )
    te = df.iloc[folds[0][1]].reset_index(drop=True)
    va = df.iloc[folds[1][1]].reset_index(drop=True)
    te_in = te[input_cols]
    va_in = va[input_cols]
    y = te["y"].to_numpy()
    y_va = va["y"].to_numpy()

    bundle = ml._load_bundle()
    proba_te = bundle.predict_proba(te_in)
    proba_va = bundle.predict_proba(va_in)

    fixed_predictions = {
        name: predict_with_layers(sp, proba_te, te_in, bundle.t_high, bundle.t_low, layers)
        for name, layers in LAYER_VARIANTS.items()
    }
    fixed_thresholds = {
        name: (bundle.t_high, bundle.t_low)
        for name in LAYER_VARIANTS
    }

    tuned_thresholds = {}
    tuned_predictions = {}
    tuning_rows = []
    for name, layers in LAYER_VARIANTS.items():
        t_high, t_low, val_bal, val_high_rec = tune_thresholds(sp, proba_va, va_in, y_va, layers)
        tuned_thresholds[name] = (t_high, t_low)
        tuned_predictions[name] = predict_with_layers(sp, proba_te, te_in, t_high, t_low, layers)
        tuning_rows.append(
            {
                "variant": name,
                "t_high": t_high,
                "t_low": t_low,
                "validation_balanced_accuracy": val_bal,
                "validation_high_recall": val_high_rec,
            }
        )

    rng = np.random.default_rng(SEED)
    bootstrap_indices = rng.integers(0, len(y), size=(args.bootstrap, len(y)))
    fixed_intervals = paired_bootstrap_intervals(y, fixed_predictions, bootstrap_indices)
    tuned_intervals = paired_bootstrap_intervals(y, tuned_predictions, bootstrap_indices)

    out = pd.DataFrame(
        rows_for_predictions(y, fixed_predictions, fixed_intervals, fixed_thresholds, "fixed_saved_thresholds")
        + rows_for_predictions(y, tuned_predictions, tuned_intervals, tuned_thresholds, "validation_retuned_thresholds")
    )
    tuning = pd.DataFrame(tuning_rows)
    csv_path = args.out_dir / "severity_ablation_results.csv"
    tuning_csv_path = args.out_dir / "severity_ablation_tuning.csv"
    md_path = args.out_dir / "severity_ablation_summary.md"
    out.to_csv(csv_path, index=False)
    tuning.to_csv(tuning_csv_path, index=False)
    md_path.write_text(
        "\n".join(
            [
                "# Severity Safety-Layer Ablation",
                "",
                f"- Test n: {len(te)}",
                f"- HIGH n: {int(np.sum(y == 2))}",
                f"- Validation n: {len(va)}",
                f"- Bootstrap resamples: {args.bootstrap}; the same resample indices are used for every row.",
                f"- Split: `StratifiedGroupKFold(10, shuffle=True, random_state={SEED})`; test fold `folds[0][1]`; validation fold `folds[1][1]`.",
                f"- Retuning rule: grid-search `T_HIGH=0.20..0.80`, `T_LOW=0.30..0.80` on validation; choose highest balanced accuracy subject to HIGH recall >= {HIGH_RECALL_FLOOR}.",
                "",
                "## Validation-Tuned Thresholds",
                "",
                tuning.to_markdown(index=False),
                "",
                "## Test Results",
                "",
                out.to_markdown(index=False),
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(out.to_string(index=False))
    print(f"Wrote {csv_path}")
    print(f"Wrote {tuning_csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
