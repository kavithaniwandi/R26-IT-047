# Approved UI consistency pass: shared word bands and upper-half targets replace prior length expectations.
"""Offline checks for repair rejection, allowance refunds and disagreement wording."""
import asyncio
import json

import pytest

from app.models import appeal_generation_service as generation
from app.models import appeal_guidance_service as guidance
from app.models.config import settings
from app.models.schemas import GuidanceFields
from app.services import appeal_budget as budgets

TEXT = "Families in Malabe need water bottles and tents for 20 people. Please donate today."
VALID = " ".join([TEXT] * 5)


def score(confidence=0.7):
    return {"final_label": "medium", "quality_score": 3.0, "raw_quality_score": 3.0,
            "confidence": confidence, "classifier_confidence": confidence,
            "class_probs": {"medium": confidence}}


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    budgets.DAILY.clear()
    monkeypatch.setattr(settings, "DAILY_IMPROVE_LIMIT", 1)
    monkeypatch.setattr(generation, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    monkeypatch.setattr(guidance, "guidance", lambda *args: {})
    monkeypatch.setattr(guidance, "batch_score", lambda *args: [score()])


@pytest.mark.asyncio
@pytest.mark.parametrize("reason,rewrite", [
    ("facts_guard", VALID.replace("20 people", "21 people")),
    ("length_guard", TEXT),
    ("provider_error", None),
])
async def test_rejected_rewrite_refunds_allowance_but_retains_billed_call(monkeypatch, reason, rewrite):
    async def call(prompt, budget):
        budget.consume()
        budget.account(True)
        if rewrite is None:
            raise budgets.BudgetExceeded("provider unavailable")
        return rewrite, "offline-model"
    monkeypatch.setattr(generation, "_call", call)
    result = await generation.repair(TEXT, {"language": "English", "length_category": "short"}, "ip")
    assert result["rejection_reason"] == reason
    assert result["message"] and not result["kept"]
    assert result["remaining_improve_uses"] == 1
    assert result["gemini_calls_used"] == 1
    assert result["improved_appeal"] == TEXT
    if reason in ("facts_guard", "length_guard"):
        assert "Original retained:" in result["message"]
    if rewrite is not None:
        record = json.loads(generation.REJECTION_LOG_PATH.read_text(encoding="utf-8"))
        assert record["guard"] == reason and record["rewrite"] == rewrite
        assert reason in record["failed_guards"]
    # A rejected attempt leaves the next attempt available even with a daily limit of one.
    again = await generation.repair(TEXT, {"language": "English", "length_category": "short"}, "ip")
    assert again["attempted"] and again["remaining_improve_uses"] == 1


@pytest.mark.asyncio
async def test_kept_rewrite_spends_allowance(monkeypatch):
    # Approved policy: use a visible score gain to exercise allowance consumption.
    scores = iter([[{**score(0.6), "quality_score": 2.9}], [score(0.8)], [score(0.6)]])
    monkeypatch.setattr(guidance, "batch_score", lambda *args: next(scores))
    async def call(prompt, budget):
        budget.consume()
        budget.account(True)
        return VALID, "offline-model"
    monkeypatch.setattr(generation, "_call", call)
    result = await generation.repair(TEXT, {"length_category": "short"}, "ip")
    assert result["kept"] and result["rejection_reason"] is None
    assert result["remaining_improve_uses"] == 0
    blocked = await generation.repair(TEXT, {}, "ip")
    assert not blocked["attempted"] and blocked["gemini_calls_used"] == 0
    assert not generation.REJECTION_LOG_PATH.exists()


def test_rejection_diagnostic_redacts_configured_and_runtime_keys(monkeypatch):
    from app.models import gemini_service
    secret = "offline-test-sensitive-value"
    monkeypatch.setenv("DIAGNOSTIC_TEST_API_KEY", secret)
    monkeypatch.setattr(gemini_service, "_gemini_api_keys", lambda: [secret])
    generation._log_rejected_rewrite(f"Original facts {secret} https://example.test/?key=unconfigured-value", "facts_guard")
    record = json.loads(generation.REJECTION_LOG_PATH.read_text(encoding="utf-8"))
    assert secret not in record["rewrite"]
    assert "unconfigured-value" not in record["rewrite"]
    assert "Original facts" in record["rewrite"] and "[REDACTED]" in record["rewrite"]


def test_refund_does_not_subtract_from_new_day(monkeypatch):
    budgets.DAILY[("old-day", "ip")] = 1
    budgets.DAILY[("new-day", "ip")] = 1
    monkeypatch.setattr(budgets, "improvement_day", lambda: "new-day")
    assert budgets.refund_improvement("ip", "old-day") == 0
    assert budgets.DAILY[("new-day", "ip")] == 1


@pytest.mark.asyncio
async def test_cancelled_attempt_releases_reservation(monkeypatch):
    async def cancel(*args):
        raise asyncio.CancelledError()
    monkeypatch.setattr(generation, "_call", cancel)
    with pytest.raises(asyncio.CancelledError):
        await generation.repair(TEXT, {}, "ip")
    assert budgets.improvement_uses("ip")[1] == 1


@pytest.mark.parametrize("category,minimum,target", [("short", 65, "85-95"), ("medium", 105, "130-145"), ("long", 185, "220-240")])
@pytest.mark.asyncio
async def test_explicit_minimum_in_both_prompts(monkeypatch, category, minimum, target):
    payload = {"campaign_type": "Flood Relief", "length_category": category}
    assert f"at least {minimum} words" in generation._prompt(payload)
    assert f"TARGET: {target}" in generation._prompt(payload)
    async def call(prompt, budget):
        assert f"at least {minimum} words" in prompt
        assert f"Target {target} words" in prompt
        raise budgets.BudgetExceeded("offline")
    monkeypatch.setattr(generation, "_call", call)
    await generation.repair(TEXT, payload)


def test_agreement_note_survives_response_schema_without_changing_level():
    result = guidance.confidence_metadata({"final_label": "low", "class_probs": {"high": 0.8, "low": 0.2}})
    assert result["agreement_note"] == "Rating and classifier disagree"
    assert result["confidence_level"] == "borderline"
    assert GuidanceFields(**result).model_dump()["agreement_note"] == result["agreement_note"]
    assert guidance.confidence_metadata({"final_label": "high", "class_probs": {"high": 0.8}})["agreement_note"] is None
