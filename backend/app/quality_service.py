import re

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

from app.config import settings


_artifacts = {}

CONFIDENCE_BASELINES = {
    "English": 0.82,
    "Sinhala": 0.71,
    "Tamil": 0.72,
}

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
    return _LANGUAGE_ALIASES.get(value, language or "English")


def _load_artifacts():
    global _artifacts
    if _artifacts:
        return _artifacts

    model_path = settings.donation_appeal_model_path
    _artifacts = {
        "tfidf_en": joblib.load(model_path("appeal_quality_vectorizer.joblib")),
        "tfidf_si": joblib.load(model_path("appeal_quality_vectorizer_si.joblib")),
        "tfidf_ta": joblib.load(model_path("appeal_quality_vectorizer_ta.joblib")),
        "svd_en": joblib.load(model_path("appeal_quality_svd_en.joblib")),
        "svd_si": joblib.load(model_path("appeal_quality_svd_si.joblib")),
        "svd_ta": joblib.load(model_path("appeal_quality_svd_ta.joblib")),
        "scaler": joblib.load(model_path("appeal_quality_scaler.joblib")),
        "clf": joblib.load(model_path("appeal_quality_classifier.joblib")),
        "le": joblib.load(model_path("appeal_quality_label_encoder.joblib")),
        "reg": joblib.load(model_path("appeal_quality_regressor.joblib")),
        "iso": joblib.load(model_path("appeal_quality_isotonic.joblib")),
        "config": joblib.load(model_path("appeal_quality_config.joblib")),
    }
    return _artifacts


def _extract_handcrafted(text: str, language: str) -> np.ndarray:
    features = [
        np.log1p(len(text)),
        np.log1p(len(text.split())),
        len(text) / (len(text.split()) + 1),
        np.log1p(text.count(".") + text.count("!") + text.count("?") + text.count("।") + 1),
        len(text.split()) / (text.count(".") + text.count("!") + text.count("?") + text.count("།") + 2),
        np.log1p(text.count("!")),
        np.log1p(text.count("?")),
        sum(char.isdigit() for char in text) / (len(text) + 1),
        sum(char.isupper() for char in text) / (len(text) + 1),
        float(any(char in text for char in "$£€R") or any(char.isdigit() for char in text)),
        float(bool(re.search(
            r"donat|contribut|help|support|give|fund|රුපියල්|දීමනා|நன்கொடை",
            text,
            re.IGNORECASE,
        ))),
        float(language == "Sinhala"),
        float(language == "Tamil"),
    ]
    return np.array(features, dtype=float)


def _tfidf_lsa_features(text: str, language: str, artifacts: dict) -> np.ndarray:
    zeros_en = np.zeros(150)
    zeros_si = np.zeros(50)
    zeros_ta = np.zeros(50)

    if language == "English":
        x_text = artifacts["tfidf_en"].transform([text])
        lsa = artifacts["svd_en"].transform(x_text)[0]
        return np.hstack([lsa, zeros_si, zeros_ta])

    if language == "Sinhala":
        x_text = artifacts["tfidf_si"].transform([text])
        lsa = artifacts["svd_si"].transform(x_text)[0]
        return np.hstack([zeros_en, lsa, zeros_ta])

    if language == "Tamil":
        x_text = artifacts["tfidf_ta"].transform([text])
        lsa = artifacts["svd_ta"].transform(x_text)[0]
        return np.hstack([zeros_en, zeros_si, lsa])

    return np.hstack([zeros_en, zeros_si, zeros_ta])


def _clf_input(text: str, language: str, artifacts: dict):
    hand = artifacts["scaler"].transform(
        _extract_handcrafted(text, language).reshape(1, -1)
    )
    hand_sp = csr_matrix(hand)

    n_en = artifacts["tfidf_en"].get_feature_names_out().shape[0]
    n_si = artifacts["tfidf_si"].get_feature_names_out().shape[0]
    n_ta = artifacts["tfidf_ta"].get_feature_names_out().shape[0]

    zeros_en = csr_matrix((1, n_en))
    zeros_si = csr_matrix((1, n_si))
    zeros_ta = csr_matrix((1, n_ta))

    if language == "English":
        x_en = artifacts["tfidf_en"].transform([text])
        return hstack([hand_sp, x_en, zeros_si, zeros_ta])

    if language == "Sinhala":
        x_si = artifacts["tfidf_si"].transform([text])
        return hstack([hand_sp, zeros_en, x_si, zeros_ta])

    if language == "Tamil":
        x_ta = artifacts["tfidf_ta"].transform([text])
        return hstack([hand_sp, zeros_en, zeros_si, x_ta])

    return hstack([hand_sp, zeros_en, zeros_si, zeros_ta])


def _resolve_label(
    score: float,
    proba_row: np.ndarray,
    classes: np.ndarray,
    tolerance: float = 0.4,
) -> str:
    if score <= 2.0:
        score_label = "low"
    elif score <= 3.0:
        score_label = "medium"
    else:
        score_label = "high"

    clf_label = classes[int(np.argmax(proba_row))]

    if score_label == clf_label:
        return score_label

    near_boundary = abs(score - 2.0) < tolerance or abs(score - 3.0) < tolerance
    if near_boundary:
        return clf_label

    return score_label


def get_quality_score(appeal_text: str, language: str = "English") -> dict:
    """
    Evaluate appeal quality using the trained multilingual local ML pipeline.
    """
    try:
        language = _normalise_language(language)
        artifacts = _load_artifacts()
        tolerance = artifacts["config"].get("boundary_tolerance", 0.4)

        x_clf = _clf_input(appeal_text, language, artifacts)
        proba = artifacts["clf"].predict_proba(x_clf)[0]
        raw_confidence = float(proba.max())
        baseline = CONFIDENCE_BASELINES.get(language, 0.795)
        confidence_normalised = round(min(1.0, raw_confidence / baseline), 2)

        hand = artifacts["scaler"].transform(
            _extract_handcrafted(appeal_text, language).reshape(1, -1)
        )
        lsa = _tfidf_lsa_features(appeal_text, language, artifacts)
        x_reg = np.hstack([proba.reshape(1, -1), hand, lsa.reshape(1, -1)])

        raw_score = float(np.clip(artifacts["reg"].predict(x_reg)[0], 1.0, 5.0))
        score = float(np.clip(artifacts["iso"].predict([raw_score])[0], 1.0, 5.0))
        status = _resolve_label(score, proba, artifacts["le"].classes_, tolerance)

        return {
            "score": round(score, 2),
            "status": status,
            "method": "ml_model",
            "confidence": round(raw_confidence, 2),
            "confidence_normalised": confidence_normalised,
            "confidence_display": f"{round(confidence_normalised * 100)}%",
        }
    except Exception as exc:
        print(f"ML quality evaluation error: {exc}")
        return {
            "score": 3.0,
            "status": "medium",
            "method": "default",
            "confidence": 0.0,
            "confidence_normalised": 0.0,
            "confidence_display": "0%",
        }
