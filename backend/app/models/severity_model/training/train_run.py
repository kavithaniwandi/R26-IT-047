"""Local provenance check for the deployed SDRDCS severity model.

This script does not retrain or redeploy. It loads the live model bundle in the
parent severity_model folder, reproduces the notebook split, and prints the
held-out test metrics that should match metrics.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold


STRICT_VERSIONS = True
SEED = 42
LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
EXPECTED_LIBS = {
    "numpy": "1.26.4",
    "sklearn": "1.7.2",
    "xgboost": "2.1.4",
    "lightgbm": "4.7.0",
}


HERE = Path(__file__).resolve().parent
MODEL_DIR = HERE.parent
BACKEND_DIR = HERE.parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Path to nhamcs_2022_camp_relabeled_v2.csv")
    return parser.parse_args()


def current_versions() -> dict[str, str]:
    import lightgbm
    import numpy
    import sklearn
    import xgboost

    return {
        "numpy": numpy.__version__,
        "sklearn": sklearn.__version__,
        "xgboost": xgboost.__version__,
        "lightgbm": lightgbm.__version__,
    }


def main() -> None:
    args = parse_args()
    actual = current_versions()
    if STRICT_VERSIONS and actual != EXPECTED_LIBS:
        raise RuntimeError(f"Version mismatch: expected {EXPECTED_LIBS}, got {actual}")

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
    idx_test = folds[0][1]
    te = df.iloc[idx_test].reset_index(drop=True)

    bundle = sp.load_bundle(str(MODEL_DIR / "severity_bundle.joblib"))
    pred = np.asarray(bundle.predict(te[input_cols])["final_pred"], dtype=int)
    y = te["y"].to_numpy()
    manifest = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))

    metrics = {
        "n": int(len(y)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "high_recall": float(recall_score(y == 2, pred == 2, zero_division=0)),
        "high_to_low": int(np.sum((y == 2) & (pred == 0))),
    }
    print(json.dumps({"versions": actual, "test": metrics, "metrics_json_test": manifest["metrics"]["test"]}, indent=2))


if __name__ == "__main__":
    main()
