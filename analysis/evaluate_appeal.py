from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    r2_score,
    recall_score,
)


ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "robustness/outputs/appeal_parity_predictions.csv"
OUTPUT = ROOT / "backend/ml_models/Donation Appeal/appeal_eval.json"
LABELS = ["low", "medium", "high"]


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> dict[str, float]:
    if n == 0:
        return {"low": 0.0, "high": 0.0}
    phat = successes / n
    denom = 1 + z**2 / n
    centre = phat + z**2 / (2 * n)
    margin = z * np.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)
    return {
        "low": float((centre - margin) / denom),
        "high": float((centre + margin) / denom),
    }


def confusion_dict(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    matrix = confusion_matrix(frame["true_label"], frame["pred_label"], labels=LABELS)
    return {
        f"true_{label}": {
            f"pred_{pred_label}": int(matrix[row_index, col_index])
            for col_index, pred_label in enumerate(LABELS)
        }
        for row_index, label in enumerate(LABELS)
    }


def metrics_for(frame: pd.DataFrame) -> dict:
    correct = int((frame["true_label"] == frame["pred_label"]).sum())
    n = int(len(frame))
    return {
        "n": n,
        "accuracy": float(accuracy_score(frame["true_label"], frame["pred_label"])),
        "accuracy_wilson_95": wilson_interval(correct, n),
        "balanced_accuracy": float(balanced_accuracy_score(frame["true_label"], frame["pred_label"])),
        "macro_f1": float(f1_score(frame["true_label"], frame["pred_label"], labels=LABELS, average="macro", zero_division=0)),
        "per_class_recall": {
            label: float(value)
            for label, value in zip(
                LABELS,
                recall_score(frame["true_label"], frame["pred_label"], labels=LABELS, average=None, zero_division=0),
            )
        },
        "mae": float(mean_absolute_error(frame["true_score"], frame["pred_score"])),
        "r_squared": float(r2_score(frame["true_score"], frame["pred_score"])),
    }


def main() -> None:
    df = pd.read_csv(PREDICTIONS)

    payload = metrics_for(df)
    payload["per_language"] = {
        language: {
            "n": int(len(group)),
            "accuracy": float(accuracy_score(group["true_label"], group["pred_label"])),
        }
        for language, group in sorted(df.groupby("language"), key=lambda item: item[0])
    }
    payload["confusion_matrices"] = {"overall": confusion_dict(df)}
    for language, group in sorted(df.groupby("language"), key=lambda item: item[0]):
        payload["confusion_matrices"][language] = confusion_dict(group)
    payload["source_predictions"] = str(PREDICTIONS.relative_to(ROOT))

    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
