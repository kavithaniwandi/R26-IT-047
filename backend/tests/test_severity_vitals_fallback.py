from app.models.config import settings
from app.models.severity_service import COMPLAINT_MAPPING_REVIEW_REASON, classify_note


VITALS_6 = {
    "vital_hr": 72,
    "vital_spo2": 98,
    "vital_sbp": 120,
    "vital_rr": 16,
    "vital_temp": 36.8,
    "pain_score": 1,
}


def test_six_vitals_uses_ml():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["method"] == "ml"
    assert result["ml_skipped_reason"] is None
    assert result["incomplete_vitals"] is False


def test_four_vitals_uses_ml():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
        vitals={key: VITALS_6[key] for key in ("vital_hr", "vital_spo2", "vital_sbp", "vital_rr")},
    )

    assert result["method"] == "ml"
    assert result["ml_skipped_reason"] is None
    assert result["incomplete_vitals"] is False


def test_three_vitals_falls_back_to_rule_based_and_floors_low_to_medium():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
        vitals={key: VITALS_6[key] for key in ("vital_hr", "vital_spo2", "vital_sbp")},
    )

    assert result["method"] == "rule_based"
    assert result["ml_skipped_reason"] == "insufficient_vitals"
    assert result["incomplete_vitals"] is True
    assert result["severity"] == "MEDIUM"
    assert "incomplete vitals" in " ".join(result["matched_rules"])


def test_no_vitals_falls_back_to_rule_based_and_floors_low_to_medium():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
    )

    assert result["method"] == "rule_based"
    assert result["ml_skipped_reason"] == "insufficient_vitals"
    assert result["incomplete_vitals"] is True
    assert result["severity"] == "MEDIUM"
    assert "incomplete vitals" in " ".join(result["matched_rules"])


def test_incomplete_vitals_preserves_high_rule_result():
    result = classify_note(
        clinical_note="severe bleeding after trauma",
        symptoms="bleeding trauma",
        age=45,
        mode="ml",
        vitals={key: VITALS_6[key] for key in ("vital_hr", "vital_spo2", "vital_sbp")},
    )

    assert result["method"] == "rule_based"
    assert result["incomplete_vitals"] is True
    assert result["severity"] in {"HIGH", "CRITICAL"}


def test_four_vitals_can_still_auto_assign_low():
    result = classify_note(
        clinical_note="cough",
        symptoms="cough",
        age=25,
        mode="ml",
        vitals={key: VITALS_6[key] for key in ("vital_hr", "vital_spo2", "vital_sbp", "vital_rr")},
    )

    assert result["incomplete_vitals"] is False
    assert result["mapped"] is True
    assert result["severity"] == "LOW"


def test_unrecognised_complaint_with_complete_vitals_floors_low_to_medium():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["incomplete_vitals"] is False
    assert result["mapped"] is False
    assert result["severity"] == "MEDIUM"
    assert result["mapping_review_reason"] == COMPLAINT_MAPPING_REVIEW_REASON


def test_low_acuity_synonyms_map_without_review_floor():
    result = classify_note(
        clinical_note="Mild headache, ran out of diabetes medication",
        symptoms="Mild headache, ran out of diabetes medication",
        age=55,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["incomplete_vitals"] is False
    assert result["mapped"] is True
    assert result["mapping_review_reason"] is None
    assert COMPLAINT_MAPPING_REVIEW_REASON not in result["matched_rules"]
    assert result["mapping_confidence"] >= settings.COMPLAINT_MAPPING_COVERAGE_THRESHOLD
    assert "headache pain in head" in result["mapped_complaints"]
    assert "medication refill" in result["mapped_complaints"]
    assert any(term in result["mapped_complaints"] for term in ("diabetes follow up", "diabetes management"))


def test_common_refill_phrase_maps_without_review_floor():
    result = classify_note(
        clinical_note="requesting medication refill, no complaints",
        symptoms="requesting medication refill, no complaints",
        age=55,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["mapped"] is True
    assert result["mapping_review_reason"] is None
    assert "medication refill" in result["mapped_complaints"]


def test_mapper_uses_clinical_note_when_symptoms_are_present():
    result = classify_note(
        clinical_note="Ran out of diabetes medication and needs refill.",
        symptoms="Mild headache",
        age=55,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["mapping_review_reason"] is None
    assert "headache pain in head" in result["mapped_complaints"]
    assert "medication refill" in result["mapped_complaints"]
    assert any(term in result["mapped_complaints"] for term in ("diabetes follow up", "diabetes management"))


def test_nonsense_complaint_still_triggers_review_floor():
    result = classify_note(
        clinical_note="xqzv blorp",
        symptoms="xqzv blorp",
        age=25,
        mode="ml",
        vitals=VITALS_6,
    )

    assert result["incomplete_vitals"] is False
    assert result["mapped"] is False
    assert result["severity"] == "MEDIUM"
    assert result["priority_score"] >= 40.0
    assert result["mapping_review_reason"] == COMPLAINT_MAPPING_REVIEW_REASON


def test_red_flag_case_is_unaffected_by_low_acuity_synonyms():
    result = classify_note(
        clinical_note="Mild headache, ran out of diabetes medication, now with chest pain",
        symptoms="Mild headache, ran out of diabetes medication",
        age=55,
        mode="ml",
        vitals=VITALS_6,
        has_red_flag=1,
        red_flag_count=1,
        rf_flags={"chest_pain": 1},
    )

    assert result["severity"] == "HIGH"
    assert result["mapping_review_reason"] is None
    assert result["mapped"] is True


def test_sudden_severe_headache_with_neuro_red_flag_and_high_sbp_is_not_low():
    result = classify_note(
        clinical_note="sudden severe headache with altered consciousness",
        symptoms="sudden severe headache",
        age=55,
        mode="ml",
        vitals={
            **VITALS_6,
            "vital_sbp": 190,
            "pain_score": 8,
        },
        has_red_flag=1,
        red_flag_count=1,
        rf_flags={"focal_neurologic_deficit": 1},
    )

    assert result["severity"] != "LOW"


def test_headache_with_hypoxia_and_tachycardia_is_not_low():
    result = classify_note(
        clinical_note="headache",
        symptoms="headache",
        age=45,
        mode="ml",
        vitals={
            **VITALS_6,
            "vital_hr": 130,
            "vital_spo2": 88,
        },
    )

    assert result["severity"] != "LOW"


def test_fractional_spo2_is_percent_with_warning_and_not_hypoxia_high():
    result = classify_note(
        clinical_note="Superficial 2 cm laceration from broken glass, bleeding controlled. Wound cleaned and dressed. Vitals stable.",
        symptoms="Small cut on the hand, mild pain",
        age=29,
        mode="ml",
        vitals={**VITALS_6, "vital_spo2": 0.99, "pain_score": 2},
    )

    assert result["vitals_warnings"][0]["code"] == "spo2_fraction_converted"
    assert result["vitals_warnings"][0]["used_value"] == 99
    assert result["severity"] != "HIGH"
    assert "SpO2 < 92" not in result["suggested_specialty"]["matched_keywords"]


def test_spo2_boundary_and_invalid_values():
    boundary = classify_note(
        clinical_note="Small cut, bleeding controlled, stable.",
        symptoms="Small cut",
        age=29,
        mode="ml",
        vitals={**VITALS_6, "vital_spo2": 92, "pain_score": 2},
    )
    dangerous_low = classify_note(
        clinical_note="Small cut, bleeding controlled, stable.",
        symptoms="Small cut",
        age=29,
        mode="ml",
        vitals={**VITALS_6, "vital_spo2": 9.9, "pain_score": 2},
    )
    harmless_high = classify_note(
        clinical_note="Small cut, bleeding controlled, stable.",
        symptoms="Small cut",
        age=29,
        mode="ml",
        vitals={**VITALS_6, "vital_spo2": 150, "pain_score": 2},
    )

    assert "SpO2 < 92" not in boundary["suggested_specialty"]["matched_keywords"]
    assert dangerous_low["vitals_warnings"][0]["code"] == "implausible_dangerous_low"
    assert "SpO2 < 92" in dangerous_low["suggested_specialty"]["matched_keywords"]
    assert harmless_high["vitals_warnings"][0]["code"] == "invalid_harmless_high"
    assert "SpO2 < 92" not in harmless_high["suggested_specialty"]["matched_keywords"]


def test_ran_out_of_insulin_with_confusion_and_abnormal_vitals_is_not_low():
    result = classify_note(
        clinical_note="ran out of insulin, confused and drowsy",
        symptoms="ran out of insulin, confused and drowsy",
        age=60,
        mode="ml",
        vitals={
            **VITALS_6,
            "vital_hr": 130,
            "vital_spo2": 88,
            "vital_rr": 26,
        },
    )

    assert result["severity"] != "LOW"
