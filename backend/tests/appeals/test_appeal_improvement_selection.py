"""Distinct, fact-preserving revisions are accepted independently of score."""

import pytest

from app.models.appeal_improvement_selection import has_new_wording


def rating(label="medium", score=3.0, confidence=.6, agreement=True):
    return {"final_label": label, "quality_score": score, "raw_quality_score": 3.45,
            "predicted_class": label if agreement else ("medium" if label == "high" else "high"),
            "classifier_confidence": confidence, "label_agreement": agreement}


@pytest.mark.asyncio
async def test_unchanged_provider_reply_is_retained_and_daily_use_refunded(monkeypatch, tmp_path):
    from app.models import appeal_generation_service as service
    from app.services import appeal_budget as budgets
    text = " ".join(["Families in Malabe need water bottles and tents for 20 people. Please donate today."] * 5)
    def scored(confidence):
        return {**rating(confidence=confidence), "confidence": confidence,
                "class_probs": {"medium": confidence}}
    values = iter([[scored(.6)], [scored(.8)]])
    monkeypatch.setattr(service.guide, "batch_score", lambda *args: next(values))
    monkeypatch.setattr(service.guide, "guidance", lambda *args: {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    calls = []
    async def provider(prompt, budget):
        calls.append(prompt)
        budget.consume()
        budget.account(True)
        return text, "offline-provider"
    monkeypatch.setattr(service, "_call", provider)
    client = "visible-improvement-test"
    day = budgets.improvement_day()
    prior = budgets.DAILY.pop((day, client), None)
    try:
        allowance = budgets.improvement_uses(client)[1]
        result = await service.repair(text, {"language": "English"}, client)
        assert not result["kept"] and result["rejection_reason"] == "unchanged_text"
        assert result["improved_appeal"] == text
        assert result["remaining_improve_uses"] == allowance
        assert len(calls) == result["gemini_calls_used"] == 1
    finally:
        budgets.DAILY.pop((day, client), None)
        if prior is not None:
            budgets.DAILY[(day, client)] = prior


@pytest.mark.parametrize("candidate,changed", [
    ("Families need water.", False), ("  FAMILIES need water!  ", False),
    ("Families require water.", True), ("", False),
])
def test_only_distinct_wording_counts_as_a_revision(candidate, changed):
    assert has_new_wording("Families need water.", candidate) is changed


@pytest.mark.asyncio
@pytest.mark.parametrize("after_score,after_label", [(3.9, "medium"), (2.9, "low")])
async def test_new_safe_revision_is_kept_without_score_or_classifier_gain(monkeypatch, tmp_path, after_score, after_label):
    from app.models import appeal_generation_service as service
    original = "Families in Gampaha need water. Please donate."
    rewrite = "Families in Gampaha require water. Please donate."
    def score(value, label):
        return {"quality_score": value, "raw_quality_score": value, "final_label": label,
                "predicted_class": label, "class_probs": {label: .8}, "confidence": .8}
    scores = iter([[score(3.9, "medium")], [score(after_score, after_label)]])
    monkeypatch.setattr(service.guide, "batch_score", lambda *args: next(scores))
    monkeypatch.setattr(service.guide, "guidance", lambda *args: {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    async def provider(prompt, budget):
        budget.consume()
        budget.account(True)
        return rewrite, "offline"
    monkeypatch.setattr(service, "_call", provider)
    result = await service.repair(original, {"language": "English"}, "accept-new-wording")
    assert result["kept"] and result["improved_appeal"] == rewrite
    assert result["improved_score"] == after_score
    assert result["after"]["predicted_class"] == after_label
    assert result["rejection_reason"] is None
