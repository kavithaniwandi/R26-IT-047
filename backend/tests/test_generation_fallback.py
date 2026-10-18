from __future__ import annotations

import pytest

from app.models import gemini_service as gs
from app.models.config import settings
import app.services.credit_monitor as cm
from app.services.credit_monitor import _key_state


@pytest.fixture(autouse=True)
def isolate_credit_monitor(tmp_path, monkeypatch):
    """Redirect state file to tmp dir and clear _key_state around each test."""
    monkeypatch.setattr(cm, "STATE_FILE", tmp_path / "credit_monitor_state.json")
    _key_state.clear()
    gs._RESULT_CACHE.clear()
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "")
    yield
    _key_state.clear()


CAMPAIGN = {
    "language": "English",
    "campaign_type": "flood relief",
    "location": "Kaduwela",
    "verified_need": "dry rations and clean water",
    "campaign_goal": "support 50 displaced families",
    "tone": "trustworthy",
    "channel": "website",
    "length_category": "short",
}


def _score_stub(text: str, language: str = "English") -> dict:
    return {
        "quality_label": "high",
        "quality_score": 4.2,
        "confidence": 0.9,
        "confidence_normalised": 0.9,
        "confidence_display": "90%",
    }


@pytest.mark.asyncio
async def test_english_uses_llama_when_gemini_fails(monkeypatch):
    async def fail_gemini(*args, **kwargs):
        raise RuntimeError("gemini unavailable")

    monkeypatch.setattr(settings, "HF_API_KEY", "test-hf-key")
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-gemini-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", fail_gemini)
    monkeypatch.setattr(
        gs,
        "_call_hf_llama_sync_with_temp",
        lambda prompt, temperature: "Families in Kaduwela need dry rations and clean water. Donate today.",
    )

    result = await gs.call_gemini_with_key_fallback("prompt", 0.5, language="English", max_retries=1)

    assert result["model"] == "llama-3.2-3b-instruct"
    assert result["provider"] == "huggingface-featherless"
    assert result["appeal_text"]


@pytest.mark.asyncio
async def test_english_llama_failure_returns_template_label(monkeypatch):
    async def fail_gemini(*args, **kwargs):
        raise RuntimeError("gemini unavailable")

    def fail_llama(*args, **kwargs):
        raise RuntimeError("llama unavailable")

    monkeypatch.setattr(settings, "HF_API_KEY", "test-hf-key")
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-gemini-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", fail_gemini)
    monkeypatch.setattr(gs, "_call_hf_llama_sync_with_temp", fail_llama)
    monkeypatch.setattr(gs, "score_text", _score_stub)

    result = await gs.generate_first_appeal_variant(CAMPAIGN)

    assert result[0]["model"] == "fallback_template"


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["Sinhala", "Tamil"])
async def test_sinhala_and_tamil_skip_llama_and_use_template(monkeypatch, language):
    async def fail_gemini(*args, **kwargs):
        raise RuntimeError("gemini unavailable")

    def fail_if_llama_called(*args, **kwargs):
        raise AssertionError("Llama should be skipped for Sinhala and Tamil")

    monkeypatch.setattr(settings, "HF_API_KEY", "test-hf-key")
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["test-gemini-key"])
    monkeypatch.setattr(gs, "call_gemini_with_key", fail_gemini)
    monkeypatch.setattr(gs, "_call_hf_llama_sync_with_temp", fail_if_llama_called)
    monkeypatch.setattr(gs, "score_text", _score_stub)

    campaign = {**CAMPAIGN, "language": language}
    result = await gs.generate_first_appeal_variant(campaign)

    assert result[0]["model"] == "fallback_template"
