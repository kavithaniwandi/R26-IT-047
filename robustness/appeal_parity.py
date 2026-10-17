"""Evaluate the live donation appeal quality model on saved held-out rows."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

LABELS = ["low", "medium", "high"]


def model_dir() -> Path:
    configured = os.environ.get("APPEAL_MODEL_DIR")
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else BACKEND_DIR / path
    return BACKEND_DIR / "ml_models" / "Donation Appeal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("robustness/outputs"), type=Path)
    parser.add_argument("--bootstrap", default=5000, type=int)
    return parser.parse_args()


def metrics(y_true: np.ndarray, y_pred: np.ndarray, s_true: np.ndarray, s_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "mae": float(mean_absolute_error(s_true, s_pred)),
        "r2": float(r2_score(s_true, s_pred)),
    }


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    s_true: np.ndarray,
    s_pred: np.ndarray,
    repeats: int,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    values = {name: [] for name in ["accuracy", "balanced_accuracy", "macro_f1", "mae", "r2"]}
    for _ in range(repeats):
        idx = rng.choice(np.arange(n), size=n, replace=True)
        row = metrics(y_true[idx], y_pred[idx], s_true[idx], s_pred[idx])
        for name, value in row.items():
            values[name].append(value)
    return {
        name: {
            "p2_5": float(np.percentile(metric_values, 2.5)),
            "p97_5": float(np.percentile(metric_values, 97.5)),
        }
        for name, metric_values in values.items()
    }


def select_test_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, str, int | None]:
    artifact_dir = model_dir()
    test_indices_path = artifact_dir / "appeal_quality_test_indices.npy"
    selected_indices_path = artifact_dir / "appeal_quality_selected_indices.npy"
    if test_indices_path.exists():
        test_indices = set(np.load(test_indices_path).astype(int).tolist())
        test = df[df["_orig_index"].isin(test_indices)].copy().reset_index(drop=True)
        selected_count = int(len(np.load(selected_indices_path))) if selected_indices_path.exists() else None
        return test, str(test_indices_path), selected_count

    _train, test = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["quality_label"],
    )
    return (
        test.reset_index(drop=True),
        "fallback train_test_split(test_size=0.2, random_state=42, stratify=quality_label)",
        None,
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    from app.models.quality_service import _handcrafted, _load_artifacts, _normalise_language, _resolve_label

    df = pd.read_csv(args.data, low_memory=False)
    required = {"appeal_text", "language", "quality_label", "overall_quality_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df = df.dropna(subset=["appeal_text", "language", "quality_label", "overall_quality_score"]).copy()
    df["_orig_index"] = df.index.astype(int)
    df["quality_label"] = df["quality_label"].astype(str).str.lower().str.strip()
    df = df[df["quality_label"].isin(LABELS)].copy()

    test, split_source, selected_count = select_test_rows(df)
    artifacts = _load_artifacts()
    languages = test["language"].map(_normalise_language).to_numpy()
    texts = test["appeal_text"].astype(str).tolist()
    hand_raw = np.vstack([_handcrafted(text, language, artifacts) for text, language in zip(texts, languages)])
    hand_scaled = artifacts["scaler"].transform(hand_raw)

    n = len(test)
    lsa_components = artifacts["cfg"]["lsa_components"]
    lsa_en = np.zeros((n, lsa_components["en"]))
    lsa_si = np.zeros((n, lsa_components["si"]))
    lsa_ta = np.zeros((n, lsa_components["ta"]))
    clf_en = csr_matrix((n, artifacts["N_EN"]), dtype=np.float64)
    clf_si = csr_matrix((n, artifacts["N_SI"]), dtype=np.float64)
    clf_ta = csr_matrix((n, artifacts["N_TA"]), dtype=np.float64)

    for language, tfidf_key, svd_key, lsa_target, clf_target in [
        ("English", "tfidf_en", "svd_en", lsa_en, "en"),
        ("Sinhala", "tfidf_si", "svd_si", lsa_si, "si"),
        ("Tamil", "tfidf_ta", "svd_ta", lsa_ta, "ta"),
    ]:
        idx = np.where(languages == language)[0]
        if len(idx) == 0:
            continue
        tfidf = artifacts[tfidf_key].transform([texts[i] for i in idx])
        lsa_target[idx, :] = artifacts[svd_key].transform(tfidf)
        if clf_target == "en":
            clf_en[idx, :] = tfidf
        elif clf_target == "si":
            clf_si[idx, :] = tfidf
        else:
            clf_ta[idx, :] = tfidf

    x_clf = hstack([csr_matrix(hand_scaled), clf_en, clf_si, clf_ta])
    proba = artifacts["clf"].predict_proba(x_clf)
    x_reg = np.hstack([proba, hand_scaled, lsa_en, lsa_si, lsa_ta])
    raw_score = np.clip(artifacts["reg"].predict(x_reg), 1.0, 5.0)
    pred_score = np.clip(artifacts["iso"].predict(raw_score), 1.0, 5.0)
    pred_label = np.asarray([_resolve_label(float(score), proba_row, artifacts) for score, proba_row in zip(pred_score, proba)])

    y_true = test["quality_label"].to_numpy()
    s_true = test["overall_quality_score"].astype(float).to_numpy()
    overall = {
        "n_corpus": int(len(df)),
        "n_selected": selected_count,
        "n_test": int(len(test)),
        "split_source": split_source,
        **metrics(y_true, pred_label, s_true, pred_score),
    }
    intervals = bootstrap_ci(y_true, pred_label, s_true, pred_score, args.bootstrap)
    overall["bootstrap_repeats"] = int(args.bootstrap)
    overall["bootstrap_95ci"] = intervals

    pred = pd.DataFrame(
        {
            "orig_index": test["_orig_index"].to_numpy(),
            "language": languages,
            "true_label": y_true,
            "pred_label": pred_label,
            "true_score": s_true,
            "pred_score": pred_score,
            "confidence": proba.max(axis=1),
            "low_confidence": proba.max(axis=1) < 0.5,
        }
    )
    per_language = []
    for language, subset in pred.groupby("language"):
        per_language.append(
            {
                "language": language,
                "n": int(len(subset)),
                **metrics(
                    subset["true_label"].to_numpy(),
                    subset["pred_label"].to_numpy(),
                    subset["true_score"].to_numpy(),
                    subset["pred_score"].to_numpy(),
                ),
            }
        )
    per_lang_df = pd.DataFrame(per_language)

    flat = {key: value for key, value in overall.items() if key != "bootstrap_95ci"}
    for name, bounds in intervals.items():
        flat[f"{name}_ci_low"] = bounds["p2_5"]
        flat[f"{name}_ci_high"] = bounds["p97_5"]

    pred_path = args.out_dir / "appeal_parity_predictions.csv"
    metrics_path = args.out_dir / "appeal_parity_metrics.csv"
    json_path = args.out_dir / "appeal_parity_metrics.json"
    md_path = args.out_dir / "appeal_parity_summary.md"
    pred.to_csv(pred_path, index=False)
    pd.DataFrame([flat]).to_csv(metrics_path, index=False)
    json_path.write_text(json.dumps(overall, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Appeal Parity Summary",
                "",
                f"- Corpus rows after filtering: {overall['n_corpus']}",
                f"- Selected rows used by saved training protocol: {overall['n_selected'] if overall['n_selected'] is not None else 'NOT FOUND'}",
                f"- Test rows: {overall['n_test']}",
                f"- Split source: `{split_source}`",
                "",
                "## Overall",
                "",
                pd.DataFrame([{k: v for k, v in overall.items() if k != "bootstrap_95ci"}]).to_markdown(index=False),
                "",
                "## 95% Bootstrap Intervals",
                "",
                pd.DataFrame(
                    [{"metric": name, "p2_5": bounds["p2_5"], "p97_5": bounds["p97_5"]} for name, bounds in intervals.items()]
                ).to_markdown(index=False),
                "",
                "## Per Language",
                "",
                per_lang_df.to_markdown(index=False),
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(pd.DataFrame([flat]).to_string(index=False))
    print(per_lang_df.to_string(index=False))
    print(f"Wrote {metrics_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {pred_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
