from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.severity_service import (
    COMPLAINT_MAPPING_REVIEW_REASON,
    _coverage_below_threshold,
    classify_note,
)


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "triage_sample_cases.json"
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
    "critical_respiratory_distress": "DANGER_TERM_UNMAPPED",
    "crush_injury": "DANGER_TERM_UNMAPPED",
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
        COMPLAINT_DANGER_TERM_FLOOR="HIGH",
    )
    assert SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK["HIGH"]
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"
    assert result["complaint_mapping"]["floor_applied"] is True

    cyanosis = {**base, "id": "danger_cyanosis", "symptoms": "cyanosis", "clinical_note": "cyanosis"}
    result = _classify_with_config(
        cyanosis,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
        COMPLAINT_DANGER_TERM_FLOOR="HIGH",
    )
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"

    negated = {**base, "id": "negated_seizure", "symptoms": "no seizure", "clinical_note": "no seizure"}
    result = _classify_with_config(
        negated,
        monkeypatch,
        COMPLAINT_COVERAGE_MODE="clinical",
        COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
        COMPLAINT_DANGER_TERM_FLOOR="HIGH",
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
        "COMPLAINT_DANGER_TERM_FLOOR": "HIGH",
    }
    for symptoms in ["deep cut with heavy bleeding", "cut hand, bleeding will not stop"]:
        case = {**base, "id": symptoms, "symptoms": symptoms, "clinical_note": symptoms}
        result = _classify_with_config(case, monkeypatch, **configs)
        assert SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK["HIGH"], symptoms
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


def test_allergy_airway_cooccurrence_raises_to_high():
    case = {
        "id": "allergy_airway_child",
        "age": 6,
        "symptoms": "Swelling of lips, difficulty breathing",
        "clinical_note": "6 year old child with swelling of the lips and difficulty breathing after eating peanuts.",
        "vitals": {
            "vital_hr": 100,
            "vital_spo2": 97,
            "vital_sbp": 105,
            "vital_rr": 22,
            "vital_temp": 36.9,
            "pain_score": 3,
        },
        "red_flags": {},
    }

    result = _classify(case)

    assert result["severity"] == "HIGH"
    assert result["priority_score"] >= 60
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"
    assert any("allergy airway compromise" in term for term in result["complaint_mapping"]["danger_terms"])


def test_negated_allergy_airway_terms_do_not_escalate():
    cases = [
        {
            "id": "negated_lip_swelling",
            "age": 6,
            "symptoms": "no swelling of the lips, mild cough",
            "clinical_note": "No swelling of the lips, mild cough only.",
            "vitals": {
                "vital_hr": 92,
                "vital_spo2": 98,
                "vital_sbp": 104,
                "vital_rr": 20,
                "vital_temp": 36.9,
                "pain_score": 1,
            },
            "red_flags": {},
        },
        {
            "id": "negated_standalone_allergy_danger_terms",
            "age": 30,
            "symptoms": "no anaphylaxis, no throat swelling",
            "clinical_note": "No anaphylaxis. No throat swelling. Routine review.",
            "vitals": {
                "vital_hr": 76,
                "vital_spo2": 99,
                "vital_sbp": 120,
                "vital_rr": 16,
                "vital_temp": 36.8,
                "pain_score": 0,
            },
            "red_flags": {},
        },
    ]

    for case in cases:
        result = _classify(case)
        assert result["severity"] != "HIGH", case["id"]
        assert result["complaint_mapping"]["reason_code"] != "DANGER_TERM_UNMAPPED", case["id"]


def test_allergy_history_or_mild_allergy_without_airway_symptoms_is_not_cooccurrence_high():
    cases = [
        {
            "id": "known_peanut_allergy_no_current_symptoms",
            "age": 10,
            "symptoms": "known peanut allergy, no symptoms, routine review",
            "clinical_note": "Known peanut allergy, no symptoms, routine review.",
            "vitals": {
                "vital_hr": 82,
                "vital_spo2": 99,
                "vital_sbp": 110,
                "vital_rr": 16,
                "vital_temp": 36.7,
                "pain_score": 0,
            },
            "red_flags": {},
        },
        {
            "id": "mild_allergic_rash_no_breathing_difficulty",
            "age": 12,
            "symptoms": "mild allergic rash, no breathing difficulty",
            "clinical_note": "Mild allergic rash. No breathing difficulty.",
            "vitals": {
                "vital_hr": 84,
                "vital_spo2": 99,
                "vital_sbp": 112,
                "vital_rr": 16,
                "vital_temp": 36.7,
                "pain_score": 1,
            },
            "red_flags": {},
        },
    ]

    for case in cases:
        result = _classify(case)
        assert result["severity"] != "HIGH", case["id"]
        assert not any("allergy airway compromise" in term for term in result["complaint_mapping"]["danger_terms"])


def test_history_of_anaphylaxis_currently_triggers_standalone_danger_term():
    # Current negation handling does not treat historical context as negation.
    # The existing rule engine also has "anaphylaxis" as a CRITICAL trigger,
    # so historical mentions are currently treated as safety-critical.
    case = {
        "id": "history_of_anaphylaxis",
        "age": 30,
        "symptoms": "history of anaphylaxis",
        "clinical_note": "History of anaphylaxis, routine review, stable now.",
        "vitals": {
            "vital_hr": 76,
            "vital_spo2": 99,
            "vital_sbp": 120,
            "vital_rr": 16,
            "vital_temp": 36.8,
            "pain_score": 0,
        },
        "red_flags": {},
    }

    result = _classify(case)

    assert result["severity"] == "CRITICAL"
    assert result["critical_trigger"] == "anaphylaxis"
    assert result["complaint_mapping"]["reason_code"] == "DANGER_TERM_UNMAPPED"
    assert "anaphylaxis" in result["complaint_mapping"]["danger_terms"]


def test_common_non_allergy_cases_are_not_escalated_by_danger_floor():
    cases = [
        {
            "id": "twisted_ankle",
            "age": 20,
            "symptoms": "Twisted ankle after fall",
            "clinical_note": "Patient twisted ankle after a fall.",
            "vitals": {
                "vital_hr": 82,
                "vital_spo2": 99,
                "vital_sbp": 118,
                "vital_rr": 16,
                "vital_temp": 36.8,
                "pain_score": 4,
            },
            "red_flags": {},
            "not_expected": "HIGH",
        },
        {
            "id": "mild_headache",
            "age": 35,
            "symptoms": "Mild headache",
            "clinical_note": "Mild headache, stable vitals.",
            "vitals": {
                "vital_hr": 76,
                "vital_spo2": 99,
                "vital_sbp": 120,
                "vital_rr": 16,
                "vital_temp": 36.8,
                "pain_score": 2,
            },
            "red_flags": {},
            "not_expected": "HIGH",
        },
        {
            "id": "chest_pain",
            "age": 58,
            "symptoms": "Chest pain",
            "clinical_note": "58 year old male, crushing chest pain spreading to the left arm for 30 minutes, sweating, feeling short of breath.",
            "vitals": {
                "vital_hr": 118,
                "vital_spo2": 88,
                "vital_sbp": 96,
                "vital_rr": 26,
                "vital_temp": 37.2,
                "pain_score": 9,
            },
            "red_flags": {},
            "expected": "HIGH",
        },
    ]

    for case in cases:
        result = _classify(case)
        if "expected" in case:
            assert result["severity"] == case["expected"], case["id"]
        else:
            assert result["severity"] != case["not_expected"], case["id"]
        assert result["complaint_mapping"]["reason_code"] != "DANGER_TERM_UNMAPPED", case["id"]


def test_danger_floor_never_lowers_existing_fixture_severity(monkeypatch):
    for case in _cases():
        danger_off = _classify_with_config(
            case,
            monkeypatch,
            COMPLAINT_DANGER_TERM_FLOOR_ENABLED=False,
        )
        danger_on = _classify_with_config(
            case,
            monkeypatch,
            COMPLAINT_DANGER_TERM_FLOOR_ENABLED=True,
            COMPLAINT_DANGER_TERM_FLOOR="HIGH",
        )
        assert SEVERITY_RANK[danger_on["severity"]] >= SEVERITY_RANK[danger_off["severity"]], case["id"]


def test_complaint_safety_floors_raise_positive_examples():
    positive_cases = [
        (
            "pregnancy_bleeding",
            {
                "id": "pregnancy_bleeding",
                "age": 30,
                "symptoms": "Pregnant with vaginal bleeding",
                "clinical_note": "Pregnant 32 weeks with vaginal bleeding.",
                "vitals": {
                    "vital_hr": 86,
                    "vital_spo2": 99,
                    "vital_sbp": 116,
                    "vital_rr": 16,
                    "vital_temp": 36.8,
                    "pain_score": 2,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "self_harm_wound_or_overdose",
            {
                "id": "self_harm_wound_or_overdose",
                "age": 19,
                "symptoms": "Self harm cut to wrist",
                "clinical_note": "Self harm cut to wrist, bleeding controlled.",
                "vitals": {
                    "vital_hr": 82,
                    "vital_spo2": 99,
                    "vital_sbp": 118,
                    "vital_rr": 16,
                    "vital_temp": 36.8,
                    "pain_score": 3,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "snake_bite",
            {
                "id": "snake_bite",
                "age": 30,
                "symptoms": "Snake bite",
                "clinical_note": "Snake bite on foot with swelling and pain.",
                "vitals": {
                    "vital_hr": 90,
                    "vital_spo2": 98,
                    "vital_sbp": 120,
                    "vital_rr": 18,
                    "vital_temp": 36.9,
                    "pain_score": 5,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "crush_landslide_limb_symptoms",
            {
                "id": "crush_landslide_limb_symptoms",
                "age": 41,
                "symptoms": "Crushed arm pain",
                "clinical_note": "Arm crushed by fallen wall, numb fingers.",
                "vitals": {
                    "vital_hr": 94,
                    "vital_spo2": 98,
                    "vital_sbp": 116,
                    "vital_rr": 18,
                    "vital_temp": 36.8,
                    "pain_score": 7,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "hypoglycaemia_insulin_danger",
            {
                "id": "hypoglycaemia_insulin_danger",
                "age": 44,
                "symptoms": "Hypoglycaemia with seizure",
                "clinical_note": "Hypoglycaemia with seizure.",
                "vitals": {
                    "vital_hr": 88,
                    "vital_spo2": 99,
                    "vital_sbp": 118,
                    "vital_rr": 16,
                    "vital_temp": 36.8,
                    "pain_score": 0,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "dehydration_signs_child_elderly",
            {
                "id": "dehydration_signs_child_elderly",
                "age": 3,
                "symptoms": "Diarrhoea with dry mouth",
                "clinical_note": "Child with dry mouth, sunken eyes and diarrhoea.",
                "vitals": {
                    "vital_hr": 104,
                    "vital_spo2": 98,
                    "vital_sbp": 102,
                    "vital_rr": 20,
                    "vital_temp": 37.2,
                    "pain_score": 2,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
        (
            "dehydration_signs_general",
            {
                "id": "dehydration_signs_general",
                "age": 25,
                "symptoms": "Vomiting and very thirsty",
                "clinical_note": "Vomiting and very thirsty after diarrhoea.",
                "vitals": {
                    "vital_hr": 88,
                    "vital_spo2": 99,
                    "vital_sbp": 116,
                    "vital_rr": 16,
                    "vital_temp": 36.9,
                    "pain_score": 2,
                },
                "red_flags": {},
            },
            "MEDIUM",
        ),
        (
            "elderly_fall_hip_leg_pain",
            {
                "id": "elderly_fall_hip_leg_pain",
                "age": 80,
                "symptoms": "Hip pain after fall",
                "clinical_note": "Hip pain after fall.",
                "vitals": {
                    "vital_hr": 82,
                    "vital_spo2": 99,
                    "vital_sbp": 118,
                    "vital_rr": 16,
                    "vital_temp": 36.8,
                    "pain_score": 5,
                },
                "red_flags": {},
            },
            "MEDIUM",
        ),
        (
            "elderly_fall_cannot_walk",
            {
                "id": "elderly_fall_cannot_walk",
                "age": 80,
                "symptoms": "Fell and unable to walk",
                "clinical_note": "Elderly patient fell and is unable to walk.",
                "vitals": {
                    "vital_hr": 82,
                    "vital_spo2": 99,
                    "vital_sbp": 118,
                    "vital_rr": 16,
                    "vital_temp": 36.8,
                    "pain_score": 6,
                },
                "red_flags": {},
            },
            "HIGH",
        ),
    ]

    for floor_id, case, floor in positive_cases:
        result = _classify(case)
        assert SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK[floor], floor_id
        assert any(item["id"] == floor_id for item in result["safety_floors"]), floor_id
        assert f"safety floor: {floor_id} - review" in result["matched_rules"], floor_id


def test_complaint_safety_floors_are_negation_aware():
    negative_cases = [
        {
            "id": "no_snake_bite",
            "age": 21,
            "symptoms": "No snake bite",
            "clinical_note": "Saw snake nearby but no snake bite.",
        },
        {
            "id": "denies_vaginal_bleeding",
            "age": 30,
            "symptoms": "Pregnant denies vaginal bleeding",
            "clinical_note": "Pregnant patient denies vaginal bleeding.",
        },
        {
            "id": "not_pregnant_no_bleeding",
            "age": 30,
            "symptoms": "Not pregnant, no bleeding",
            "clinical_note": "Not pregnant, no bleeding.",
        },
    ]
    vitals = {
        "vital_hr": 82,
        "vital_spo2": 99,
        "vital_sbp": 118,
        "vital_rr": 16,
        "vital_temp": 36.8,
        "pain_score": 1,
    }

    for case in negative_cases:
        result = _classify({**case, "vitals": vitals, "red_flags": {}})
        assert result["safety_floors"] == [], case["id"]
        assert not any(str(rule).startswith("safety floor:") for rule in result["matched_rules"]), case["id"]


def test_complaint_safety_floors_do_not_change_rule_based_mode():
    vitals = {
        "vital_hr": 82,
        "vital_spo2": 99,
        "vital_sbp": 118,
        "vital_rr": 16,
        "vital_temp": 36.8,
        "pain_score": 1,
    }
    snake = classify_note(
        clinical_note="Snake bite on foot with swelling and pain.",
        symptoms="Snake bite",
        age=30,
        mode="rule_based",
        vitals=vitals,
    )
    assert snake["safety_floors"] == []
    assert not any(str(rule).startswith("safety floor:") for rule in snake["matched_rules"])

    for note, trigger in [("Patient is not breathing.", "not breathing"), ("Patient has no pulse.", "no pulse")]:
        result = classify_note(clinical_note=note, symptoms=note, age=30, mode="rule_based", vitals=vitals)
        assert result["severity"] == "CRITICAL"
        assert result["critical_trigger"] == trigger


def test_complaint_safety_floors_never_lower_existing_fixture_severity(monkeypatch):
    for case in _cases():
        floors_off = _classify_with_config(
            case,
            monkeypatch,
            COMPLAINT_SAFETY_FLOORS_ENABLED=False,
        )
        floors_on = _classify_with_config(
            case,
            monkeypatch,
            COMPLAINT_SAFETY_FLOORS_ENABLED=True,
        )
        assert SEVERITY_RANK[floors_on["severity"]] >= SEVERITY_RANK[floors_off["severity"]], case["id"]


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


@pytest.mark.xfail(
    strict=True,
    reason="historical / post-span negation not handled; planned negation-history phase",
)
def test_old_snake_bite_scar_historical_not_high():
    vitals = {
        "vital_hr": 82,
        "vital_spo2": 99,
        "vital_sbp": 118,
        "vital_rr": 16,
        "vital_temp": 36.8,
        "pain_score": 1,
    }
    active = classify_note(
        clinical_note="Snake bite on foot with swelling and pain.",
        symptoms="Snake bite",
        age=40,
        mode="ml",
        vitals=vitals,
        has_red_flag=0,
        red_flag_count=0,
        rf_flags={},
    )
    assert active["severity"] == "HIGH"

    historical = classify_note(
        clinical_note="Old snake bite scar, no current bite.",
        symptoms="Old snake bite scar",
        age=40,
        mode="ml",
        vitals=vitals,
        has_red_flag=0,
        red_flag_count=0,
        rf_flags={},
    )
    assert historical["severity"] != "HIGH"
