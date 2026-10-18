"""Bounded key failover and fact-preserving fallback; no network requests."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from app.models import appeal_generation_service as service, gemini_service as gs
from app.models.config import settings
from app.models.appeal_rewrite_validator import validate_rewrite
from app.services import appeal_budget as budgets

TEXT = ("Brilliant students from low-income families are being forced to abandon their dreams of a college education "
        "simply because they cannot afford the cost of tuition and textbooks.")


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "_REPAIR_KEY_COOLDOWNS", {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    monkeypatch.setattr(budgets, "DAILY", {})
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda _: False)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["offline-1", "offline-2", "offline-3", "offline-4"])
    monkeypatch.setattr(settings, "GEMINI_MODEL", "offline-model")


@pytest.mark.asyncio
@pytest.mark.parametrize("error", ["429 per day quota", "429 per minute", "403 forbidden", "401 invalid key", "503 unavailable"])
async def test_failed_primary_rotates_and_cools_down_without_retrying_success(monkeypatch, error):
    provider = AsyncMock(side_effect=[RuntimeError(error), "A grounded rewrite", "Another rewrite"])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    budget = budgets.Budget(limit=3, allow_key_failover=True)
    text, model = await service._call("private prompt", budget)
    assert text == "A grounded rewrite" and model == "offline-model"
    assert budget.attempts == 2 and budget.last_status == "200"
    assert [call.args[2] for call in provider.await_args_list] == ["offline-1", "offline-2"]
    second = budgets.Budget(limit=3, allow_key_failover=True)
    await service._call("another prompt", second)
    assert provider.await_args.args[2] == "offline-2"
    assert second.attempts == 1


@pytest.mark.asyncio
async def test_all_failed_keys_stop_at_three_attempts(monkeypatch):
    provider = AsyncMock(side_effect=RuntimeError("429 daily quota"))
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    budget = budgets.Budget(limit=3, allow_key_failover=True)
    with pytest.raises(budgets.BudgetExceeded):
        await service._call("prompt", budget)
    assert provider.await_count == budget.attempts == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [asyncio.TimeoutError(), RuntimeError("400 malformed request")])
async def test_timeout_or_bad_request_does_not_probe_other_keys(monkeypatch, error):
    provider = AsyncMock(side_effect=error)
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    with pytest.raises(budgets.BudgetExceeded):
        await service._call("prompt", budgets.Budget(limit=3, allow_key_failover=True))
    assert provider.await_count == 1


@pytest.mark.asyncio
async def test_503_uses_next_key_and_stops_after_one_success(monkeypatch):
    provider = AsyncMock(side_effect=[RuntimeError("503 unavailable"), "One rewrite", "Unused"])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    monkeypatch.setattr(service.asyncio, "sleep", AsyncMock())
    budget = budgets.Budget(limit=3, allow_key_failover=True)
    text, _ = await service._call("one variant", budget)
    assert text == "One rewrite"
    assert provider.await_count == budget.attempts == 2
    assert budget.calls == 1
    assert [call.args[2] for call in provider.await_args_list] == ["offline-1", "offline-2"]
    service.asyncio.sleep.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("limit,expected_attempts", [(1, 1), (3, 3)])
async def test_persistent_503_is_bounded(monkeypatch, limit, expected_attempts):
    provider = AsyncMock(side_effect=RuntimeError("503 unavailable"))
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    monkeypatch.setattr(service.asyncio, "sleep", AsyncMock())
    budget = budgets.Budget(limit=limit, allow_key_failover=True)
    with pytest.raises(budgets.BudgetExceeded):
        await service._call("one variant", budget)
    assert provider.await_count == budget.attempts == expected_attempts
    assert budget.calls == 0
    assert len({call.args[2] for call in provider.await_args_list}) == expected_attempts


@pytest.mark.asyncio
async def test_rate_limited_first_key_and_overloaded_second_use_third(monkeypatch):
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda label: label == "gemini_key_1")
    provider = AsyncMock(side_effect=[RuntimeError("503 unavailable"), "Third key rewrite"])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    budget = budgets.Budget(limit=3, allow_key_failover=True)
    text, _ = await service._call("one variant", budget)
    assert text == "Third key rewrite"
    assert [call.args[2] for call in provider.await_args_list] == ["offline-2", "offline-3"]
    assert budget.attempts == 2 and budget.calls == 1


@pytest.mark.asyncio
async def test_later_requests_can_reach_all_configured_keys_with_bounded_attempts(monkeypatch):
    keys = [f"offline-{i}" for i in range(1, 12)]
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: keys)
    provider = AsyncMock(side_effect=[*[RuntimeError("503 unavailable") for _ in range(9)], "Tenth key rewrite"])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    for _ in range(3):
        budget = budgets.Budget(limit=3, allow_key_failover=True)
        with pytest.raises(budgets.BudgetExceeded):
            await service._call("one variant", budget)
        assert budget.attempts == 3
    text, _ = await service._call("one variant", budgets.Budget(limit=3, allow_key_failover=True))
    assert text == "Tenth key rewrite"
    assert [call.args[2] for call in provider.await_args_list] == keys[:10]


@pytest.mark.asyncio
async def test_503_retry_does_not_exceed_shared_attempts(monkeypatch):
    provider = AsyncMock(side_effect=RuntimeError("503 unavailable"))
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    budget = budgets.Budget(limit=3, attempts=2, allow_key_failover=True)
    with pytest.raises(budgets.BudgetExceeded):
        await service._call("review within remaining budget", budget)
    assert provider.await_count == 1
    assert budget.attempts == 3


def test_grounded_candidate_preserves_original_and_does_not_invent_facts():
    candidate = service._grounded_repair_candidate(TEXT, "English")
    assert candidate.startswith(TEXT + " ")
    assert validate_rewrite(TEXT, candidate).accepted
    assert len(candidate.split()) <= service._repair_length_policy(TEXT, None)[1]
    assert service._grounded_repair_candidate("Students cannot afford tuition. Please donate.", "English") is None
    unrelated = service._grounded_repair_candidate("Students do not dream of a degree. Families cannot afford tuition.", "English")
    assert unrelated is not None and "pursue" not in unrelated
    assert service._grounded_repair_candidate(TEXT, "Sinhala") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_unavailable", [False, True])
async def test_exact_appeal_improves_with_real_model_even_when_provider_is_weak(monkeypatch, provider_unavailable):
    async def provider(prompt, budget):
        budget.consume()
        budget.account(True)
        if provider_unavailable:
            budget.last_status = "429"
            raise budgets.BudgetExceeded("daily quota")
        budget.last_status = "200"
        return TEXT, "offline-model"
    monkeypatch.setattr(service, "_call", provider)
    result = await service.repair(TEXT, {"language": "English"}, "real-model-fallback")
    assert result["kept"] and result["original_score"] == result["before"]["raw_quality_score"]
    assert result["improved_score"] > result["original_score"]
    assert result["rewrite_source"] == "grounded_request"
    assert validate_rewrite(TEXT, result["improved_appeal"]).accepted
    assert result["provider_attempts"] == 1
    assert result["candidate_assessment"]["score"]["quality_score"] == result["improved_score"]
