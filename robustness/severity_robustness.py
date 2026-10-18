"""
Run robustness checks for the live patient severity triage bundle.

This script is intentionally read-only with respect to repository files. It
loads the live bundle under backend/app/models/severity_model/ and writes its
CSV/Markdown outputs to the chosen output directory.

Required input:
    nhamcs_2022_camp_relabeled_v2.csv

Example:
    python robustness/severity_robustness.py ^
      --data C:\\path\\to\\nhamcs_2022_camp_relabeled_v2.csv ^
      --out-dir robustness\\outputs

Use --allow-version-mismatch only for diagnostic runs. Exact parity with
metrics.json requires the pinned versions recorded in that file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
SEED = 42
N_SPLIT_FOLDS = 10
REPEATS = 20
VITAL_UNITS = {
    "vital_hr": "beats/min",
    "vital_spo2": "%",
    "vital_sbp": "mmHg",
    "vital_rr": "breaths/min",
    "vital_temp": "C",
    "pain_score": "0-10 integer scale",
}
VALID_RANGES = {
    "vital_hr": (20.0, 250.0),
    "vital_spo2": (50.0, 100.0),
    "vital_sbp": (50.0, 300.0),
    "vital_rr": (4.0, 80.0),
    "vital_temp": (30.0, 43.0),
    "pain_score": (0.0, 10.0),
}
INJURY_COL_CANDIDATES = (
    "INJURY",
    "injury",
    "injury_visit",
    "is_injury",
    "INJURY72",
    "RFV_INJURY",
)
INJURY_LIKE_COMPLAINT_KEYWORDS = (
    "fall",
    "fracture",
    "laceration",
    "wound",
    "burn",
    "bleeding",
    "trauma",
    "injury",
    "crush",
    "drowning",
    "stab",
    "gunshot",
    "sprain",
    "dislocation",
)
RECORD_ID_CANDIDATES = (
    "record_id",
    "case_id",
    "patient_id",
    "visit_id",
    "encounter_id",
    "edvisit_id",
    "nhamcs_id",
    "PATCODE",
    "PATID",
    "VISITID",
)


@dataclass(frozen=True)
class SplitData:
    df: pd.DataFrame
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    input_cols: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Path to nhamcs_2022_camp_relabeled_v2.csv")
    parser.add_argument("--out-dir", default=Path("robustness/outputs"), type=Path)
    parser.add_argument("--injury-col", default=None, help="NHAMCS injury indicator column; auto-detected if omitted")
    parser.add_argument(
        "--allow-version-mismatch",
        action="store_true",
        help="Set SEVERITY_ALLOW_VERSION_MISMATCH=1 for diagnostic runs.",
    )
    parser.add_argument("--repeats", default=REPEATS, type=int)
    return parser.parse_args()


def load_live_modules(allow_version_mismatch: bool):
    if allow_version_mismatch:
        os.environ["SEVERITY_ALLOW_VERSION_MISMATCH"] = "1"
    from app.models.complaint_mapper import ComplaintMapper
    from app.models import severity_ml_service as ml
    from app.models import severity_pipeline as sp

    bundle = ml._load_bundle()
    mapper = ComplaintMapper(bundle.features.complaint_vec_.vocabulary_)
    return ml, sp, bundle, mapper


def reproduce_split(data_path: Path, sp) -> SplitData:
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {data_path}. Provide nhamcs_2022_camp_relabeled_v2.csv with --data."
        )

    df = pd.read_csv(data_path, low_memory=False)
    input_cols = (
        ["symptoms", "age", "has_red_flag", "red_flag_count"]
        + [f"rf_{flag}" for flag in sp.KNOWN_FLAGS]
        + list(sp.VITAL_COLS)
    )
    missing = [col for col in input_cols + [LABEL_COL, GROUP_COL] if col not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df[df[LABEL_COL].isin(sp.LABEL_MAP)].reset_index(drop=True)
    df["y"] = df[LABEL_COL].map(sp.LABEL_MAP).astype(int)

    folds = list(
        StratifiedGroupKFold(N_SPLIT_FOLDS, shuffle=True, random_state=SEED).split(
            df, df["y"], groups=df[GROUP_COL]
        )
    )
    idx_test, idx_val = folds[0][1], folds[1][1]
    idx_train = np.setdiff1d(np.arange(len(df)), np.r_[idx_test, idx_val])
    train, val, test = (df.iloc[idx].reset_index(drop=True) for idx in (idx_train, idx_val, idx_test))

    if set(train[GROUP_COL]) & set(val[GROUP_COL]):
        raise AssertionError("profile leaked between train and val")
    if set(train[GROUP_COL]) & set(test[GROUP_COL]):
        raise AssertionError("profile leaked between train and test")
    if set(val[GROUP_COL]) & set(test[GROUP_COL]):
        raise AssertionError("profile leaked between val and test")

    return SplitData(df=df, train=train, val=val, test=test, input_cols=input_cols)


def predict(bundle, rows: pd.DataFrame, input_cols: list[str]) -> np.ndarray:
    return np.asarray(bundle.predict(rows[input_cols])["final_pred"], dtype=int)


def mean_complaint_nonzero(bundle, rows: pd.DataFrame) -> float:
    complaint_matrix = bundle.features.complaint_vec_.transform(rows["symptoms"])
    return float(np.mean(complaint_matrix.getnnz(axis=1)))


def free_text_symptoms(value) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace("|", " and ").lower()
    return f"patient complains of {text}"


def mapped_symptoms(mapper, value) -> str:
    text = "" if pd.isna(value) else str(value)
    mapped = mapper.map(text)
    return "|".join(mapped) if mapped else text


def high_to_low(y_true: np.ndarray, y_pred: np.ndarray) -> int:
    return int(np.sum((y_true == 2) & (y_pred == 0)))


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "high_recall": float(recall_score(y_true == 2, y_pred == 2, zero_division=0)),
        "high_to_low": float(high_to_low(y_true, y_pred)),
        "n": float(len(y_true)),
        "n_high": float(np.sum(y_true == 2)),
    }


def interval(values: Iterable[float]) -> tuple[float, float, float]:
    arr = np.asarray(list(values), dtype=float)
    return float(np.mean(arr)), float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def append_summary_rows(rows: list[dict], experiment: str, level: str, repeats: list[dict]) -> None:
    for metric_name in ("high_recall", "high_to_low", "balanced_accuracy"):
        mean, lo, hi = interval(run[metric_name] for run in repeats)
        rows.append(
            {
                "experiment": experiment,
                "level": level,
                "metric": metric_name,
                "mean": mean,
                "p2_5": lo,
                "p97_5": hi,
                "n_rows": repeats[0]["n"],
                "n_high": repeats[0]["n_high"],
                "repeats": len(repeats),
            }
        )


def missing_vitals_experiment(bundle, split: SplitData, repeats: int) -> list[dict]:
    rows = []
    y = split.test["y"].to_numpy()
    for p in (0.1, 0.2, 0.3, 0.5):
        run_metrics = []
        for offset in range(repeats):
            rng = np.random.default_rng(SEED + 1000 + offset)
            perturbed = split.test.copy()
            for col in VITAL_UNITS:
                mask = rng.random(len(perturbed)) < p
                perturbed.loc[mask, col] = np.nan
            run_metrics.append(metrics(y, predict(bundle, perturbed, split.input_cols)))
        append_summary_rows(rows, "missing_vitals", f"p={p}", run_metrics)
    return rows


def noise_experiment(bundle, split: SplitData, repeats: int) -> list[dict]:
    rows = []
    y = split.test["y"].to_numpy()
    train_sd = split.train[list(VITAL_UNITS)].apply(pd.to_numeric, errors="coerce").std()
    for pct in (0.05, 0.10):
        run_metrics = []
        for offset in range(repeats):
            rng = np.random.default_rng(SEED + 2000 + offset)
            perturbed = split.test.copy()
            for col in VITAL_UNITS:
                numeric = pd.to_numeric(perturbed[col], errors="coerce")
                noise = rng.normal(0.0, pct * float(train_sd[col]), size=len(perturbed))
                lo, hi = VALID_RANGES[col]
                perturbed[col] = (numeric + noise).clip(lo, hi)
            run_metrics.append(metrics(y, predict(bundle, perturbed, split.input_cols)))
        append_summary_rows(rows, "vital_noise", f"sd={int(pct * 100)}pct_training_sd", run_metrics)
    return rows


def free_text_input_experiment(bundle, mapper, split: SplitData, baseline: dict) -> list[dict]:
    y = split.test["y"].to_numpy()
    baseline_complaints = mean_complaint_nonzero(bundle, split.test)

    perturbed = split.test.copy()
    perturbed["symptoms"] = perturbed["symptoms"].map(free_text_symptoms)
    perturbed["symptoms"] = perturbed["symptoms"].map(lambda text: mapped_symptoms(mapper, text))
    y_pred = predict(bundle, perturbed, split.input_cols)
    result = metrics(y, y_pred)
    free_text_complaints = mean_complaint_nonzero(bundle, perturbed)

    rows = []
    for metric_name in ("balanced_accuracy", "macro_f1", "high_recall", "high_to_low"):
        rows.append(
            {
                "experiment": "free_text_input",
                "level": "patient_complains_prefix_pipe_to_and_mapped",
                "metric": metric_name,
                "mean": result[metric_name],
                "p2_5": result[metric_name],
                "p97_5": result[metric_name],
                "n_rows": result["n"],
                "n_high": result["n_high"],
                "repeats": 1,
                "baseline_mean": baseline[metric_name],
                "delta_from_baseline": result[metric_name] - baseline[metric_name],
            }
        )

    rows.extend(
        [
            {
                "experiment": "free_text_input",
                "level": "baseline",
                "metric": "mean_complaint_nonzero",
                "mean": baseline_complaints,
                "p2_5": baseline_complaints,
                "p97_5": baseline_complaints,
                "n_rows": baseline["n"],
                "n_high": baseline["n_high"],
                "repeats": 1,
                "baseline_mean": baseline_complaints,
                "delta_from_baseline": 0.0,
            },
            {
                "experiment": "free_text_input",
                "level": "patient_complains_prefix_pipe_to_and_mapped",
                "metric": "mean_complaint_nonzero",
                "mean": free_text_complaints,
                "p2_5": free_text_complaints,
                "p97_5": free_text_complaints,
                "n_rows": result["n"],
                "n_high": result["n_high"],
                "repeats": 1,
                "baseline_mean": baseline_complaints,
                "delta_from_baseline": free_text_complaints - baseline_complaints,
            },
        ]
    )
    return rows


def detect_injury_col(df: pd.DataFrame, override: str | None) -> str:
    if override:
        if override not in df.columns:
            raise ValueError(f"--injury-col {override!r} not found in CSV")
        return override
    for col in INJURY_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise ValueError(
        "Could not auto-detect injury indicator column. Pass --injury-col. "
        f"Tried: {', '.join(INJURY_COL_CANDIDATES)}"
    )


def injury_mask(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0) > 0
    return series.astype(str).str.strip().str.lower().isin({"1", "yes", "y", "true", "injury"})


def injury_like_complaint_mask(symptoms: pd.Series) -> pd.Series:
    pattern = "|".join(INJURY_LIKE_COMPLAINT_KEYWORDS)
    return symptoms.fillna("").astype(str).str.contains(pattern, case=False, regex=True)


def detect_record_id_cols(df: pd.DataFrame) -> list[str]:
    columns = set(df.columns)
    return [col for col in RECORD_ID_CANDIDATES if col in columns]


def subgroup_experiment(bundle, split: SplitData, injury_col: str) -> list[dict]:
    y_pred = predict(bundle, split.test, split.input_cols)
    y_true = split.test["y"].to_numpy()
    age = pd.to_numeric(split.test["age"], errors="coerce")
    injury = injury_mask(split.test[injury_col])

    masks = {
        "injury_visits": injury,
        "injury_like_complaint_proxy": injury_like_complaint_mask(split.test["symptoms"]),
        "age_lt_18": age < 18,
        "age_ge_65": age >= 65,
        "rest": ~(injury | (age < 18) | (age >= 65)),
    }
    rows = []
    for name, mask in masks.items():
        mask_arr = np.asarray(mask.fillna(False), dtype=bool)
        if not np.any(mask_arr):
            rows.append(
                {
                    "experiment": "subgroup",
                    "level": name,
                    "metric": "all",
                    "mean": np.nan,
                    "p2_5": np.nan,
                    "p97_5": np.nan,
                    "n_rows": 0,
                    "n_high": 0,
                    "repeats": 1,
                    "injury_col": injury_col,
                }
            )
            continue
        result = metrics(y_true[mask_arr], y_pred[mask_arr])
        for metric_name in ("balanced_accuracy", "macro_f1", "high_recall", "high_to_low"):
            rows.append(
                {
                    "experiment": "subgroup",
                    "level": name,
                    "metric": metric_name,
                    "mean": result[metric_name],
                    "p2_5": result[metric_name],
                    "p97_5": result[metric_name],
                    "n_rows": result["n"],
                    "n_high": result["n_high"],
                    "repeats": 1,
                    "injury_col": injury_col,
                }
            )
    return rows


def prevalence_experiment(bundle, split: SplitData, repeats: int) -> list[dict]:
    y_pred_all = predict(bundle, split.test, split.input_cols)
    y_true_all = split.test["y"].to_numpy()
    high_idx = np.where(y_true_all == 2)[0]
    non_high_idx = np.where(y_true_all != 2)[0]
    n = len(y_true_all)
    rows = []

    for prevalence in (0.20, 0.35, 0.50):
        n_high = int(round(n * prevalence))
        n_non_high = n - n_high
        repeat_rows = []
        for offset in range(repeats):
            rng = np.random.default_rng(SEED + 3000 + offset)
            idx = np.r_[
                rng.choice(high_idx, size=n_high, replace=True),
                rng.choice(non_high_idx, size=n_non_high, replace=True),
            ]
            rng.shuffle(idx)
            y_true = y_true_all[idx]
            y_pred = y_pred_all[idx]
            fp_per_100 = float(np.sum((y_true != 2) & (y_pred == 2)) / len(idx) * 100.0)
            repeat_rows.append(
                {
                    "high_precision": float(precision_score(y_true == 2, y_pred == 2, zero_division=0)),
                    "high_recall": float(recall_score(y_true == 2, y_pred == 2, zero_division=0)),
                    "non_high_predicted_high_per_100": fp_per_100,
                    "n": float(len(idx)),
                    "n_high": float(np.sum(y_true == 2)),
                }
            )
        for metric_name in ("high_precision", "high_recall", "non_high_predicted_high_per_100"):
            mean, lo, hi = interval(run[metric_name] for run in repeat_rows)
            rows.append(
                {
                    "experiment": "prevalence_resample",
                    "level": f"high_prevalence={int(prevalence * 100)}pct",
                    "metric": metric_name,
                    "mean": mean,
                    "p2_5": lo,
                    "p97_5": hi,
                    "n_rows": repeat_rows[0]["n"],
                    "n_high": repeat_rows[0]["n_high"],
                    "repeats": repeats,
                }
            )
    return rows


def load_metrics_manifest() -> dict:
    path = BACKEND_DIR / "app" / "models" / "severity_model" / "metrics.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_markdown(
    out_path: Path,
    split: SplitData,
    summary: pd.DataFrame,
    baseline: dict,
    manifest: dict,
    injury_col: str | None,
) -> None:
    input_table = "\n".join(
        f"| `{col}` | {VITAL_UNITS.get(col, 'see code')} | "
        f"{VALID_RANGES.get(col, ('NA', 'NA'))[0]}-{VALID_RANGES.get(col, ('NA', 'NA'))[1]} |"
        for col in split.input_cols
        if col in VITAL_UNITS
    )
    red_flags = ", ".join(col for col in split.input_cols if col.startswith("rf_"))
    test_manifest = manifest["metrics"]["test"]
    record_id_cols = detect_record_id_cols(split.df)
    record_id_summary = ", ".join(f"`{col}`" for col in record_id_cols) if record_id_cols else "NOT FOUND IN CSV"
    lines = [
        "# Severity Robustness Summary",
        "",
        "## Split",
        "",
        f"- Data rows after label filtering: {len(split.df)}",
        f"- Train n: {len(split.train)}; validation n: {len(split.val)}; test n: {len(split.test)}",
        f"- Split code: `StratifiedGroupKFold(10, shuffle=True, random_state={SEED})`; test fold `folds[0][1]`, validation fold `folds[1][1]`.",
        f"- Label column: `{LABEL_COL}`; group column: `{GROUP_COL}`.",
        f"- Injury column used: `{injury_col}`" if injury_col else "- Injury column used: NOT RUN.",
        f"- Record ID column for joining to raw NHAMCS injury indicator: {record_id_summary}.",
        "",
        "## Baseline",
        "",
        f"- Balanced accuracy: {baseline['balanced_accuracy']:.6f} (metrics.json test: {test_manifest['bal_acc']:.6f})",
        f"- Macro-F1: {baseline['macro_f1']:.6f} (metrics.json test: {test_manifest['macro_f1']:.6f})",
        f"- HIGH recall: {baseline['high_recall']:.6f} (metrics.json test: {test_manifest['high_recall']:.6f})",
        f"- HIGH-to-LOW count: {int(baseline['high_to_low'])} (metrics.json test: {test_manifest['high_to_low']})",
        "",
        "## Columns And Units",
        "",
        "| Column | Unit | Valid range used for clipping |",
        "|---|---:|---:|",
        input_table,
        "",
        f"Red-flag columns: {red_flags}.",
        "",
        "## Results",
        "",
        "The full machine-readable table is in `severity_robustness_results.csv`. "
        "Intervals are empirical 2.5th and 97.5th percentiles over repeats.",
        "",
    ]
    for experiment in summary["experiment"].dropna().unique():
        lines.extend([f"### {experiment}", ""])
        subset = summary[summary["experiment"] == experiment]
        lines.append(subset.to_markdown(index=False))
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    _ml, sp, bundle, mapper = load_live_modules(args.allow_version_mismatch)
    split = reproduce_split(args.data, sp)
    manifest = load_metrics_manifest()

    y_test = split.test["y"].to_numpy()
    pred_test = predict(bundle, split.test, split.input_cols)
    baseline = metrics(y_test, pred_test)

    rows = [
        {
            "experiment": "baseline",
            "level": "test",
            "metric": key,
            "mean": value,
            "p2_5": value,
            "p97_5": value,
            "n_rows": baseline["n"],
            "n_high": baseline["n_high"],
            "repeats": 1,
        }
        for key, value in baseline.items()
        if key not in {"n", "n_high"}
    ]
    rows.extend(missing_vitals_experiment(bundle, split, args.repeats))
    rows.extend(noise_experiment(bundle, split, args.repeats))
    rows.extend(free_text_input_experiment(bundle, mapper, split, baseline))

    injury_col = detect_injury_col(split.test, args.injury_col)
    rows.extend(subgroup_experiment(bundle, split, injury_col))
    rows.extend(prevalence_experiment(bundle, split, args.repeats))

    summary = pd.DataFrame(rows)
    csv_path = args.out_dir / "severity_robustness_results.csv"
    md_path = args.out_dir / "severity_robustness_summary.md"
    summary.to_csv(csv_path, index=False)
    write_markdown(md_path, split, summary, baseline, manifest, injury_col)

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
