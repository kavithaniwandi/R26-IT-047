"""Evaluate optional age65_abnormal_vitals raise-only layer on the severity test fold."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("robustness/outputs"), type=Path)
    return parser.parse_args()


def apply_age_layer(pred: np.ndarray, rows: pd.DataFrame) -> np.ndarray:
    raised = pred.copy()
    age = pd.to_numeric(rows["age"], errors="coerce")
    spo2 = pd.to_numeric(rows["vital_spo2"], errors="coerce")
    sbp = pd.to_numeric(rows["vital_sbp"], errors="coerce")
    hr = pd.to_numeric(rows["vital_hr"], errors="coerce")
    rr = pd.to_numeric(rows["vital_rr"], errors="coerce")
    abnormal = ((spo2 < 94).fillna(False).astype(int)
                + (sbp < 90).fillna(False).astype(int)
                + (hr > 110).fillna(False).astype(int)
                + (rr > 22).fillna(False).astype(int))
    age65 = (age >= 65).fillna(False)
    raised[age65 & (abnormal == 1) & (raised < 1)] = 1
    raised[age65 & (abnormal >= 2) & (raised < 2)] = 2
    return raised


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "n_rows": int(len(y_true)),
        "n_high": int(np.sum(y_true == 2)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "high_recall": float(recall_score(y_true == 2, y_pred == 2, zero_division=0)),
        "high_to_low": int(np.sum((y_true == 2) & (y_pred == 0))),
        "medium_to_high": int(np.sum((y_true == 1) & (y_pred == 2))),
    }


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
    folds = list(StratifiedGroupKFold(10, shuffle=True, random_state=SEED).split(df, df["y"], groups=df[GROUP_COL]))
    te = df.iloc[folds[0][1]].reset_index(drop=True)
    y = te["y"].to_numpy()
    pred_off = ml._load_bundle().predict(te[input_cols])["final_pred"]
    pred_on = apply_age_layer(np.asarray(pred_off, dtype=int), te)
    age65_mask = pd.to_numeric(te["age"], errors="coerce").fillna(-1).to_numpy() >= 65

    rows = [
        {"setting": "off", "subgroup": "overall", **metrics(y, pred_off)},
        {"setting": "on", "subgroup": "overall", **metrics(y, pred_on)},
        {"setting": "off", "subgroup": "age_ge_65", **metrics(y[age65_mask], pred_off[age65_mask])},
        {"setting": "on", "subgroup": "age_ge_65", **metrics(y[age65_mask], pred_on[age65_mask])},
    ]
    out = pd.DataFrame(rows)
    csv_path = args.out_dir / "severity_age65_layer_results.csv"
    md_path = args.out_dir / "severity_age65_layer_summary.md"
    out.to_csv(csv_path, index=False)
    md_path.write_text("# Age65 Abnormal Vitals Layer\n\n" + out.to_markdown(index=False) + "\n", encoding="utf-8")
    print(out.to_string(index=False))
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
