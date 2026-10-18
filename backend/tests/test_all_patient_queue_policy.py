import pytest

from app.models.severity_service import _build_queue_policy, classify_note


@pytest.mark.parametrize("severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
@pytest.mark.parametrize("risk", [0, 20, 39, 40, 100])
@pytest.mark.parametrize("matched", [[], ["existing matched rule"]])
def test_all_registered_patients_enter_queue(severity, risk, matched):
    policy = _build_queue_policy(severity, risk, "ml", matched, None)
    assert policy["should_queue"] is True
    assert policy["queue_reason"] == "auto_triage"
    assert policy["method"] == "ml"
    assert "Excluded" not in policy["queue_reason_text"]
    assert "No queue action" not in policy["display_note"]
    if severity == "LOW":
        assert "after" in policy["display_note"]


def test_critical_trigger_still_requires_immediate_review():
    policy = _build_queue_policy("CRITICAL", 100, "rule_based", ["unresponsive"], "unresponsive")
    assert policy["should_queue"] is True
    assert policy["queue_reason"] == "rule_flag"
    assert "immediately" in policy["recommended_action"]


def test_low_ml_prediction_is_queued_without_raising_severity_or_score():
    result = classify_note(
        clinical_note="Mild headache, stable and alert.", symptoms="mild headache", age=25, mode="ml",
        vitals={"vital_hr": 78, "vital_spo2": 98, "vital_sbp": 120, "vital_rr": 16, "vital_temp": 37, "pain_score": 2},
    )
    assert result["severity"] == "LOW"
    assert result["priority_score"] < 40
    assert result["should_queue"] is True
    assert result["queue_reason"] == "auto_triage"
