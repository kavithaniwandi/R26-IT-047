from __future__ import annotations

import json
from pathlib import Path

from app.models.severity_service import (
    COMPLAINT_MAPPING_REVIEW_REASON,
    _coverage_below_threshold,
    classify_note,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "triage_sample_cases.json"
ORIGINAL_15_EXPECTED = {
    "critical_respiratory_distress": ("CRITICAL", 100.0000),
    "crush_injury": ("CRITICAL", 100.0000),
    "stroke": ("CRITICAL", 100.0000),
    "pregnancy_bleeding": ("HIGH", 79.6036),
    "paediatric_dehydration": ("HIGH", 79.0245),
    "infected_wound": ("MEDIUM", 40.0000),
    "fracture": ("MEDIUM", 40.0000),
    "leptospirosis_fever": ("MEDIUM", 40.0000),
    "minor_cut": ("MEDIUM", 40.0000),
    "medication_need": ("LOW", 19.3816),
    "safety_severe_headache_neuro_red_flag": ("HIGH", 79.7395),
    "safety_headache_hypoxia_tachycardia": ("HIGH", 79.3846),
    "safety_insulin_confused_drowsy": ("HIGH", 79.8901),
    "safety_gibberish": ("MEDIUM", 40.0000),
    "case8_negated_chest_sob_mild_headache": ("LOW", 19.5705),
    "negation_boundary_no_fever_chest_pain": ("HIGH", 68.3291),
    "negation_boundary_no_cough_chest_pain": ("HIGH", 68.3291),
    "negation_boundary_no_chest_pain_but_sob": ("HIGH", 70.0083),
    "negation_denies_chest_pain": ("MEDIUM", 40.0000),
    "negation_without_fever": ("MEDIUM", 40.0000),
    "empty_signal_no_complaints": ("MEDIUM", 40.0000),
    "empty_signal_denies_pain": ("MEDIUM", 40.0000),
    "empty_signal_no_symptoms": ("MEDIUM", 40.0000),
    "minor_cut_ui_exact": ("MEDIUM", 40.0000),
}
SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
EXPECTED_REASON_CODES = {
    "critical_respiratory_distress": "NO_MAPPING",
    "crush_injury": "LOW_COVERAGE",
    "stroke": "NO_MAPPING",
    "pregnancy_bleeding": "LOW_COVERAGE",
    "paediatric_dehydration": "NO_MAPPING",
    "infected_wound": "NO_MAPPING",
    "fracture": "LOW_COVERAGE",
    "leptospirosis_fever": "NO_MAPPING",
    "minor_cut": "NO_MAPPING",
    "medication_need": "PARTIAL_MATCH",
    "safety_severe_headache_neuro_red_flag": "LOW_COVERAGE",
    "safety_headache_hypoxia_tachycardia": None,
    "safety_insulin_confused_drowsy": "NO_MAPPING",
    "safety_gibberish": "NO_MAPPING",
    "case8_negated_chest_sob_mild_headache": "PARTIAL_MATCH",
    "negation_boundary_no_fever_chest_pain": None,
    "negation_boundary_no_cough_chest_pain": None,
    "negation_boundary_no_chest_pain_but_sob": None,
    "negation_denies_chest_pain": "NO_MAPPING",
    "negation_without_fever": "NO_MAPPING",
    "empty_signal_no_complaints": "NO_MAPPING",
    "empty_signal_denies_pain": "NO_MAPPING",
    "empty_signal_no_symptoms": "NO_MAPPING",
    "minor_cut_ui_exact": "NO_MAPPING",
}


def _cases() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _classify(case: dict) -> dict:
    red_flags = case.get("red_flags") or {}
    return classify_note(
        clinical_note=case["clinical_note"],
        age=case.get("age"),
        mode="ml",
        symptoms=case.get("symptoms", ""),
        vitals=case.get("vitals"),
        has_red_flag=1 if red_flags else 0,
        red_flag_count=len(red_flags),
        rf_flags=red_flags,
    )


def _classify_with_mode(case: dict, mode: str, monkeypatch) -> dict:
    from app.models.config import settings

    monkeypatch.setattr(settings, "COMPLAINT_COVERAGE_MODE", mode)
    return _classify(case)


def _classify_with_config(case: dict, monkeypatch, **config) -> dict:
    from app.models.config import settings

    for key, value in config.items():
        monkeypatch.setattr(settings, key, value)
    return _classify(case)


def test_fixture_cases_classify_successfully():
    for case in _cases():
        result = _classify(case)
        assert result["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}, case["id"]
        assert 0 <= result["priority_score"] <= 100, case["id"]


def test_fixture_safety_cases_are_not_low_and_gibberish_is_reviewed():
    cases = {case["id"]: case for case in _cases()}

    for case_id in [
        "safety_severe_headache_neuro_red_flag",
        "safety_headache_hypoxia_tachycardia",
        "safety_insulin_confused_drowsy",
    ]:
        assert _classify(cases[case_id])["severity"] != "LOW"

    gibberish = _classify(cases["safety_gibberish"])
    assert gibberish["severity"] == "MEDIUM"
    assert gibberish["mapping_review_reason"] == COMPLAINT_MAPPING_REVIEW_REASON


def test_fixture_negated_headache_case_does_not_map_chest_or_breathing():
    cases = {case["id"]: case for case in _cases()}
    result = _classify(cases["case8_negated_chest_sob_mild_headache"])

    assert result["mapped_complaints"] == ["headache pain in head"]
    assert result["mapping_review_reason"] is None


def test_fixture_cases_keep_expected_severity_and_score():
    cases = {case["id"]: case for case in _cases()}

    for case_id, (severity, score) in ORIGINAL_15_EXPECTED.items():
        result = _classify(cases[case_id])
        assert result["severity"] == severity, case_id
        assert result["priority_score"] == score, case_id


def test_minor_cut_ui_exact_is_not_high():
    cases = {case["id"]: case for case in _cases()}
    result = _classify(cases["minor_cut_ui_exact"])

    assert result["severity"] != "HIGH"
    assert "SpO2 < 92" not in result["suggested_specialty"]["matched_keywords"]


def test_fixture_negation_boundary_cases_map_expected_terms():
    cases = {case["id"]: case for case in _cases()}
    expectations = {
        "negation_boundary_no_fever_chest_pain": (["chest pain"], ["fever"]),
        "negation_boundary_no_cough_chest_pain": (["chest pain"], ["cough"]),
        "negation_boundary_no_chest_pain_but_sob": (["shortness of breath"], ["chest pain"]),
        "negation_denies_chest_pain": ([], ["chest pain"]),
        "negation_without_fever": ([], ["fever"]),
    }

    for case_id, (present, absent) in expectations.items():
        result = _classify(cases[case_id])
        mapped = result["mapped_complaints"]
        for expected in present:
            assert any(expected in term for term in mapped), case_id
        for expected in absent:
            assert all(expected not in term for term in mapped), case_id


def test_fixture_empty_signal_cases_get_review_floor():
    cases = {case["id"]: case for case in _cases()}

    for case_id in [
        "empty_signal_no_complaints",
        "empty_signal_denies_pain",
        "empty_signal_no_symptoms",
    ]:
        result = _classify(cases[case_id])
        assert result["mapped"] is False, case_id
        assert result["severity"] == "MEDIUM", case_id
        assert result["priority_score"] >= 40.0, case_id
        assert result["mapping_review_reason"] == COMPLAINT_MAPPING_REVIEW_REASON, case_id


def test_fixture_expected_specialty_suggestions():
    for case in _cases():
        result = _classify(case)
        suggested = result["suggested_specialty"]

        assert suggested["primary"] == case["expected_specialty_primary"], case["id"]
        acceptable_secondary = set(case.get("acceptable_secondary") or [])
        assert all(
            specialty in acceptable_secondary
            for specialty in suggested.get("secondary", [])
        ), case["id"]
        if case.get("expected_fallback"):
            assert suggested["fallback"] is True, case["id"]


def test_fixture_expected_complaint_mapping_reason_codes():
    cases = {case["id"]: case for case in _cases()}

    for case_id, reason_code in EXPECTED_REASON_CODES.items():
        result = _classify(cases[case_id])
        assert result["complaint_mapping"]["reason_code"] == reason_code, case_id
        assert isinstance(result["complaint_mapping"]["unmapped_terms"], list), case_id
        assert isinstance(result["complaint_mapping"]["mapped_terms"], list), case_id


def test_clinical_coverage_shadow_mode_does_not_change_default_fixture_outputs(monkeypatch):
    from app.models.config import settings

    cases = {case["id"]: case for case in _cases()}
    case = cases["extra_crushing_chest_pain"] if "extra_crushing_chest_pain" in cases else None
    assert case is None

    medication = cases["medication_need"]
    monkeypatch.setattr(settings, "COMPLAINT_COVERAGE_MODE", "clinical")
    clinical = _classify(medication)
    monkeypatch.setattr(settings, "COMPLAINT_COVERAGE_MODE", "legacy")
    legacy = _classify(medication)

    assert clinical["severity"] == legacy["severity"]
    assert clinical["priority_score"] == legacy["priority_score"]
    assert clinical["complaint_mapping"]["coverage"] >= legacy["complaint_mapping"]["coverage"]


def test_clinical_coverage_shadow_safety_assertions(monkeypatch):
    cases = {case["id"]: case for case in _cases()}
    extras = {
        "extra_crushing_chest_pain": {
            "id": "extra_crushing_chest_pain",
            "age": 45,
            "symptoms": "Crushing chest pain spreading to the left arm for 30 minutes, sweating. No fever, no cough.",
            "clinical_note": "Crushing chest pain spreading to the left arm for 30 minutes, sweating. No fever, no cough.",
            "vitals": {
                "vital_hr": 88,
                "vital_spo2": 98,
                "vital_sbp": 128,
                "vital_rr": 18,
                "vital_temp": 36.8,
                "pain_score": 7,
            },
            "red_flags": {},
        },
        "extra_insulin_confused_drowsy": {
            "id": "extra_insulin_confused_drowsy",
            "age": 45,
            "symptoms": "Ran out of insulin 3 days ago, now confused and very drowsy",
            "clinical_note": "Ran out of insulin 3 days ago, now confused and very drowsy",
            "vitals": {
                "vital_hr": 88,
                "vital_spo2": 98,
                "vital_sbp": 128,
                "vital_rr": 18,
                "vital_temp": 36.8,
                "pain_score": 1,
            },
            "red_flags": {},
        },
    }

    for case in [*cases.values(), *extras.values()]:
        legacy = _classify_with_mode(case, "legacy", monkeypatch)
        clinical = _classify_with_mode(case, "clinical", monkeypatch)
        if legacy["severity"] in {"HIGH", "CRITICAL"}:
            assert SEVERITY_RANK[clinical["severity"]] >= SEVERITY_RANK[legacy["severity"]], case["id"]

    for case_id in ["infected_wound", "fracture", "leptospirosis_fever", "minor_cut"]:
        clinical = _classify_with_mode(cases[case_id], "clinical", monkeypatch)
        assert SEVERITY_RANK[clinical["severity"]] >= SEVERITY_RANK["MEDIUM"], case_id

    for case_id in [
        "safety_gibberish",
        "negation_denies_chest_pain",
        "negation_without_fever",
        "empty_signal_no_complaints",
        "empty_signal_denies_pain",
        "empty_signal_no_symptoms",
    ]:
        clinical = _classify_with_mode(cases[case_id], "clinical", monkeypatch)
        assert clinical["complaint_mapping"]["floor_applied"] is True, case_id


def test_threshold_boundary_semantics_for_legacy_and_clinical_modes(monkeypatch):
    from app.models.config import settings

    for mode in ["legacy", "clinical"]:
        monkeypatch.setattr(settings, "COMPLAINT_COVERAGE_MODE", mode)
        assert _coverage_below_threshold(0.4999, 0.5) is True
        assert _coverage_below_threshold(0.5, 0.5) is False
        assert _coverage_below_threshold(0.5001, 0.5) is False


def test_danger_term_floor_is_flagged_and_negation_aware(monkeypatch):
    base = {
        "id": "danger_unresponsive",
        "age": 40,
        "symptoms": "cough for two days, also unresponsive",
        "clinical_note": "cough for two days, also unresponsive",
        "vitals": {
            "vital_hr": 80,
            "vital_spo2": 98,
            "vital_sbp": 120,
            "vital_rr": 16,
            "vital_temp": 36.8,
            "pain_score": 1,
        },
        "red_flags": {},
    }
    result = _classify_with_config(
        base,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_APPROVED_SYNONYMS_ENABLED=True,
        COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
    )
    assert SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK["MEDIUM"]
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"
    assert result["complaint_mapping"]["floor_applied"] is True

    cyanosis = {**base, "id": "danger_cyanosis", "symptoms": "cyanosis", "clinical_note": "cyanosis"}
    result = _classify_with_config(
        cyanosis,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
    )
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"

    negated = {**base, "id": "negated_seizure", "symptoms": "no seizure", "clinical_note": "no seizure"}
    result = _classify_with_config(
        negated,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
    )
    assert result["complaint_mapping"]["reason_code"] == "NO_MAPPING"


def test_cut_bleeding_shadow_safety_cases(monkeypatch):
    base = {
        "age": 32,
        "clinical_note": "",
        "vitals": {
            "vital_hr": 82,
            "vital_spo2": 98,
            "vital_sbp": 122,
            "vital_rr": 16,
            "vital_temp": 36.8,
            "pain_score": 1,
        },
        "red_flags": {},
    }

    configs = {
        "COMPLAINT_COVERAGE_MODE": "clinical",
        "COMPLAINT_APPROVED_SYNONYMS_ENABLED": True,
        "COMPLAINT_DANGER_TERM_FLOOR_ENABLED": True,
    }
    for symptoms in ["deep cut with heavy bleeding", "cut hand, bleeding will not stop"]:
        case = {**base, "id": symptoms, "symptoms": symptoms, "clinical_note": symptoms}
        result = _classify_with_config(case, monkeypatch, **configs)
        assert SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK["MEDIUM"], symptoms
        assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED", symptoms

    controlled = {
        **base,
        "id": "controlled_cut",
        "symptoms": "small superficial cut on hand, bleeding controlled",
        "clinical_note": "small superficial cut on hand, bleeding controlled",
    }
    result = _classify_with_config(controlled, monkeypatch, **configs)
    assert result["severity"] == "LOW"
    assert result["complaint_mapping"]["reason_code"] is None


def test_conditional_synonym_shadow_case_outcomes_are_explicit(monkeypatch):
    cases = {case["id"]: case for case in _cases()}
    infected = _classify_with_config(
        cases["infected_wound"],
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_APPROVED_SYNONYMS_ENABLED=True,
        COMPLAINT_CONDITIONAL_SYNONYMS_ENABLED=["infected_wound"],
    )
    assert "skin infection cellulitis" in infected["complaint_mapping"]["mapped_terms"]
    assert infected["severity"] == "LOW"

    insulin = {
        "id": "extra_insulin_confused_drowsy",
        "age": 45,
        "symptoms": "Ran out of insulin 3 days ago, now confused and very drowsy",
        "clinical_note": "Ran out of insulin 3 days ago, now confused and very drowsy",
        "vitals": {
            "vital_hr": 88,
            "vital_spo2": 98,
            "vital_sbp": 128,
            "vital_rr": 18,
            "vital_temp": 36.8,
            "pain_score": 1,
        },
        "red_flags": {},
    }
    insulin_result = _classify_with_config(
        insulin,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_APPROVED_SYNONYMS_ENABLED=True,
        COMPLAINT_CONDITIONAL_SYNONYMS_ENABLED=["insulin"],
    )
    assert SEVERITY_RANK[insulin_result["severity"]] >= SEVERITY_RANK["MEDIUM"]
    assert "diabetes management" in insulin_result["complaint_mapping"]["mapped_terms"]
