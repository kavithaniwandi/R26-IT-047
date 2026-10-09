"""Generate typed-note stress tests from the NHAMCS severity test fold.

This is not clinical validation. It transforms existing coded test-fold rows
into prose-like notes and sends them through the live severity service.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold


HERE = Path(__file__).resolve()
BACKEND_DIR = HERE.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models import severity_pipeline as sp  # noqa: E402
from app.models.severity_service import classify_note  # noqa: E402


LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
SEED = 42
INPUT_COLS = (
    ["symptoms", "age", "has_red_flag", "red_flag_count"]
    + [f"rf_{flag}" for flag in sp.KNOWN_FLAGS]
    + list(sp.VITAL_COLS)
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out", default=Path("tests/typed_note_stress_report.json"), type=Path)
    parser.add_argument("--high-to-low-limit", default=5, type=int)
    return parser.parse_args()


def test_fold(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path, low_memory=False)
    df = df[df[LABEL_COL].isin(sp.LABEL_MAP)].reset_index(drop=True)
    df["y"] = df[LABEL_COL].map(sp.LABEL_MAP).astype(int)
    folds = list(
        StratifiedGroupKFold(10, shuffle=True, random_state=SEED).split(
            df, df["y"], groups=df[GROUP_COL]
        )
    )
    return df.iloc[folds[0][1]].reset_index(drop=True)


def complaints(row: pd.Series) -> list[str]:
    return [part.strip() for part in str(row["symptoms"]).split("|") if part.strip()]


def typo(text: str) -> str:
    replacements = {
        "chest": "chesst",
        "pain": "paen",
        "breath": "breth",
        "fracture": "fractur",
        "vomiting": "vomting",
        "fever": "fevr",
        "injury": "injry",
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def vital_sentence(row: pd.Series) -> str:
    fields = [
        ("HR", "vital_hr"),
        ("SpO2", "vital_spo2"),
        ("SBP", "vital_sbp"),
        ("RR", "vital_rr"),
        ("temp", "vital_temp"),
        ("pain", "pain_score"),
    ]
    parts = []
    for label, col in fields:
        value = row.get(col)
        if pd.notna(value):
            parts.append(f"{label} {value}")
    return ", ".join(parts)


def make_note(row: pd.Series, template: str, rng: random.Random) -> str:
    parts = complaints(row)
    lowered = [part.lower() for part in parts]
    if template == "patient_complains":
        return "Patient complains of " + " and ".join(lowered)
    if template == "lowercase_typos":
        return "patient complains of " + typo(" and ".join(lowered))
    if template == "shuffled_order":
        shuffled = lowered[:]
        rng.shuffle(shuffled)
        return "Patient complains of " + " and ".join(shuffled)
    if template == "dropped_words":
        dropped = []
        for part in lowered:
            words = part.split()
            dropped.append(" ".join(words[:-1] if len(words) > 1 else words))
        return "Patient complains of " + " and ".join(filter(None, dropped))
    if template == "age_vitals_embedded":
        return f"{int(row['age']) if pd.notna(row['age']) else 'unknown age'} year old. Patient complains of {' and '.join(lowered)}. Vitals: {vital_sentence(row)}."
    raise ValueError(template)


def classify_row(row: pd.Series, note: str) -> int:
    flags = {flag: int(row.get(f"rf_{flag}", 0)) for flag in sp.KNOWN_FLAGS if int(row.get(f"rf_{flag}", 0) or 0)}
    vitals = {col: (None if pd.isna(row[col]) else float(row[col])) for col in sp.VITAL_COLS}
    result = classify_note(
        clinical_note=note,
        age=None if pd.isna(row["age"]) else int(row["age"]),
        mode="ml",
        vitals=vitals,
        has_red_flag=int(row.get("has_red_flag", 0) or 0),
        red_flag_count=int(row.get("red_flag_count", 0) or 0),
        rf_flags=flags,
        symptoms="",
    )
    severity = "HIGH" if result["severity"] == "CRITICAL" else result["severity"]
    return sp.LABEL_MAP[severity]


def template_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "high_recall": float(recall_score(y_true == 2, y_pred == 2, zero_division=0)),
        "high_to_low": int(np.sum((y_true == 2) & (y_pred == 0))),
        "medium_to_high": int(np.sum((y_true == 1) & (y_pred == 2))),
    }


def main() -> None:
    args = parse_args()
    te = test_fold(args.data)
    y_true = te["y"].to_numpy()
    rng = random.Random(SEED)
    templates = ["patient_complains", "lowercase_typos", "shuffled_order", "dropped_words", "age_vitals_embedded"]
    report = {"n": int(len(te)), "n_high": int(np.sum(y_true == 2)), "templates": {}}
    failures = []
    for template in templates:
        y_pred = np.asarray([classify_row(row, make_note(row, template, rng)) for _, row in te.iterrows()])
        result = template_metrics(y_true, y_pred)
        report["templates"][template] = result
        if result["high_to_low"] > args.high_to_low_limit:
            failures.append((template, result["high_to_low"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(f"HIGH-to-LOW exceeded limit {args.high_to_low_limit}: {failures}")


if __name__ == "__main__":
    main()
