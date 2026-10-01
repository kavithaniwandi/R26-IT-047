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


def test_three_vitals_falls_back_to_rule_based():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
        vitals={key: VITALS_6[key] for key in ("vital_hr", "vital_spo2", "vital_sbp")},
    )

    assert result["method"] == "rule_based"
    assert result["ml_skipped_reason"] == "insufficient_vitals"


def test_no_vitals_falls_back_to_rule_based():
    result = classify_note(
        clinical_note="Cold",
        symptoms="Cold",
        age=25,
        mode="ml",
    )

    assert result["method"] == "rule_based"
    assert result["ml_skipped_reason"] == "insufficient_vitals"
