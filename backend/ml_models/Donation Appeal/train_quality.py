"""Train the live donation appeal quality model with the paper protocol.

Expected corpus columns:
    appeal_text, language, overall_quality_score, quality_label,
    data_origin, source

The script saves artifacts under the same filenames loaded by
backend/app/models/quality_service.py, plus index/provenance files for parity.
By default it writes to v2_paper_protocol/ so live artifacts are not overwritten.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack, lil_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


SEED = 42
TARGET_ROWS = 5627
LABEL_ORDER = ["low", "medium", "high"]
AUGMENTED_ORIGINS = {
    "controlled_augmentation_native_reviewed",
    "controlled_augmentation_from_original_english",
    "AI_GENERATED_BOUNDARY_CASE",
    "AI_GENERATED_NOISY_CASE",
}
FEATURE_NAMES = [
    "log_text_len",
    "log_word_count",
    "avg_word_len",
    "sentence_count",
    "avg_sent_len",
    "exclamation_count",
    "question_count",
    "digit_ratio",
    "upper_ratio",
    "has_currency",
    "has_donate_word",
    "is_sinhala",
    "is_tamil",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path(__file__).resolve().parent / "v2_paper_protocol", type=Path)
    parser.add_argument("--seed", default=SEED, type=int)
    parser.add_argument("--target-rows", default=TARGET_ROWS, type=int)
    return parser.parse_args()


def extract_handcrafted(frame: pd.DataFrame) -> np.ndarray:
    text = frame["appeal_text"].astype(str)
    words = text.str.split().str.len()
    length = text.str.len()
    sentences = text.str.count(r"[.!?।]")

    features = pd.DataFrame(index=frame.index)
    features["log_text_len"] = np.log1p(length)
    features["log_word_count"] = np.log1p(words)
    features["avg_word_len"] = length / (words + 1)
    features["sentence_count"] = np.log1p(sentences + 1)
    features["avg_sent_len"] = words / (text.str.count(r"[.!?།]") + 2)
    features["exclamation_count"] = np.log1p(text.str.count(r"!"))
    features["question_count"] = np.log1p(text.str.count(r"\?"))
    features["digit_ratio"] = text.str.count(r"\d") / (length + 1)
    features["upper_ratio"] = text.str.count(r"[A-Z]") / (length + 1)
    features["has_currency"] = text.str.contains(r"[$£€Rs\d]", regex=True).astype(int)
    features["has_donate_word"] = text.str.contains(
        r"donat|contribut|help|support|give|fund|රුපියල්|දීමනා|நன்கொடை",
        case=False,
        regex=True,
    ).astype(int)
    features["is_sinhala"] = (frame["language"] == "Sinhala").astype(int)
    features["is_tamil"] = (frame["language"] == "Tamil").astype(int)
    return features[FEATURE_NAMES].fillna(0).to_numpy(dtype=float)


def load_and_thin(path: Path, seed: int, target_rows: int) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = df.dropna(subset=["appeal_text", "language", "quality_label", "overall_quality_score"]).copy()
    df["appeal_text"] = df["appeal_text"].astype(str).str.strip()
    df["quality_label"] = df["quality_label"].astype(str).str.lower().str.strip()
    df = df[(df["appeal_text"].str.len() > 10) & df["quality_label"].isin(LABEL_ORDER)].copy()
    df["_orig_index"] = df.index.astype(int)

    non_english_aug = df[
        df["language"].isin(["Sinhala", "Tamil"]) & df["data_origin"].isin(AUGMENTED_ORIGINS)
    ].copy()
    rest = df.drop(index=non_english_aug.index)
    needed = target_rows - len(rest)
    if needed <= 0 or needed > len(non_english_aug):
        raise ValueError(
            f"Cannot reach target_rows={target_rows}; rest={len(rest)}, "
            f"augmented_non_english={len(non_english_aug)}"
        )

    stratify = non_english_aug["language"].astype(str) + "__" + non_english_aug["quality_label"].astype(str)
    aug_sample, _unused = train_test_split(
        non_english_aug,
        train_size=needed,
        random_state=seed,
        stratify=stratify,
    )
    clean = pd.concat([rest, aug_sample], axis=0).sort_values("_orig_index").reset_index(drop=True)
    if len(clean) != target_rows:
        raise AssertionError(f"Expected {target_rows} rows after thinning, got {len(clean)}")
    return clean


def near_duplicate_groups(df: pd.DataFrame) -> np.ndarray:
    groups = np.empty(len(df), dtype=object)
    offset = 0
    for language in ["English", "Sinhala", "Tamil"]:
        mask = (df["language"] == language).to_numpy()
        idx = np.where(mask)[0]
        if len(idx) == 0:
            continue
        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=50_000,
            min_df=2,
            sublinear_tf=True,
            strip_accents=None,
        )
        matrix = vec.fit_transform(df.loc[mask, "appeal_text"].astype(str))
        sim = matrix @ matrix.T
        sim.setdiag(0)
        sim.eliminate_zeros()
        sim.data = (sim.data > 0.8).astype(np.int8)
        sim.eliminate_zeros()
        n_components, labels = connected_components(sim, directed=False, return_labels=True)
        groups[idx] = [f"{language}_{offset + label}" for label in labels]
        offset += n_components
    return groups


def fit_tfidf(texts: pd.Series, analyzer: str, ngram_range: tuple[int, int], max_features: int):
    vectorizer = TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        max_features=max_features,
        sublinear_tf=True,
        strip_accents=None,
        min_df=3,
    )
    return vectorizer, vectorizer.fit_transform(texts.astype(str))


def expand_sparse(block, mask_values: np.ndarray, n_rows: int):
    full = lil_matrix((n_rows, block.shape[1]))
    for i, row_i in enumerate(np.where(mask_values)[0]):
        full[row_i] = block[i]
    return full.tocsr()


def expand_dense(block: np.ndarray, mask_values: np.ndarray, n_rows: int, n_cols: int) -> np.ndarray:
    full = np.zeros((n_rows, n_cols), dtype=float)
    full[np.where(mask_values)[0]] = block
    return full


def resolve_labels(scores: np.ndarray, probas: np.ndarray, classes: np.ndarray, tolerance: float = 0.25) -> np.ndarray:
    resolved = []
    for score, proba in zip(scores, probas):
        if score <= 2.0:
            score_label = "low"
        elif score <= 3.0:
            score_label = "medium"
        else:
            score_label = "high"
        clf_label = classes[int(np.argmax(proba))]
        if score_label == clf_label:
            resolved.append(score_label)
        elif abs(score - 2.0) < tolerance or abs(score - 3.0) < tolerance:
            resolved.append(clf_label)
        else:
            resolved.append(score_label)
    return np.asarray(resolved)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_thin(args.data, args.seed, args.target_rows)
    groups = near_duplicate_groups(df)
    le = LabelEncoder()
    y = le.fit_transform(df["quality_label"])
    scores = df["overall_quality_score"].to_numpy(dtype=float)

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=args.seed)
    train_idx, test_idx = next(splitter.split(df, y, groups=groups))
    train = df.iloc[train_idx].copy()
    test = df.iloc[test_idx].copy()

    en_mask = df["language"] == "English"
    si_mask = df["language"] == "Sinhala"
    ta_mask = df["language"] == "Tamil"
    tfidf_en, x_en = fit_tfidf(df.loc[en_mask, "appeal_text"], "word", (1, 2), 25_000)
    tfidf_si, x_si = fit_tfidf(df.loc[si_mask, "appeal_text"], "char_wb", (3, 5), 8_000)
    tfidf_ta, x_ta = fit_tfidf(df.loc[ta_mask, "appeal_text"], "char_wb", (3, 5), 8_000)

    svd_en = TruncatedSVD(n_components=150, random_state=args.seed)
    svd_si = TruncatedSVD(n_components=50, random_state=args.seed)
    svd_ta = TruncatedSVD(n_components=50, random_state=args.seed)
    lsa_en = svd_en.fit_transform(x_en)
    lsa_si = svd_si.fit_transform(x_si)
    lsa_ta = svd_ta.fit_transform(x_ta)

    n = len(df)
    x_en_full = expand_sparse(x_en, en_mask.to_numpy(), n)
    x_si_full = expand_sparse(x_si, si_mask.to_numpy(), n)
    x_ta_full = expand_sparse(x_ta, ta_mask.to_numpy(), n)
    lsa_en_full = expand_dense(lsa_en, en_mask.to_numpy(), n, 150)
    lsa_si_full = expand_dense(lsa_si, si_mask.to_numpy(), n, 50)
    lsa_ta_full = expand_dense(lsa_ta, ta_mask.to_numpy(), n, 50)

    scaler = StandardScaler()
    x_hand = scaler.fit_transform(extract_handcrafted(df))
    x_clf = hstack([csr_matrix(x_hand), x_en_full, x_si_full, x_ta_full])
    x_reg_base = np.hstack([x_hand, lsa_en_full, lsa_si_full, lsa_ta_full])

    base_clf = RandomForestClassifier(
        n_estimators=500,
        max_depth=20,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced",
        random_state=args.seed,
        n_jobs=-1,
    )
    clf = CalibratedClassifierCV(base_clf, method="isotonic", cv=5)
    clf.fit(x_clf[train_idx], y[train_idx])
    train_proba = clf.predict_proba(x_clf[train_idx])
    test_proba = clf.predict_proba(x_clf[test_idx])

    reg = GradientBoostingRegressor(n_estimators=300, max_depth=4, random_state=args.seed)
    reg.fit(np.hstack([train_proba, x_reg_base[train_idx]]), scores[train_idx])
    train_raw = np.clip(reg.predict(np.hstack([train_proba, x_reg_base[train_idx]])), 1.0, 5.0)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(train_raw, scores[train_idx])

    test_raw = np.clip(reg.predict(np.hstack([test_proba, x_reg_base[test_idx]])), 1.0, 5.0)
    test_scores = np.clip(iso.predict(test_raw), 1.0, 5.0)
    pred_labels = resolve_labels(test_scores, test_proba, le.classes_)
    truth_labels = test["quality_label"].to_numpy()
    metrics = {
        "n_corpus": int(len(df)),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "accuracy": float(accuracy_score(truth_labels, pred_labels)),
        "balanced_accuracy": float(balanced_accuracy_score(truth_labels, pred_labels)),
        "macro_f1": float(f1_score(truth_labels, pred_labels, labels=LABEL_ORDER, average="macro", zero_division=0)),
        "mae": float(mean_absolute_error(scores[test_idx], test_scores)),
        "r2": float(r2_score(scores[test_idx], test_scores)),
    }

    cfg = {
        "label_classes": list(le.classes_),
        "boundary_tolerance": 0.25,
        "lsa_components": {"en": 150, "si": 50, "ta": 50},
        "scaler_feature_names": FEATURE_NAMES,
        "model_version": "paper_protocol_grouped_v1",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": int(len(train)),
        "corpus_rows_after_thinning": int(len(df)),
        "test_rows": int(len(test)),
        "seed": int(args.seed),
        "split": "StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42), first fold as test",
        "near_duplicate_threshold": 0.8,
        "non_english_augmented_rows_sampled": int(args.target_rows - len(df[~(
            df["language"].isin(["Sinhala", "Tamil"]) & df["data_origin"].isin(AUGMENTED_ORIGINS)
        )])),
    }

    joblib.dump(tfidf_en, args.out_dir / "appeal_quality_vectorizer.joblib")
    joblib.dump(tfidf_si, args.out_dir / "appeal_quality_vectorizer_si.joblib")
    joblib.dump(tfidf_ta, args.out_dir / "appeal_quality_vectorizer_ta.joblib")
    joblib.dump(svd_en, args.out_dir / "appeal_quality_svd_en.joblib")
    joblib.dump(svd_si, args.out_dir / "appeal_quality_svd_si.joblib")
    joblib.dump(svd_ta, args.out_dir / "appeal_quality_svd_ta.joblib")
    joblib.dump(scaler, args.out_dir / "appeal_quality_scaler.joblib")
    joblib.dump(clf, args.out_dir / "appeal_quality_classifier.joblib")
    joblib.dump(le, args.out_dir / "appeal_quality_label_encoder.joblib")
    joblib.dump(reg, args.out_dir / "appeal_quality_regressor.joblib")
    joblib.dump(iso, args.out_dir / "appeal_quality_isotonic.joblib")
    joblib.dump(cfg, args.out_dir / "appeal_quality_config.joblib")
    np.save(args.out_dir / "appeal_quality_selected_indices.npy", df["_orig_index"].to_numpy(dtype=int))
    np.save(args.out_dir / "appeal_quality_test_indices.npy", test["_orig_index"].to_numpy(dtype=int))
    (args.out_dir / "appeal_quality_training_manifest.json").write_text(
        json.dumps({**cfg, "metrics": metrics}, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
