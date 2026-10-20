"""Specialty evidence regressions; no changes to severity model decisions."""
import pytest

from app.models.specialty_service import suggest_specialty


def suggest(symptoms, note="", age=25, severity="MEDIUM", vitals=None, flags=None, mapped=None):
    return suggest_specialty(symptoms, note, flags or {}, age, severity, mapped or [], vitals)


@pytest.mark.parametrize("age", [12, 25, 64, 65, None])
def test_generic_gastrointestinal_symptoms_do_not_imply_pediatric(age):
    result = suggest("vomiting and diarrhoea", "SpO2 99, HR 80, RR 16, BP 120/80, temp 37.", age=age,
                     vitals={"vital_spo2": 99, "vital_hr": 80, "vital_rr": 16, "vital_sbp": 120, "vital_temp": 37})
    assert result["primary"] == "Gastrointestinal"
    assert "Pediatric" not in result["secondary"]
    assert "Respiratory" not in result["secondary"]
    assert set(result["evidence"]["Gastrointestinal"]) == {"vomiting", "diarrhoea"}


@pytest.mark.parametrize("age", [0, 4, 11])
def test_configured_pediatric_age_still_supports_pediatric(age):
    assert suggest("vomiting and diarrhoea", age=age)["primary"] == "Pediatric"


def test_missing_age_requires_explicit_patient_context_for_pediatric():
    result = suggest("child with vomiting and diarrhoea", age=None)
    assert result["primary"] == "Pediatric"
    assert any("age is missing" in reason for reason in result["review_reasons"])


def test_adult_age_wins_over_conflicting_child_wording_and_requests_review():
    result = suggest("child with vomiting and diarrhoea", age=25)
    assert result["primary"] == "Gastrointestinal"
    assert "Pediatric" not in result["secondary"]
    assert any("age conflicts" in reason for reason in result["review_reasons"])


@pytest.mark.parametrize("note", [
    "History of asthma.",
    "Previously had pneumonia.",
    "Mother has cough and wheezing.",
    "Her child has asthma and cough.",
    "No chest pain or shortness of breath or cough.",
    "Cough absent. Hypoxia is not present.",
])
def test_inactive_or_other_person_symptoms_do_not_inflate_specialties(note):
    result = suggest("vomiting and diarrhoea", note)
    assert result["primary"] == "Gastrointestinal"
    assert "Respiratory" not in result["secondary"]
    assert "Cardiovascular" not in result["secondary"]


def test_relative_child_does_not_establish_patient_age():
    result = suggest("vomiting and diarrhoea", "My child has asthma and cough.", age=None)
    assert result["primary"] == "Gastrointestinal"
    assert "Pediatric" not in result["secondary"]


def test_current_assertion_after_history_or_negation_is_preserved():
    result = suggest("No chest pain but shortness of breath.", "History of asthma; now wheezing.")
    assert result["primary"] == "Respiratory"
    assert "Cardiovascular" not in result["secondary"]


def test_mapped_model_phrases_do_not_reintroduce_negated_evidence():
    result = suggest("vomiting and diarrhoea", "No cough or shortness of breath.",
                     mapped=["shortness of breath dyspnoea", "pediatric asthma"])
    assert result["primary"] == "Gastrointestinal"
    assert "Respiratory" not in result["secondary"]
    assert "Pediatric" not in result["secondary"]


def test_equivalent_phrases_and_repeated_fields_count_once():
    baseline = suggest("shortness of breath")
    repeated = suggest("shortness of breath, breathlessness, breathing difficulty",
                       "short of breath, respiratory distress, shortness of breath")
    assert repeated["evidence_scores"]["Respiratory"] == baseline["evidence_scores"]["Respiratory"]


def test_spelling_variants_do_not_double_count_diarrhea():
    baseline = suggest("vomiting and diarrhea")
    repeated = suggest("vomiting, diarrhea and diarrhoea")
    assert repeated["evidence_scores"]["Gastrointestinal"] == baseline["evidence_scores"]["Gastrointestinal"]


def test_checkbox_and_same_symptom_are_one_observation():
    flags = {"breathing_difficulty": 1}
    baseline = suggest("", flags=flags)
    repeated = suggest("shortness of breath", flags=flags)
    assert repeated["evidence_scores"]["Respiratory"] == baseline["evidence_scores"]["Respiratory"]


def test_normal_spo2_does_not_cancel_a_real_respiratory_complaint():
    result = suggest("asthma and cough", "SpO2 99.", vitals={"vital_spo2": 99})
    assert result["primary"] == "Respiratory"
    assert "SpO2 < 92" not in result["matched_keywords"]


def test_abnormal_vital_explanation_identifies_the_actual_evidence():
    result = suggest("vomiting and diarrhoea", severity="HIGH", vitals={"vital_spo2": 88})
    assert result["primary"] == "Emergency Medicine"
    assert "SpO2 < 92" in result["reason"]
    assert "SpO2 < 92" in result["evidence"]["Respiratory"]
    assert all(result["evidence"][specialty] for specialty in result["secondary"])


def test_critical_primary_does_not_require_keyword_evidence_or_fill_secondary_slots():
    result = suggest("", severity="CRITICAL")
    assert result["primary"] == "Emergency Medicine"
    assert result["secondary"] == []
    assert result["evidence"]["Emergency Medicine"] == ["CRITICAL severity"]


def test_tied_scores_are_explicitly_flagged_for_review():
    result = suggest("fracture and wound")
    assert any("tied" in reason for reason in result["review_reasons"])


def test_mapped_phrases_remain_a_fallback_for_callers_without_raw_text():
    assert suggest("", mapped=["nausea and vomiting"])["primary"] == "Gastrointestinal"


def test_api_response_schema_preserves_evidence_and_review_reasons():
    from app.models.schemas import SuggestedSpecialty

    result = suggest("child with vomiting and diarrhoea", age=25)
    response = SuggestedSpecialty.model_validate(result).model_dump()
    assert response["evidence"] == result["evidence"]
    assert response["evidence_scores"] == result["evidence_scores"]
    assert response["review_reasons"] == result["review_reasons"]


@pytest.mark.parametrize("severity", ["LOW", "MEDIUM"])
def test_specific_mild_headache_prefers_general_over_broad_headache(severity):
    result = suggest("Mild headache since morning", "Mild headache since morning, no other symptoms, vitals stable",
                     age=45, severity=severity,
                     vitals={"vital_hr": 78, "vital_spo2": 98, "vital_sbp": 118, "vital_rr": 16, "vital_temp": 36, "pain_score": 4})
    assert result["primary"] == "General Practice"
    assert "Neurological" not in result["secondary"]
    assert result["evidence"]["General Practice"] == ["mild headache"]


@pytest.mark.parametrize("vitals", [
    {"vital_spo2": 88}, {"vital_hr": 130}, {"vital_sbp": 80},
    {"vital_rr": 30}, {"vital_temp": 39}, {"pain_score": 9},
])
def test_abnormal_vitals_do_not_suppress_neurological_headache_evidence(vitals):
    result = suggest("mild headache", vitals=vitals)
    assert result["evidence_scores"].get("Neurological", 0) > 0


def test_mild_wording_does_not_hide_separate_neurological_evidence():
    result = suggest("mild headache", "Later developed severe headache and arm weakness.")
    assert result["evidence_scores"].get("Neurological", 0) > 0
    assert result["primary"] == "Neurological"


@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_high_severity_does_not_use_routine_mild_headache_preference(severity):
    result = suggest("mild headache", severity=severity)
    assert result["evidence_scores"].get("Neurological", 0) > 0


def test_neurological_red_flag_prevents_routine_phrase_preference():
    result = suggest("mild headache", flags={"focal_neurologic_deficit": 1})
    assert "headache" in result["evidence"]["Neurological"]


def test_screenshot_specialty_change_preserves_mapping_review_and_severity():
    from app.models.severity_service import classify_note

    result = classify_note(
        clinical_note="Mild headache since morning, no other symptoms, vitals stable",
        symptoms="Mild headache since morning", age=45, mode="ml",
        vitals={"vital_hr": 78, "vital_spo2": 98, "vital_sbp": 118, "vital_rr": 16, "vital_temp": 36, "pain_score": 4},
    )
    assert result["suggested_specialty"]["primary"] == "General Practice"
    assert result["severity"] == "MEDIUM"
    assert result["priority_score"] == 40.0
    assert result["complaint_mapping"]["floor_changed_result"] is True
