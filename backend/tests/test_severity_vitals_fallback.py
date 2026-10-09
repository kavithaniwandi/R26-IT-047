from app.models.severity_service import classify_note


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
    assert "incomplete vitals — review" in result["matched_rules"]


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
    assert "incomplete vitals — review" in result["matched_rules"]


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
    assert result["mapping_review_reason"] == "complaint not recognised — review"
