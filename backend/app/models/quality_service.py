"""
Donation appeal quality scoring service.

Pipeline:
text + language -> handcrafted features + per-language TF-IDF/LSA
-> calibrated classifier probabilities -> GBR regressor -> isotonic score.
"""

from __future__ import annotations

import logging
import re

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

from app.models.config import settings


logger = logging.getLogger(__name__)

_ARTIFACTS: dict = {}

_LANGUAGE_ALIASES = {
    "en": "English",
    "eng": "English",
    "english": "English",
    "si": "Sinhala",
    "sin": "Sinhala",
    "sinhala": "Sinhala",
    "ta": "Tamil",
    "tam": "Tamil",
    "tamil": "Tamil",
}


def _normalise_language(language: str | None) -> str:
    value = (language or "English").strip().lower()
    return _LANGUAGE_ALIASES.get(value, "English")


def _load_artifacts() -> dict:
    global _ARTIFACTS
    if _ARTIFACTS:
        return _ARTIFACTS

    names = {
        "tfidf_en": "appeal_quality_vectorizer.joblib",
        "tfidf_si": "appeal_quality_vectorizer_si.joblib",
        "tfidf_ta": "appeal_quality_vectorizer_ta.joblib",
        "svd_en": "appeal_quality_svd_en.joblib",
        "svd_si": "appeal_quality_svd_si.joblib",
        "svd_ta": "appeal_quality_svd_ta.joblib",
        "scaler": "appeal_quality_scaler.joblib",
        "clf": "appeal_quality_classifier.joblib",
        "le": "appeal_quality_label_encoder.joblib",
        "reg": "appeal_quality_regressor.joblib",
        "iso": "appeal_quality_isotonic.joblib",
        "cfg": "appeal_quality_config.joblib",
    }

    loaded = {}
    for key, filename in names.items():
        path = settings.donation_appeal_model_path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Quality model artifact missing: {path}")
        loaded[key] = joblib.load(path)
        logger.info("Loaded donation appeal artifact: %s", filename)

    loaded["N_EN"] = loaded["tfidf_en"].transform([""]).shape[1]
    loaded["N_SI"] = loaded["tfidf_si"].transform([""]).shape[1]
    loaded["N_TA"] = loaded["tfidf_ta"].transform([""]).shape[1]

    _ARTIFACTS = loaded
    logger.info("Donation appeal quality scoring pipeline ready")
    return _ARTIFACTS


def _handcrafted(text: str, language: str, artifacts: dict) -> np.ndarray:
    t = str(text or "")
    words = t.split()
    sentence_count = len(re.findall(r"[.!?।]", t))
    avg_sent_denominator = len(re.findall(r"[.!?།]", t)) + 2

    row = {
        "log_text_len": np.log1p(len(t)),
        "log_word_count": np.log1p(len(words)),
        "avg_word_len": len(t) / (len(words) + 1),
        "sentence_count": np.log1p(sentence_count + 1),
        "avg_sent_len": len(words) / avg_sent_denominator,
        "exclamation_count": np.log1p(t.count("!")),
        "question_count": np.log1p(t.count("?")),
        "digit_ratio": len(re.findall(r"\d", t)) / (len(t) + 1),
        "upper_ratio": len(re.findall(r"[A-Z]", t)) / (len(t) + 1),
        "has_currency": int(bool(re.search(r"[$£€Rs\d]", t))),
        "has_donate_word": int(
            bool(
                re.search(
                    r"donat|contribut|help|support|give|fund|රුපියල්|දීමනා|நன்கொடை",
                    t,
                    re.IGNORECASE,
                )
            )
        ),
        "is_sinhala": int(language == "Sinhala"),
        "is_tamil": int(language == "Tamil"),
    }

    feature_names = artifacts["cfg"]["scaler_feature_names"]
    return np.array([row[name] for name in feature_names], dtype=float).reshape(1, -1)


def _resolve_label(score: float, proba: np.ndarray, artifacts: dict) -> str:
    tolerance = artifacts["cfg"].get("boundary_tolerance", 0.25)

    if score <= 2.0:
        score_label = "low"
    elif score <= 3.0:
        score_label = "medium"
    else:
        score_label = "high"

    clf_label = artifacts["le"].classes_[int(np.argmax(proba))]
    if score_label == clf_label:
        return score_label

    if abs(score - 2.0) < tolerance or abs(score - 3.0) < tolerance:
        return clf_label

    return score_label


def score_appeal(text: str, language: str = "English") -> dict:
    artifacts = _load_artifacts()
    language = _normalise_language(language)
    lsa_components = artifacts["cfg"]["lsa_components"]

    hand_raw = _handcrafted(text, language, artifacts)
    hand_scaled = artifacts["scaler"].transform(hand_raw)

    if language == "Sinhala":
        tfidf_feat = artifacts["tfidf_si"].transform([text])
        lsa_en = np.zeros((1, lsa_components["en"]))
        lsa_si = artifacts["svd_si"].transform(tfidf_feat)
        lsa_ta = np.zeros((1, lsa_components["ta"]))
        clf_tfidf_en = csr_matrix((1, artifacts["N_EN"]))
        clf_tfidf_si = tfidf_feat
        clf_tfidf_ta = csr_matrix((1, artifacts["N_TA"]))
    elif language == "Tamil":
        tfidf_feat = artifacts["tfidf_ta"].transform([text])
        lsa_en = np.zeros((1, lsa_components["en"]))
        lsa_si = np.zeros((1, lsa_components["si"]))
        lsa_ta = artifacts["svd_ta"].transform(tfidf_feat)
        clf_tfidf_en = csr_matrix((1, artifacts["N_EN"]))
        clf_tfidf_si = csr_matrix((1, artifacts["N_SI"]))
        clf_tfidf_ta = tfidf_feat
    else:
        tfidf_feat = artifacts["tfidf_en"].transform([text])
        lsa_en = artifacts["svd_en"].transform(tfidf_feat)
        lsa_si = np.zeros((1, lsa_components["si"]))
        lsa_ta = np.zeros((1, lsa_components["ta"]))
        clf_tfidf_en = tfidf_feat
        clf_tfidf_si = csr_matrix((1, artifacts["N_SI"]))
        clf_tfidf_ta = csr_matrix((1, artifacts["N_TA"]))

    x_clf = hstack(
        [csr_matrix(hand_scaled), clf_tfidf_en, clf_tfidf_si, clf_tfidf_ta]
    )
    proba = artifacts["clf"].predict_proba(x_clf)[0]

    x_reg = np.hstack([proba.reshape(1, -1), hand_scaled, lsa_en, lsa_si, lsa_ta])
    raw_score = float(np.clip(artifacts["reg"].predict(x_reg)[0], 1.0, 5.0))
    score = float(np.clip(artifacts["iso"].predict([raw_score])[0], 1.0, 5.0))
    label = _resolve_label(score, proba, artifacts)

    confidence = round(float(proba.max()), 3)
    return {
        "quality_label": label,
        "quality_score": round(score, 2),
        "confidence": confidence,
        "probabilities": {
            cls: round(float(probability), 3)
            for cls, probability in zip(artifacts["le"].classes_, proba)
        },
    }


def get_quality_score(appeal_text: str, language: str = "English") -> dict:
    """
    Backward-compatible API used by FastAPI and Gemini appeal generation.
    """
    try:
        result = score_appeal(appeal_text, language)
        confidence = result["confidence"]
        return {
            "score": result["quality_score"],
            "status": result["quality_label"],
            "method": "ml_model",
            "confidence": confidence,
            "confidence_normalised": confidence,
            "confidence_display": f"{round(confidence * 100)}%",
            "probabilities": result["probabilities"],
        }
    except Exception as exc:
        logger.exception("ML quality evaluation error: %s", exc)
        return {
            "score": 3.0,
            "status": "medium",
            "method": "default",
            "confidence": 0.0,
            "confidence_normalised": 0.0,
            "confidence_display": "0%",
            "probabilities": {},
        }
