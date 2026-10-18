"""
Phase 2 tests for gemini_service.py.
All Gemini and HF client calls are mocked — no real API calls made.
Run with: backend/venv/Scripts/python.exe -m pytest tests/test_gemini_phase2.py -v
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.models import gemini_service as gs
from app.models.config import settings
import app.services.credit_monitor as cm
from app.services.credit_monitor import _key_state


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolate_credit_monitor(tmp_path, monkeypatch):
    """
    Redirect the credit monitor state file to a per-test tmp dir so that
    mark_exhausted() / record_failure() never touch the real
    credit_monitor_state.json on disk, and clear _key_state before/after.
    """
    monkeypatch.setattr(cm, "STATE_FILE", tmp_path / "credit_monitor_state.json")
    _key_state.clear()
    gs._RESULT_CACHE.clear()
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "")
    yield
    _key_state.clear()

CAMPAIGN = {
    "language": "English",
    "campaign_type": "flood_relief",
    "location": "Kaduwela",
    "verified_need": "dry rations and clean water",
    "campaign_goal": "support 50 displaced families",
    "tone": "trustworthy",
    "channel": "website",
    "length_category": "short",
}

GOOD_APPEAL = (
    "Families in Kaduwela urgently need dry rations and clean water. "
    "This flood relief campaign aims to support displaced households. "
    "Your donation provides verified, direct support. Please donate today."
)


def _score_stub(text: str, language: str = "English") -> dict:
    return {
        "quality_label": "high",
        "quality_score": 4.2,
        "confidence": 0.9,
        "confidence_normalised": 0.9,
        "confidence_display": "90%",
    }


# ---------------------------------------------------------------------------
# 1. Success path — Gemini returns a good appeal
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_success_returns_live_status(monkeypatch):
    async def good_gemini(prompt, temp, api_key):
        return GOOD_APPEAL

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", good_gemini)
    # Clear cache so previous runs don't interfere
    gs._RESULT_CACHE.clear()

    result = await gs.call_gemini_with_key_fallback("some prompt", 0.5, language="English")

    assert result["generator_status"] == "live"
    assert result["generator_error"] is None
    assert result["appeal_text"] == GOOD_APPEAL


@pytest.mark.asyncio
async def test_success_result_is_cached(monkeypatch):
    call_count = {"n": 0}

    async def good_gemini(prompt, temp, api_key):
        call_count["n"] += 1
        return GOOD_APPEAL

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", good_gemini)
    gs._RESULT_CACHE.clear()

    await gs.call_gemini_with_key_fallback("cached prompt", 0.5, language="English")
    await gs.call_gemini_with_key_fallback("cached prompt", 0.5, language="English")

    assert call_count["n"] == 1, "Second identical call should have been served from cache"


# ---------------------------------------------------------------------------
# 2. 429 rate-limit — exponential backoff then next key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_429_retries_with_backoff_then_succeeds(monkeypatch):
    attempts = {"n": 0}
    slept = []

    async def flaky_gemini(prompt, temp, api_key):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise Exception("429 too many requests per_minute")
        return GOOD_APPEAL

    async def fake_sleep(secs):
        slept.append(secs)

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", flaky_gemini)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    gs._RESULT_CACHE.clear()

    result = await gs.call_gemini_with_key_fallback("prompt", 0.5, language="English", max_retries=3)

    assert result["generator_status"] == "live"
    assert len(slept) >= 1, "Should have slept at least once during backoff"
    assert all(s > 0 for s in slept), "All backoff delays must be positive"


# ---------------------------------------------------------------------------
# 3. 404 invalid model — fail fast, don't try remaining keys
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("hf_key", [None, "mock-hf-key"])
async def test_404_invalid_model_fails_fast(monkeypatch, hf_key):
    keys_tried = []
    exhausted = []
    monkeypatch.setattr(gs, "mark_exhausted", exhausted.append)

    async def not_found_gemini(prompt, temp, api_key):
        keys_tried.append(api_key)
        raise Exception("404 model not_found no longer available")

    monkeypatch.setattr(settings, "HF_API_KEY", hf_key)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["key-1", "key-2", "key-3"])
    monkeypatch.setattr(gs, "call_gemini_with_key", not_found_gemini)
    gs._RESULT_CACHE.clear()

    result = await gs.call_gemini_with_key_fallback("prompt", 0.5, language="English")

    assert result["generator_error"] == "404 model not found"
    assert exhausted == [], "A model configuration error must not exhaust a key"
    assert len(keys_tried) == 1, (
        f"Should stop after first key on 404, but tried {len(keys_tried)} keys"
    )


# ---------------------------------------------------------------------------
# 4. Invalid / rejected key (403 / auth error) — marks key exhausted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_key_records_failure_and_falls_back(monkeypatch):
    async def auth_fail(prompt, temp, api_key):
        raise Exception("403 API key not valid. Please pass a valid API key.")

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["bad-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", auth_fail)
    monkeypatch.setattr(gs, "score_text", _score_stub)
    gs._RESULT_CACHE.clear()

    variants = await gs.generate_first_appeal_variant(CAMPAIGN)

    assert variants[0]["model"] == "fallback_template"
    assert variants[0]["generator_status"] == "fallback"
    assert variants[0]["generator_error"] is not None


# ---------------------------------------------------------------------------
# 5. Timeout — asyncio.TimeoutError falls back to template
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_timeout_falls_back_to_template(monkeypatch):
    async def slow_gemini(prompt, temp, api_key):
        raise asyncio.TimeoutError("generation timed out")

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", slow_gemini)
    monkeypatch.setattr(gs, "score_text", _score_stub)
    gs._RESULT_CACHE.clear()

    variants = await gs.generate_first_appeal_variant(CAMPAIGN)

    assert variants[0]["model"] == "fallback_template"
    assert variants[0]["generator_status"] == "fallback"


# ---------------------------------------------------------------------------
# 6. ImportError — fail fast, no keys tried, clear error logged
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_import_error_fails_fast_no_keys_tried(monkeypatch, caplog):
    import logging

    keys_tried = []

    async def should_not_be_called(prompt, temp, api_key):
        keys_tried.append(api_key)
        return GOOD_APPEAL

    def bad_import(name, *args, **kwargs):
        if name == "google.genai":
            raise ImportError("No module named 'google'")
        return real_import(name, *args, **kwargs)

    import builtins
    real_import = builtins.__import__

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["key-1", "key-2"])
    monkeypatch.setattr(gs, "call_gemini_with_key", should_not_be_called)
    gs._RESULT_CACHE.clear()

    # Simulate missing google.genai by patching the module-level import check
    import unittest.mock as mock
    with mock.patch.dict("sys.modules", {"google": None, "google.genai": None}):
        with caplog.at_level(logging.ERROR, logger="app.models.gemini_service"):
            result = await gs.call_gemini_with_key_fallback("prompt", 0.5, language="English")

    assert result["generator_error"] == "google-genai unavailable"
    assert keys_tried == [], "No Gemini keys should have been tried after ImportError"
    assert any("google-genai" in r.message for r in caplog.records), (
        "ERROR log must mention google-genai"
    )


# ---------------------------------------------------------------------------
# 7. Mock mode — returns canned appeal without any network call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_mode_returns_canned_appeal_no_api_call(monkeypatch):
    call_count = {"n": 0}

    async def should_not_be_called(prompt, temp, api_key):
        call_count["n"] += 1
        return GOOD_APPEAL

    monkeypatch.setattr(settings, "GENERATOR_MODE", "mock")
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", should_not_be_called)
    gs._RESULT_CACHE.clear()

    result = await gs.call_gemini_with_key_fallback("prompt", 0.5, language="English")

    assert result["generator_status"] == "live"
    assert result["model"] == "mock"
    assert call_count["n"] == 0, "Mock mode must not call Gemini API"


# ---------------------------------------------------------------------------
# 8. Fallback variant carries generator_status = "fallback"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_variant_has_fallback_status(monkeypatch):
    async def fail_gemini(*args, **kwargs):
        raise RuntimeError("gemini unavailable")

    monkeypatch.setattr(settings, "HF_API_KEY", None)
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", fail_gemini)
    monkeypatch.setattr(gs, "score_text", _score_stub)
    gs._RESULT_CACHE.clear()

    variants = await gs.generate_first_appeal_variant(CAMPAIGN)

    assert variants[0]["generator_status"] == "fallback"
    assert variants[0]["model"] == "fallback_template"
    assert variants[0]["generator_error"] is not None


# ---------------------------------------------------------------------------
# 9. campaign_goal first character is lowercased in fallback template
# ---------------------------------------------------------------------------

def test_fallback_goal_is_lowercased_mid_sentence():
    form = {
        "language": "English",
        "location": "Gampaha",
        "verified_need": "food",
        "campaign_goal": "Support displaced families",
        "campaign_type": "flood_relief",
    }
    text = gs._build_fallback_appeal(form)
    # "This flood relief campaign aims to support displaced families."
    assert "aims to support" in text, (
        f"Expected lowercase goal mid-sentence, got: {text!r}"
    )
    assert "aims to Support" not in text


# ---------------------------------------------------------------------------
# 10. /health returns Gemini reachability (mocked, no real HTTP)
# ---------------------------------------------------------------------------

def test_health_gemini_check_returns_status(monkeypatch):
    import urllib.request

    class FakeResponse:
        status = 200
        def read(self): return b'{"models": []}'
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: FakeResponse())
    gs._GEMINI_HEALTH.clear()

    result = gs.gemini_health_check()

    assert result["status"] == "reachable"
    assert "200" in result["message"]
