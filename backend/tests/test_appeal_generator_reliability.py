"""Generator recovery uses mocked providers and temporary credit state only."""
import json
from unittest.mock import AsyncMock

import pytest
import requests

from app.models import appeal_generation_service as service, appeal_guidance_service as guide, gemini_service as gs
from app.models.config import settings
from app.services import appeal_budget as budgets, credit_monitor as cm

PAYLOAD = {"language": "English", "campaign_type": "Flood Relief", "location": "Malabe",
           "verified_need": "water bottles and tents for 20 people", "campaign_goal": "support affected families",
           "length_category": "short"}
TEXT = "Families in Malabe need water bottles and tents for 20 people. Please donate."


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(budgets, "SESSIONS", {})
    monkeypatch.setattr(settings, "GEMINI_MODEL", "offline-model")
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "")
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["offline-first", "offline-second"])
    monkeypatch.setattr(cm, "is_exhausted", lambda _: False)
    score = {"quality_label": "medium", "final_label": "medium", "quality_score": 3.0,
             "raw_quality_score": 3.0, "confidence": .8, "class_probs": {"medium": .8}}
    monkeypatch.setattr(gs, "score_text", lambda *args: dict(score))
    monkeypatch.setattr(guide, "batch_score", lambda texts, language: [dict(score) for _ in texts])


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["429 daily quota", "403 permission rejected", "401 invalid key"])
async def test_generation_fails_over_and_records_outcomes(monkeypatch, failure):
    provider = AsyncMock(side_effect=[RuntimeError(failure), TEXT])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    result = await service.generate(PAYLOAD)
    assert result[0]["generator_status"] == "live"
    assert [call.args[2] for call in provider.await_args_list] == ["offline-first", "offline-second"]
    state = budgets.session(PAYLOAD)
    assert not state["flow"].stopped and state["flow"].attempts == 2
    assert cm._key_state["gemini_key_1"]["last_status"] == failure[:3]
    assert cm._key_state["gemini_key_2"]["last_status"] == "200"
    assert cm._key_state["gemini_key_2"]["calls"] == 1


@pytest.mark.asyncio
async def test_failed_cache_retries_after_cooldown_without_repeating_success(monkeypatch):
    pair = json.dumps({"appeals": [{"style": "community", "appeal_text": TEXT},
                                    {"style": "urgent", "appeal_text": TEXT + " Support families."}]})
    provider = AsyncMock(side_effect=[TEXT, requests.exceptions.ReadTimeout(), pair])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    first = await service.generate(PAYLOAD)
    assert await service.generate(PAYLOAD, remaining=True) == []
    assert await service.generate(PAYLOAD, remaining=True) == []
    assert provider.await_count == 2  # No hot retry of a potentially billable timeout.
    state = budgets.session(PAYLOAD)
    state["retry_at"]["remaining"] = 0
    recovered = await service.generate(PAYLOAD, remaining=True)
    assert len(recovered) == 2 and all(v["generator_status"] == "live" for v in recovered)
    assert provider.await_count == 3
    assert await service.generate(PAYLOAD) is first
    assert provider.await_count == 3 and not state["partial"] and not state["errors"]


@pytest.mark.asyncio
async def test_cached_template_can_recover(monkeypatch):
    provider = AsyncMock(side_effect=[RuntimeError("400 malformed request"), TEXT])
    monkeypatch.setattr(gs, "call_gemini_with_key", provider)
    assert (await service.generate(PAYLOAD))[0]["generator_status"] == "fallback"
    assert (await service.generate(PAYLOAD))[0]["generator_status"] == "fallback"
    assert provider.await_count == 1
    state = budgets.session(PAYLOAD)
    state["retry_at"]["first"] = 0
    assert (await service.generate(PAYLOAD))[0]["generator_status"] == "live"
    assert provider.await_count == 2


def test_status_labels_do_not_claim_stale_calls_are_live_health():
    cm._key_state["gemini_key_1"] = {"calls": 100, "exhausted": False}
    status = cm.get_status()
    key = next(p for p in status["providers"] if p["provider"] == "GEMINI_KEY_1")
    assert key["status_label"] == "Not checked"
    assert "not a live quota check" in status["message"]


def test_recorded_status_and_daily_counters_are_sanitized():
    cm.record_result("gemini_key_1", "429", 60)
    assert cm._key_state["gemini_key_1"]["retry_after"]
    cm.record_result("gemini_key_2", "200")
    assert cm._key_state["gemini_key_2"]["calls"] == 1
    assert cm._key_state["gemini_key_2"]["attempts_today"] == 1
    assert cm._key_state["gemini_key_2"]["last_status"] == "200"


def test_english_template_meets_short_band_without_invented_urgency():
    text = gs._build_fallback_appeal(PAYLOAD)
    assert guide.length_warning(text, "short") is None
    assert "urgently" not in text and "today" not in text
    assert PAYLOAD["verified_need"] in text and PAYLOAD["campaign_goal"] in text
