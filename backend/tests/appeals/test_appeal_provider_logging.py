"""Provider failures remain diagnosable without logging keys or provider bodies."""
import asyncio
import logging
from unittest.mock import AsyncMock

import pytest
import requests

from app.models import appeal_generation_service as service
from app.models import gemini_service as gemini
from app.models.config import settings
from app.services import appeal_budget as budgets


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome,status,billed", [
    (None, "200", 1),
    ("403", "403", 0),
    ("429", "429", 1),
    ("503", "503", 0),
    ("timeout", "TimeoutError", 1),
    ("read_timeout", "ReadTimeout", 1),
    ("connection", "ConnectionError", 0),
])
async def test_call_status_is_logged_with_warning_root_and_without_secrets(monkeypatch, caplog, outcome, status, billed):
    private_key = "offline-sensitive-provider-token"
    private_prompt = "private-appeal-text-not-for-diagnostic-logs"
    monkeypatch.setattr(gemini, "_gemini_api_keys", lambda: [private_key])
    monkeypatch.setattr(settings, "GEMINI_MODEL", "offline-primary")
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "")
    monkeypatch.setattr(settings, "REQUEST_TIME_BUDGET_S", 25)
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda _: False)
    monkeypatch.setattr(service.asyncio, "sleep", AsyncMock())
    calls = []
    async def provider(prompt, temperature, api_key, **kwargs):
        calls.append(1)
        detail = f"provider-body ?key={private_key}"
        if outcome == "timeout":
            raise asyncio.TimeoutError(detail)
        if outcome == "read_timeout":
            raise requests.exceptions.ReadTimeout(detail)
        if outcome == "connection":
            raise ConnectionError(detail)
        if outcome is not None:
            raise RuntimeError(f"{outcome} {detail}")
        return "A recorded provider response."
    monkeypatch.setattr(gemini, "call_gemini_with_key", provider)
    budget = budgets.Budget(limit=1)
    # Exercise production logger configuration: setting it in the test would hide
    # the original bug in which the WARNING root suppressed every call status.
    with caplog.at_level(logging.WARNING):
        caplog.handler.setLevel(logging.INFO)
        assert service.logger.isEnabledFor(logging.INFO)
        if outcome is None:
            result, model = await service._call(private_prompt, budget)
            assert result == "A recorded provider response." and model == "offline-primary"
        else:
            with pytest.raises(budgets.BudgetExceeded):
                await service._call(private_prompt, budget)
    records = [r.getMessage() for r in caplog.records if r.name == service.__name__ and "Appeal Gemini" in r.getMessage()]
    assert len(records) == len(calls) == 1
    message = records[0]
    for field in ("key_index=1", "model=offline-primary", f"status={status}", "elapsed_ms=", f"calls_used={billed}", "provider_attempts=1"):
        assert field in message
    assert private_key not in caplog.text
    assert private_prompt not in caplog.text
    assert "provider-body" not in caplog.text
