"""Analyzer repair regressions with factual adversaries and real scoring parity."""
import pytest

from app.models import appeal_generation_service as service
from app.models import appeal_rewrite_validator as validator
from app.models import appeal_guidance_service as guide
from app.services import appeal_budget as budgets


SHORT = ("Brilliant students from low-income families are being forced to abandon their dreams of a college education "
         "simply because they cannot afford the cost of tuition and textbooks")
GROUNDED = SHORT + ". Please support these students so they can afford tuition and textbooks and pursue their college education."


@pytest.mark.parametrize("original,rewrite", [
    (SHORT, "Brilliant students from low-income families are being forced to abandon their dreams of a college education. "
            "They cannot afford the cost of tuition and textbooks. Please support these students."),
    ("You are not just funding a degree—you are empowering students.",
     "You are funding a degree. You are empowering students."),
    ("You are not only funding a degree but empowering students.",
     "You are funding a degree and empowering students."),
])
def test_safe_sentence_splitting_and_additive_rhetoric(original, rewrite):
    assert validator.validate_rewrite(original, rewrite).accepted


@pytest.mark.parametrize("original,rewrite", [
    ("Students cannot afford tuition.", "Students can afford tuition."),
    ("We do not provide food because families need shelter.", "We provide food. Families need shelter."),
    ("We can provide food because families need food.", "We provide food. Families need food."),
    ("We do not just provide food.", "We provide food."),
    ("You are not just funding a degree—you are empowering students.", "You are not funding a degree."),
    (SHORT, SHORT + ". Please support patients."),
    (SHORT, SHORT + ". Please donate $100 today."),
    (SHORT, SHORT + ". These students will graduate."),
])
def test_new_facts_negation_and_certainty_stay_blocked(original, rewrite):
    assert not validator.validate_rewrite(original, rewrite).accepted


def test_length_policy_does_not_require_padding_short_inputs():
    minimum, maximum, prompt = service._repair_length_policy(SHORT, None)
    assert minimum <= len(GROUNDED.split()) <= maximum
    assert "at least 65" not in prompt and "Do not double" not in prompt
    assert service._repair_length_policy(SHORT, "short")[:2] == (65, 100)


def test_missing_facts_suggestions_never_ask_for_invention():
    instructions = service._repair_instructions({"suggestions": [
        {"check": "amount_mentioned", "message": "Invent an amount"},
        {"check": "fund_use"}, {"check": "specific_call_to_action"},
    ]})
    assert "leave the amount unspecified" in instructions
    assert "otherwise leave it unspecified" in instructions
    assert "direct donation request" in instructions
    assert "Invent an amount" not in instructions


def test_edit_plan_targets_repeated_supplies_without_weakening_existing_request():
    text = ("Families in Gampaha need clean drinking water and food packs. "
            "Donate now to provide clean drinking water and food packs to these families.")
    instructions = service._repair_instructions({"suggestions": []}, text)
    assert "Reduce repetition" in instructions
    assert "clean drinking water" in instructions
    assert "Keep every distinct requested item" in instructions
    assert "Keep the existing final donation request" in instructions
    assert "do not weaken it or add new urgency" in instructions


def test_edit_plan_does_not_add_urgency_when_source_has_no_final_request():
    instructions = service._repair_instructions({}, "Families need food and water.")
    assert "Keep the existing final donation request" not in instructions
    assert "do not invent missing details" in instructions


@pytest.fixture
def isolated_repair(monkeypatch, tmp_path):
    monkeypatch.setattr(budgets, "DAILY", {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejections.jsonl")


@pytest.mark.asyncio
async def test_screenshot_repair_with_real_model_accepts_grounded_request(monkeypatch, isolated_repair):
    prompts = []
    async def provider(prompt, budget):
        prompts.append(prompt)
        budget.consume()
        budget.account(True)
        return GROUNDED, "offline-recorded-rewrite"
    monkeypatch.setattr(service, "_call", provider)
    result = await service.repair(SHORT, {"language": "English"}, "screenshot-test")
    assert result["original_score"] == result["before"]["raw_quality_score"]
    assert result["kept"] and result["improved_score"] > result["original_score"]
    assert result["improved_appeal"] == GROUNDED
    assert result["candidate_assessment"]["facts_passed"]
    assert result["candidate_assessment"]["length_passed"]
    assert "APPLICABLE GUIDANCE:" in prompts[0]
    assert "Do not add people, claims, deadlines, urgency, amounts" in prompts[0]
    assert "Do not double" not in prompts[0]
    assert len(prompts) == result["provider_attempts"] == 1


@pytest.mark.asyncio
async def test_rejected_candidate_scored_but_never_returned_as_accepted(monkeypatch, isolated_repair):
    monkeypatch.setattr(service, "_grounded_repair_candidate", lambda *args: None)
    calls = []
    def score(texts, language):
        calls.append(texts)
        value = 2.0 if texts == [SHORT] else 4.0
        label = "low" if value == 2 else "high"
        return [{"final_label": label, "quality_score": value, "raw_quality_score": value,
                 "confidence": .8, "class_probs": {label: .8}}]
    async def provider(prompt, budget):
        budget.consume()
        budget.account(True)
        return SHORT + ". Donate $100 today.", "offline-unsafe"
    monkeypatch.setattr(guide, "batch_score", score)
    monkeypatch.setattr(service, "_call", provider)
    result = await service.repair(SHORT, {"language": "English"}, "rejected-test")
    assert len(calls) == 2
    assert not result["kept"] and result["rejection_reason"] == "facts_guard"
    assert result["candidate_assessment"]["score"]["quality_score"] == 4.0
    assert result["candidate_assessment"]["guard_reason"] == "changed_amount"
    assert result["improved_appeal"] == result["after"]["appeal_text"] == SHORT
    assert result["improved_score"] == 2.0


@pytest.mark.asyncio
async def test_rate_limit_is_explained_without_spending_daily_allowance(monkeypatch, isolated_repair, caplog):
    monkeypatch.setattr(service, "_grounded_repair_candidate", lambda *args: None)
    async def provider(prompt, budget):
        budget.consume()
        budget.account(True)
        budget.last_status = "429"
        raise budgets.BudgetExceeded("429 rate limit")
    monkeypatch.setattr(service, "_call", provider)
    allowance = budgets.improvement_uses("rate-limit-test")[1]
    result = await service.repair(SHORT, {"language": "English"}, "rate-limit-test")
    assert result["provider_status"] == "429"
    assert "rate-limited" in result["message"]
    assert result["rejection_reason"] == "provider_error" and not result["kept"]
    assert result["candidate_assessment"] is None
    assert result["remaining_improve_uses"] == allowance
    assert result["provider_attempts"] == 1
    assert len(result["diagnostic_id"]) == 12
    assert "diagnostic_id=" + result["diagnostic_id"] in caplog.text
    assert "outcome=provider_error provider_status=429" in caplog.text
    assert "candidate_score=None" in caplog.text
    assert SHORT not in caplog.text
