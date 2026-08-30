import pytest
from app.models.nlp_service import (
    _is_valid_clinical_text,
    _map_to_specialty,
    extract_clinical_entities,
    SPECIALTY_TO_ML_GROUP,
    DEFAULT_ML_GROUP,
    DEFAULT_GROUP,
)


class TestIsValidClinicalText:
    def test_rejects_too_short(self):
        assert _is_valid_clinical_text("pain") is False

    def test_rejects_gibberish_chars(self):
        assert _is_valid_clinical_text("asdf qwer zxcv tyui opwq") is False

    def test_rejects_no_alpha(self):
        assert _is_valid_clinical_text("12345 6789 0000") is False

    def test_accepts_plain_prose(self):
        assert _is_valid_clinical_text("Patient presents with shortness of breath") is True

    def test_accepts_abbreviation_heavy_note(self):
        # Previously rejected: "SOB" and "CP" both lack vowels
        assert _is_valid_clinical_text("SOB c/o CP, diaphoresis") is True

    def test_accepts_mixed_abbreviation_prose(self):
        assert _is_valid_clinical_text("HTN patient with SOB and chest pain") is True

    def test_accepts_pure_abbreviation_list(self):
        assert _is_valid_clinical_text("HTN DM2 SOB CP diaphoresis") is True

    def test_rejects_single_repeated_short_word(self):
        assert _is_valid_clinical_text("no no no no no no no no") is False


class TestMapToSpecialty:
    def test_cardiovascular(self):
        specialty, ml_group, conf = _map_to_specialty(["chest pain", "tachycardia"])
        assert ml_group == "CARDIOVASCULAR"
        assert specialty == "Cardiovascular"
        assert 0.0 < conf <= 1.0

    def test_respiratory(self):
        _, ml_group, _ = _map_to_specialty(["dyspnea", "wheeze", "cough"])
        assert ml_group == "RESPIRATORY"

    def test_neurological(self):
        _, ml_group, _ = _map_to_specialty(["seizure", "confusion", "headache"])
        assert ml_group == "NEUROLOGIC"

    def test_trauma(self):
        _, ml_group, _ = _map_to_specialty(["fracture", "hemorrhage", "laceration"])
        assert ml_group == "TRAUMA"

    def test_infection(self):
        _, ml_group, _ = _map_to_specialty(["sepsis", "fever", "bacterial infection"])
        assert ml_group == "INFECTION_SYSTEMIC"

    def test_renal(self):
        _, ml_group, _ = _map_to_specialty(["renal failure", "creatinine", "hematuria"])
        assert ml_group == "RENAL_URINARY"

    def test_obstetric(self):
        _, ml_group, _ = _map_to_specialty(["pregnant", "eclampsia", "fetal distress"])
        assert ml_group == "OBSTETRIC_GYNECOLOGIC"

    def test_endocrine(self):
        _, ml_group, _ = _map_to_specialty(["diabetic ketoacidosis", "glucose", "insulin"])
        assert ml_group == "ENDOCRINE_METABOLIC"

    def test_empty_returns_defaults(self):
        specialty, ml_group, conf = _map_to_specialty([])
        assert specialty == DEFAULT_GROUP
        assert ml_group == DEFAULT_ML_GROUP
        assert conf == 0.0

    def test_unrecognised_returns_default(self):
        _, ml_group, _ = _map_to_specialty(["routine checkup", "annual review"])
        assert ml_group == DEFAULT_ML_GROUP

    def test_all_specialty_labels_have_ml_mapping(self):
        for specialty_label, ml_group in SPECIALTY_TO_ML_GROUP.items():
            assert ml_group, f"{specialty_label} maps to empty ML group"

    def test_ml_groups_are_valid_model_keys(self):
        valid_keys = {
            "CARDIOVASCULAR", "ENDOCRINE_METABOLIC", "GASTROINTESTINAL",
            "INFECTION_SYSTEMIC", "NEUROLOGIC", "OBSTETRIC_GYNECOLOGIC",
            "OTHER_EMERGENCY", "RENAL_URINARY", "RESPIRATORY", "TRAUMA",
        }
        for ml_group in SPECIALTY_TO_ML_GROUP.values():
            assert ml_group in valid_keys, f"'{ml_group}' is not a valid ML model key"


class TestExtractClinicalEntities:
    def test_invalid_text_returns_valid_false(self):
        result = extract_clinical_entities("aaa")
        assert result["valid"] is False
        assert result["condition_group"] == DEFAULT_ML_GROUP
        assert result["extracted_symptoms"] == []

    def test_gibberish_returns_valid_false(self):
        result = extract_clinical_entities("asdf qwer zxcv tyui opwq mnbv")
        assert result["valid"] is False

    def test_valid_note_returns_valid_true(self):
        result = extract_clinical_entities(
            "Patient presents with chest pain and shortness of breath"
        )
        assert result["valid"] is True

    def test_condition_group_is_uppercase_ml_key(self):
        valid_keys = {
            "CARDIOVASCULAR", "ENDOCRINE_METABOLIC", "GASTROINTESTINAL",
            "INFECTION_SYSTEMIC", "NEUROLOGIC", "OBSTETRIC_GYNECOLOGIC",
            "OTHER_EMERGENCY", "RENAL_URINARY", "RESPIRATORY", "TRAUMA",
        }
        result = extract_clinical_entities(
            "Patient with severe headache, confusion, and focal neurological deficit"
        )
        if result["valid"]:
            assert result["condition_group"] in valid_keys

    def test_abbreviation_note_is_valid(self):
        result = extract_clinical_entities("SOB and chest pain with diaphoresis")
        assert result["valid"] is True

    def test_symptoms_combined_with_note(self):
        result = extract_clinical_entities(
            clinical_note="Vital signs stable, awaiting labs",
            symptoms="chest pain, shortness of breath",
        )
        assert result["valid"] is True

    def test_response_has_required_fields(self):
        result = extract_clinical_entities("Patient reports nausea and vomiting after meals")
        assert "condition_group" in result
        assert "specialty" in result
        assert "extracted_symptoms" in result
        assert "confidence" in result
        assert "valid" in result

    def test_confidence_range(self):
        result = extract_clinical_entities("Severe abdominal pain with nausea and vomiting")
        assert 0.0 <= result["confidence"] <= 1.0
