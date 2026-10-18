"""Ground a donation request's intended benefit without asserting a new outcome."""
import pytest

from app.models import appeal_rewrite_validator as validator

ORIGINAL = (
    "Brilliant students from low-income families are being forced to abandon their dreams of a college education "
    "simply because they cannot afford the cost of tuition and textbooks. Academic talent is everywhere, but equal "
    "opportunity is not, leaving thousands of capable young minds locked out of the future they have worked so hard to build."
)
REQUEST = "Please support these students so they can afford tuition and textbooks and pursue their college education."
REWRITE = ORIGINAL + " " + REQUEST


def test_exact_recorded_rewrite_passes_without_changing_negative_assertions():
    assert validator.validate_rewrite(ORIGINAL, REWRITE).accepted
    assert "cannot afford" in REWRITE


@pytest.mark.parametrize("action_text", [
    "Please support these students so they can afford tuition and textbooks.",
    "Please support these students so that they could afford tuition.",
    "Please support these students so they may pursue their college education.",
])
def test_same_beneficiaries_and_stated_goal_are_admitted(action_text):
    assert validator.validate_rewrite(ORIGINAL, ORIGINAL + " " + action_text).accepted


@pytest.mark.parametrize("action_text", [
    "Please support these students so they will afford tuition.",
    "Please support these students so they can afford medicine.",
    "Please support these patients so they can afford tuition.",
    "Please support these families so they can afford tuition.",
    "Please support these students so they can pursue their medical education.",
    "Please support these students so they can graduate.",
    "Please support these students so they can afford tuition today.",
    "Please support these students with $100 so they can afford tuition.",
    "Please support these students so they can pursue tuition.",
    "Please support these students so they can afford.",
    "Please support these students so they can guarantee admission.",
])
def test_new_facts_promises_urgency_and_changed_recipients_stay_blocked(action_text):
    assert not validator.validate_rewrite(ORIGINAL, ORIGINAL + " " + action_text).accepted


def test_purpose_exception_never_turns_inability_into_a_factual_assertion():
    assert not validator.validate_rewrite(ORIGINAL, ORIGINAL.replace("cannot afford", "can afford")).accepted


def test_benefit_cannot_be_borrowed_from_another_beneficiary():
    original = "Students cannot afford tuition. Families need medicine."
    rewrite = original + " Please support students so they can afford medicine."
    assert not validator.validate_rewrite(original, rewrite).accepted


def test_goal_cannot_be_borrowed_from_another_beneficiary():
    original = "Students cannot afford tuition. Families dream of a home."
    rewrite = original + " Please support students so they can pursue a home."
    assert not validator.validate_rewrite(original, rewrite).accepted


@pytest.mark.parametrize("original,purpose", [
    ("Students do not dream of a college education.", "pursue a college education"),
    ("Students dream of not attending college.", "pursue college"),
    ("Students cannot afford tuition but do not need medicine.", "afford medicine"),
    ("Students need tuition whereas families need medicine.", "need medicine"),
])
def test_negated_goals_and_other_recipients_are_not_inferred(original, purpose):
    rewrite = original + f" Please support students so they can {purpose}."
    assert not validator.validate_rewrite(original, rewrite).accepted


@pytest.mark.asyncio
@pytest.mark.parametrize("visible_gain", [True, False])
async def test_recorded_reply_is_accepted_with_or_without_score_gain(monkeypatch, tmp_path, visible_gain):
    from app.models import appeal_generation_service as service
    # Isolate the recorded provider reply; grounded fallback has its own real-model tests.
    monkeypatch.setattr(service, "_grounded_repair_candidate", lambda *args: None)
    from app.services import appeal_budget as budgets
    def score(label, value):
        return {"final_label": label, "quality_score": value, "raw_quality_score": value,
                "confidence": .8, "class_probs": {label: .8}}
    scores = iter([[score("medium", 3.0)], [score("high", 3.9) if visible_gain else score("medium", 3.0)]])
    scored = []
    def batch(texts, language):
        scored.append(texts)
        return next(scores)
    monkeypatch.setattr(service.guide, "batch_score", batch)
    monkeypatch.setattr(service.guide, "guidance", lambda *args: {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    calls = []
    async def provider(prompt, budget):
        calls.append(prompt)
        budget.consume()
        budget.account(True)
        return REWRITE, "offline-provider"
    monkeypatch.setattr(service, "_call", provider)
    client = "grounded-purpose-test"
    day = budgets.improvement_day()
    prior = budgets.DAILY.pop((day, client), None)
    try:
        allowance = budgets.improvement_uses(client)[1]
        result = await service.repair(ORIGINAL, {"language": "English"}, client)
        assert scored == [[ORIGINAL], [REWRITE]]
        assert result["kept"]
        assert result["improved_appeal"] == REWRITE
        assert result["rejection_reason"] is None
        assert result["remaining_improve_uses"] == allowance - 1
        assert len(calls) == result["gemini_calls_used"] == 1
    finally:
        budgets.DAILY.pop((day, client), None)
        if prior is not None:
            budgets.DAILY[(day, client)] = prior
