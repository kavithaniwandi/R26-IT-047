"""
tests/appeals/test_donation_appeal_quality.py
-------------------------------------
Unit test suite for the Donation Appeal Quality Scoring component.
"""
from __future__ import annotations

import joblib
import numpy as np
from unittest.mock import AsyncMock
import pytest

from app.models.config import settings
from app.models.quality_service import (
    QualityModelLoadError,
    _load_artifacts,
    _normalise_language,
    get_quality_score,
    score_appeal,
    warm_up,
)


ARTIFACT_DIR = settings.donation_appeal_model_path("")

REQUIRED_ARTIFACTS = [
    "appeal_quality_vectorizer.joblib",
    "appeal_quality_vectorizer_si.joblib",
    "appeal_quality_vectorizer_ta.joblib",
    "appeal_quality_svd_en.joblib",
    "appeal_quality_svd_si.joblib",
    "appeal_quality_svd_ta.joblib",
    "appeal_quality_scaler.joblib",
    "appeal_quality_classifier.joblib",
    "appeal_quality_label_encoder.joblib",
    "appeal_quality_regressor.joblib",
    "appeal_quality_isotonic.joblib",
    "appeal_quality_config.joblib",
]

VALID_LABELS = {"low", "medium", "high"}

ENGLISH_APPEAL = (
    "Please donate to support flood-affected families in Gampaha district "
    "who have lost their homes and urgently need food, shelter, and clean water. "
    "Your contribution of any amount will make a direct difference to over "
    "200 displaced families. Help us reach our goal of Rs. 500,000."
)

SINHALA_APPEAL = (
    "ගංවතුරෙන් පීඩාවට පත් ගම්පහ දිස්ත්‍රික්කයේ පවුල් 200කට උදව් කිරීමට "
    "කරුණාකර පරිත්‍යාග කරන්න. ඔවුන්ට ආහාර, නවාතැන් සහ පිරිසිදු ජලය "
    "අවශ්‍යය. ඔබේ දායකත්වය ජීවිත වෙනස් කරනු ඇත."
)

TAMIL_APPEAL = (
    "வெள்ளத்தால் பாதிக்கப்பட்ட கம்பஹா மாவட்டத்தில் உள்ள 200 குடும்பங்களுக்கு "
    "உதவ தயவுசெய்து நன்கொடை அளியுங்கள். அவர்களுக்கு உணவு, தங்குமிடம் மற்றும் "
    "தூய்மையான தண்ணீர் தேவை. உங்கள் பங்களிப்பு வாழ்க்கையை மாற்றும்."
)


class TestDonationAppealQualityArtifacts:
    def test_all_artifact_files_exist(self):
        missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
        assert not missing, f"Missing artifact files: {missing}"

    def test_all_artifacts_load_without_error(self):
        for name in REQUIRED_ARTIFACTS:
            assert joblib.load(ARTIFACT_DIR / name) is not None

    def test_config_contains_required_keys(self):
        cfg = joblib.load(ARTIFACT_DIR / "appeal_quality_config.joblib")
        required_keys = {"boundary_tolerance", "lsa_components", "scaler_feature_names"}
        assert not required_keys - set(cfg.keys())

    def test_config_lsa_components_valid(self):
        cfg = joblib.load(ARTIFACT_DIR / "appeal_quality_config.joblib")
        lsa = cfg["lsa_components"]
        assert lsa["en"] > 0
        assert lsa["si"] > 0
        assert lsa["ta"] > 0

    def test_label_encoder_has_three_classes(self):
        le = joblib.load(ARTIFACT_DIR / "appeal_quality_label_encoder.joblib")
        assert set(le.classes_) == VALID_LABELS


class TestWarmUp:
    def test_warm_up_runs_without_error(self):
        warm_up()

    def test_warm_up_is_idempotent(self):
        warm_up()
        warm_up()

    def test_load_artifacts_exposes_cached_zero_blocks(self):
        artifacts = _load_artifacts()
        assert {"ZERO_EN", "ZERO_SI", "ZERO_TA"} <= set(artifacts.keys())


class TestInputValidation:
    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="empty"):
            score_appeal("", "English")

    def test_whitespace_only_raises_value_error(self):
        with pytest.raises(ValueError, match="empty"):
            score_appeal("     ", "English")

    def test_too_short_raises_value_error(self):
        with pytest.raises(ValueError, match="too short"):
            score_appeal("short", "English")

    def test_exactly_min_length_does_not_raise_for_length(self):
        try:
            score_appeal("a" * 10, "English")
        except ValueError as exc:
            pytest.fail(f"10-character text incorrectly rejected: {exc}")

    def test_over_max_length_is_truncated_not_rejected(self):
        long_text = "Support flood victims in Gampaha. " * 400
        result = score_appeal(long_text, "English")
        assert result["quality_label"] in VALID_LABELS

    def test_none_language_defaults_to_english(self):
        result = score_appeal(ENGLISH_APPEAL, None)
        assert result["quality_label"] in VALID_LABELS


class TestLanguageNormalisation:
    @pytest.mark.parametrize(
        "alias,expected",
        [
            ("en", "English"),
            ("eng", "English"),
            ("english", "English"),
            ("EN", "English"),
            ("si", "Sinhala"),
            ("sin", "Sinhala"),
            ("sinhala", "Sinhala"),
            ("ta", "Tamil"),
            ("tam", "Tamil"),
            ("tamil", "Tamil"),
            ("unknown", "English"),
            (None, "English"),
        ],
    )
    def test_language_alias_resolves(self, alias, expected):
        assert _normalise_language(alias) == expected


class TestLanguageInference:
    @pytest.mark.parametrize(
        "text,language",
        [
            (ENGLISH_APPEAL, "English"),
            (SINHALA_APPEAL, "Sinhala"),
            (TAMIL_APPEAL, "Tamil"),
        ],
    )
    def test_language_returns_valid_prediction_shape(self, text, language):
        result = score_appeal(text, language)

        assert result["quality_label"] in VALID_LABELS
        assert 1.0 <= result["quality_score"] <= 5.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["low_confidence"], bool)
        assert set(result["probabilities"].keys()) == VALID_LABELS
        assert abs(sum(result["probabilities"].values()) - 1.0) < 0.01

    @pytest.mark.parametrize(
        "alias,full,text",
        [
            ("en", "English", ENGLISH_APPEAL),
            ("si", "Sinhala", SINHALA_APPEAL),
            ("ta", "Tamil", TAMIL_APPEAL),
        ],
    )
    def test_language_alias_matches_full_name(self, alias, full, text):
        result_alias = score_appeal(text, alias)
        result_full = score_appeal(text, full)

        assert result_alias["quality_label"] == result_full["quality_label"]
        assert result_alias["quality_score"] == result_full["quality_score"]


class TestScoreBoundsAndLabelValidity:
    @pytest.mark.parametrize(
        "text,language",
        [
            (ENGLISH_APPEAL, "English"),
            (SINHALA_APPEAL, "Sinhala"),
            (TAMIL_APPEAL, "Tamil"),
            ("Please help flood victims now urgently.", "English"),
        ],
    )
    def test_score_always_in_range(self, text, language):
        result = score_appeal(text, language)
        assert 1.0 <= result["quality_score"] <= 5.0

    @pytest.mark.parametrize(
        "text,language",
        [
            (ENGLISH_APPEAL, "English"),
            (SINHALA_APPEAL, "Sinhala"),
            (TAMIL_APPEAL, "Tamil"),
        ],
    )
    def test_label_always_valid(self, text, language):
        result = score_appeal(text, language)
        assert result["quality_label"] in VALID_LABELS


class TestBoundaryResolution:
    @pytest.mark.parametrize("text,language", [
        (ENGLISH_APPEAL, "English"),
        (SINHALA_APPEAL, "Sinhala"),
        (TAMIL_APPEAL, "Tamil"),
    ])
    def test_final_label_does_not_clip_numerical_prediction(self, text, language):
        result = score_appeal(text, language)
        score = result["quality_score"]
        assert score == result["raw_quality_score"]
        assert result["quality_label"] in VALID_LABELS
        assert result["quality_label"] == result["predicted_class"]


class TestGetQualityScoreWrapper:
    REQUIRED_WRAPPER_KEYS = {
        "score",
        "status",
        "method",
        "confidence",
        "confidence_normalised",
        "confidence_display",
        "low_confidence",
        "probabilities",
    }

    def test_wrapper_returns_all_required_keys(self):
        result = get_quality_score(ENGLISH_APPEAL, "English")
        assert not self.REQUIRED_WRAPPER_KEYS - set(result.keys())

    def test_wrapper_score_in_bounds(self):
        result = get_quality_score(ENGLISH_APPEAL, "English")
        assert 1.0 <= result["score"] <= 5.0

    def test_wrapper_status_valid(self):
        result = get_quality_score(ENGLISH_APPEAL, "English")
        assert result["status"] in VALID_LABELS

    def test_wrapper_method_is_ml_model(self):
        result = get_quality_score(ENGLISH_APPEAL, "English")
        assert result["method"] == "ml_model"

    def test_wrapper_confidence_display_is_percentage_string(self):
        display = get_quality_score(ENGLISH_APPEAL, "English")["confidence_display"]
        assert isinstance(display, str)
        assert display.endswith("%")

    def test_wrapper_re_raises_validation_error(self):
        with pytest.raises(ValueError):
            get_quality_score("", "English")

    def test_wrapper_low_confidence_is_bool(self):
        result = get_quality_score(ENGLISH_APPEAL, "English")
        assert isinstance(result["low_confidence"], bool)


@pytest.mark.parametrize("language,base", [
    ("English", ENGLISH_APPEAL),
    ("Sinhala", SINHALA_APPEAL),
    ("Tamil", TAMIL_APPEAL),
])
@pytest.mark.parametrize("kind", ["short", "normal", "long"])
def test_calibrated_score_is_displayed_across_languages(language, base, kind):
    text = base[:30] if kind == "short" else base if kind == "normal" else base * 4
    result = score_appeal(text, language)
    assert 1.0 <= result["raw_quality_score"] <= 5.0
    score = result["quality_score"]
    assert score == result["raw_quality_score"]
    assert result["quality_label"] == result["predicted_class"]


@pytest.mark.parametrize("raw,label,proba", [
    (2.4, "low", [0.1, 0.8, 0.1]),
    (1.8, "medium", [0.1, 0.1, 0.8]),
    (2.8, "high", [0.8, 0.1, 0.1]),
    (3.33, "medium", [0.31, 0.045, 0.645]),
    (3.45, "medium", [0.29, 0.072, 0.638]),
    (3.79, "medium", [0.307, 0.094, 0.599]),
    (4.8, "low", [0.1, 0.8, 0.1]),
    (1.2, "high", [0.8, 0.1, 0.1]),
])
def test_label_resolution_preserves_isotonic_score_and_classifier(monkeypatch, raw, label, proba):
    artifacts = _load_artifacts()
    monkeypatch.setattr(artifacts["iso"], "predict", lambda _: np.array([raw]))
    monkeypatch.setattr(artifacts["clf"], "predict_proba", lambda _: np.array([proba]))
    result = score_appeal(ENGLISH_APPEAL)
    assert result["quality_label"] == label
    assert result["raw_quality_score"] == raw
    assert result["quality_score"] == raw
    assert result["confidence"] == round(max(proba), 3)
    from app.models.appeal_guidance_service import batch_score
    batch_result = batch_score([ENGLISH_APPEAL])[0]
    assert batch_result["quality_score"] == result["quality_score"]
    assert batch_result["final_label"] == result["quality_label"]
    assert batch_result["predicted_class"] == result["predicted_class"]


@pytest.mark.parametrize("scorer", [score_appeal, get_quality_score])
def test_missing_directory_raises_without_rule_fallback(monkeypatch, tmp_path, scorer):
    from app.models import quality_service as qs
    missing = tmp_path / "missing-appeal-model"
    monkeypatch.setattr(settings, "APPEAL_MODEL_DIR", missing)
    monkeypatch.setattr(qs, "_ARTIFACTS", {})
    with pytest.raises(QualityModelLoadError) as error:
        scorer(ENGLISH_APPEAL)
    assert str(missing) in str(error.value)
    assert "directory missing" in str(error.value)
    assert "no alternate model" in str(error.value)


def test_missing_files_name_selected_directory(monkeypatch, tmp_path):
    from app.models import quality_service as qs
    monkeypatch.setattr(settings, "APPEAL_MODEL_DIR", tmp_path)
    monkeypatch.setattr(qs, "_ARTIFACTS", {})
    with pytest.raises(QualityModelLoadError) as error:
        qs._load_artifacts()
    assert str(tmp_path) in str(error.value)
    assert "appeal_quality_classifier.joblib" in str(error.value)


def test_unreadable_artifact_names_file(monkeypatch):
    from app.models import quality_service as qs
    monkeypatch.setattr(qs, "_ARTIFACTS", {})
    def unreadable(_):
        raise OSError("mock unreadable artifact")
    monkeypatch.setattr(qs.joblib, "load", unreadable)
    with pytest.raises(QualityModelLoadError) as error:
        qs._load_artifacts()
    assert str(settings.donation_appeal_model_path("appeal_quality_vectorizer.joblib")) in str(error.value)
    assert "OSError" in str(error.value)


@pytest.mark.parametrize("route", [
    "/api/quality/evaluate", "/api/quality/analyse", "/api/quality/improve",
    "/api/generate-appeal-variants", "/api/generate-appeal-variants/next",
    "/api/generate-appeal-variants/remaining",
])
def test_scoring_endpoints_return_503_for_model_load_failure(monkeypatch, route):
    from fastapi.testclient import TestClient
    from app.models import quality_service as qs, gemini_service as gs, main
    from app.services import mongo_service
    from app.services import appeal_budget
    monkeypatch.setattr(appeal_budget, "SESSIONS", {})
    monkeypatch.setattr(appeal_budget, "DAILY", {})
    monkeypatch.setattr(gs, "call_gemini_with_key", AsyncMock(return_value=ENGLISH_APPEAL))
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["offline"])
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda _: False)
    message = "Appeal quality model directory missing: mock/v3_retrained"
    def fail_load():
        raise QualityModelLoadError(message)
    monkeypatch.setattr(qs, "_load_artifacts", fail_load)
    generate = AsyncMock(return_value={
        "model": "mock", "appeal_text": ENGLISH_APPEAL, "generator_status": "live"
    })
    monkeypatch.setattr(gs, "call_gemini_with_key_fallback", generate)
    monkeypatch.setattr(mongo_service, "log_appeal_analysis", AsyncMock())
    monkeypatch.setattr(mongo_service, "log_appeal_generation", AsyncMock())
    payload = {"appeal_text": ENGLISH_APPEAL, "language": "English"} if "/quality/" in route else {
        "language": "English", "campaign_type": "Flood Relief",
        "location": "Nawalapitiya", "verified_need": "water and tents for 20 people",
        "campaign_goal": "provide water and shelter", "style_index": 1,
    }
    # No lifespan: no server, Mongo initialization, or startup work.
    client = TestClient(main.app)
    try:
        response = client.post(route, json=payload)
    finally:
        client.close()
    assert response.status_code == 503
    assert response.json() == {"status": "failed", "detail": message}
