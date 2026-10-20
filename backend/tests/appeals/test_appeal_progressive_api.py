"""Progressive appeal generation contracts; external services are mocked."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.models import gemini_service as gs
from app.models import main
from app.models.schemas import AppealVariant, GenerateNextAppealVariantRequest
from app.services import mongo_service


CAMPAIGN = {
    "language": "English", "campaign_type": "Flood Relief",
    "location": "Nawalapitiya", "verified_need": "water and tents for 20 people",
    "campaign_goal": "provide water and shelter",
}
TEXT = "Families need water and tents. Please donate today."
SCORE = {
    "quality_label": "medium", "quality_score": 3.0,
    "confidence": 0.6, "confidence_normalised": 0.6,
    "confidence_display": "60%", "predicted_class": "medium",
    "class_probs": {"low": 0.2, "medium": 0.6, "high": 0.2},
}


@pytest.fixture(autouse=True)
def services(monkeypatch):
    from app.services import appeal_budget
    monkeypatch.setattr(appeal_budget, "SESSIONS", {})
    monkeypatch.setattr(appeal_budget, "DAILY", {})
    monkeypatch.setattr(gs, "call_gemini_with_key", AsyncMock(return_value=TEXT))
    monkeypatch.setattr(gs, "_gemini_api_keys", lambda: ["offline"])
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda _: False)
    generate = AsyncMock(return_value={
        "model": "mock-model", "appeal_text": TEXT,
        "generator_status": "live", "generator_error": None,
    })
    monkeypatch.setattr(gs, "call_gemini_with_key_fallback", generate)
    monkeypatch.setattr(gs, "score_text", lambda *a, **kw: dict(SCORE))
    monkeypatch.setattr(mongo_service, "log_appeal_generation", AsyncMock())
    monkeypatch.setattr(mongo_service, "log_appeal_analysis", AsyncMock())
    return generate


@pytest.fixture
def client():
    # No lifespan: never initialize production databases or model downloads.
    client = TestClient(main.app)
    yield client
    client.close()


@pytest.mark.parametrize("style_index", [1, 2])
def test_next_returns_one_scored_style(client, services, style_index):
    response = client.post("/api/generate-appeal-variants/next",
                           json={**CAMPAIGN, "style_index": style_index})
    assert response.status_code == 200
    variants = response.json()["variants"]
    assert len(variants) == 1
    variant = variants[0]
    assert variant["style"] == gs.VARIANT_STYLES[style_index]["style_name"]
    assert variant["quality_score"] == 3.0
    assert variant["class_probs"] == SCORE["class_probs"]
    assert variant["generator_status"] == "live"
    assert isinstance(variant["generation_ms"], int)
    assert variant["generation_ms"] >= 0
    assert services.await_args.kwargs["key_offset"] == style_index * 3
    assert "style_index" not in services.await_args.args[0]


@pytest.mark.parametrize("style_index", [0, 3, -1, "1", 1.5, True, None])
def test_next_rejects_invalid_style_before_generation(client, services, style_index):
    response = client.post("/api/generate-appeal-variants/next",
                           json={**CAMPAIGN, "style_index": style_index})
    assert response.status_code == 422
    services.assert_not_awaited()


def test_next_requires_style(client, services):
    assert client.post("/api/generate-appeal-variants/next", json=CAMPAIGN).status_code == 422
    services.assert_not_awaited()


@pytest.mark.parametrize("style_index", [1, 2])
def test_next_total_failure_is_503_without_template(client, services, style_index):
    services.return_value = {"generator_error": "503 overloaded after 1 retries"}
    response = client.post("/api/generate-appeal-variants/next",
                           json={**CAMPAIGN, "style_index": style_index})
    assert response.status_code == 503
    assert "variants" not in response.json()
    assert response.json()["detail"] == "503 overloaded after 1 retries"


@pytest.mark.parametrize("style_index", [1, 2])
def test_next_deadline_is_504_without_template(client, services, monkeypatch, style_index):
    async def pending(*a, **kw):
        await asyncio.Event().wait()
    services.side_effect = pending
    monkeypatch.setattr(gs, "VARIANT_TIMEOUT_SECONDS", 0.01)
    response = client.post("/api/generate-appeal-variants/next",
                           json={**CAMPAIGN, "style_index": style_index})
    assert response.status_code == 504
    assert "variants" not in response.json()
    assert "generation ceiling" in response.json()["detail"]


@pytest.mark.parametrize("timeout", [False, True])
def test_first_failure_remains_200_template(client, services, monkeypatch, timeout):
    # This endpoint now uses the budgeted raw provider, not the legacy wrapper.
    error = asyncio.TimeoutError() if timeout else RuntimeError("403 unavailable")
    monkeypatch.setattr(gs, "call_gemini_with_key", AsyncMock(side_effect=error))
    response = client.post("/api/generate-appeal-variants", json=CAMPAIGN)
    assert response.status_code == 200
    variant = response.json()["variants"][0]
    assert variant["generator_status"] == "fallback"
    assert variant["model"] == "fallback_template"
    assert variant["appeal_text"]
    assert variant["generator_error"]
    assert isinstance(variant["generation_ms"], int)


def test_existing_routes_keep_envelopes(client, services):
    # Approved: remaining styles now share one provider JSON response, not two calls.
    services.side_effect = [
        {"model": "mock", "appeal_text": text}
        for text in [TEXT, TEXT + " Together.", TEXT + " Help now."]
    ]
    async def provider(prompt, temp, api_key, **kwargs):
        if 'Return ONLY JSON:' in prompt:
            return __import__('json').dumps({'appeals': [
                {'style':'community','appeal_text':TEXT+' Together.'},
                {'style':'urgent','appeal_text':TEXT+' Help now.'}]})
        return TEXT
    from app.models import appeal_guidance_service as guidance
    from app.services import appeal_budget
    appeal_budget.SESSIONS.clear()
    # Patch the single-request provider boundary while preserving the endpoint assertions.
    services.side_effect = None
    from unittest.mock import patch
    with patch.object(gs, 'call_gemini_with_key', provider), \
         patch.object(gs, '_gemini_api_keys', return_value=['offline']), \
         patch('app.services.credit_monitor.is_exhausted', return_value=False), \
         patch.object(guidance, 'batch_score', side_effect=lambda texts, language: [{**SCORE, 'final_label':'medium'} for _ in texts]), \
         patch.object(guidance, 'guidance_many', side_effect=lambda texts, *args: [{'suggestions_ms':0, 'length_warning':None, 'word_count':len(text.split())} for text in texts]):
        first = client.post("/api/generate-appeal-variants", json=CAMPAIGN)
        remaining = client.post("/api/generate-appeal-variants/remaining", json=CAMPAIGN)
    assert first.status_code == remaining.status_code == 200
    assert len(first.json()["variants"]) == 1
    assert len(remaining.json()["variants"]) == 2
    assert all(v["generator_status"] != "fallback" for v in remaining.json()["variants"])


def test_remaining_failure_preserves_empty_list(client, services, monkeypatch):
    # Approved: retain the empty list while exposing partial delivery explicitly.
    from app.services import appeal_budget
    appeal_budget.SESSIONS.clear()  # Isolate failure from the preceding successful cached flow.
    monkeypatch.setattr(gs, 'call_gemini_with_key', AsyncMock(side_effect=RuntimeError('403 unavailable')))
    monkeypatch.setattr(gs, '_gemini_api_keys', lambda: ['offline'])
    monkeypatch.setattr('app.services.credit_monitor.is_exhausted', lambda _: False)
    services.return_value = {}
    response = client.post("/api/generate-appeal-variants/remaining", json=CAMPAIGN)
    assert response.status_code == 200
    assert response.json()["variants"] == []
    assert response.json()["partial"] is True


def test_generation_ms_schema_default():
    variant = AppealVariant(model="mock", temperature=0.5, appeal_text=TEXT,
                            quality_label="medium", final_label="medium", quality_score=3,
                            confidence=0.6, confidence_normalised=0.6, confidence_display="60%")
    assert variant.generation_ms == 0
    assert GenerateNextAppealVariantRequest(**CAMPAIGN, style_index=1).style_index == 1


@pytest.mark.asyncio
async def test_ceiling_cancels_generation_and_stops_attempts(services, monkeypatch):
    cancelled = asyncio.Event()
    async def pending(*a, **kw):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
    services.side_effect = pending
    monkeypatch.setattr(gs, "VARIANT_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(gs.AppealVariantGenerationError) as exc:
        await gs.generate_appeal_variant(CAMPAIGN, 1)
    assert exc.value.status_code == 504
    assert cancelled.is_set()
    assert services.await_count == 1


@pytest.mark.asyncio
async def test_default_ceiling_is_30_seconds(services, monkeypatch):
    real_wait_for = asyncio.wait_for
    timeouts = []
    async def observed(awaitable, timeout):
        timeouts.append(timeout)
        return await real_wait_for(awaitable, timeout)
    monkeypatch.setattr(gs.asyncio, "wait_for", observed)
    await gs.generate_appeal_variant(CAMPAIGN, 1)
    assert timeouts == [30.0]


@pytest.mark.asyncio
async def test_mongo_logging_runs_off_response_path_and_catches_failure(caplog):
    started, release = asyncio.Event(), asyncio.Event()
    async def delayed_log(*a, **kw):
        started.set()
        await release.wait()
        raise RuntimeError("private diagnostic text")
    main._schedule_appeal_log(delayed_log, CAMPAIGN, [])
    await started.wait()
    tasks = list(main._APPEAL_LOG_TASKS)
    assert tasks and not tasks[0].done()
    release.set()
    await asyncio.gather(*tasks)
    await asyncio.sleep(0)
    assert not main._APPEAL_LOG_TASKS
    assert "MongoDB logging failed (non-fatal): RuntimeError" in caplog.text
    assert "private diagnostic text" not in caplog.text


@pytest.mark.asyncio
async def test_first_route_does_not_wait_for_mongo(services, monkeypatch):
    started, release = asyncio.Event(), asyncio.Event()
    async def delayed_log(*a, **kw):
        started.set()
        await release.wait()
    monkeypatch.setattr(mongo_service, "log_appeal_generation", delayed_log)
    request = main.GenerateAppealRequest(**CAMPAIGN)
    response = await asyncio.wait_for(main.generate_appeal_variants_endpoint(request), 1)
    assert len(response.variants) == 1
    await started.wait()
    tasks = list(main._APPEAL_LOG_TASKS)
    release.set()
    await asyncio.gather(*tasks)



def test_huggingface_uses_ten_second_timeout(monkeypatch):
    import huggingface_hub

    options = {}
    def fake_client(**kwargs):
        options.update(kwargs)
        return SimpleNamespace(chat_completion=lambda **kw: SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=TEXT))]))
    monkeypatch.setattr(huggingface_hub, "InferenceClient", fake_client)
    assert gs._call_hf_llama_sync_with_temp("mock prompt", 0.3) == TEXT
    assert options["timeout"] == 10.0


@pytest.mark.asyncio
async def test_ceiling_includes_scoring(services, monkeypatch):
    async def pending_scoring(*a, **kw):
        await asyncio.Event().wait()
    monkeypatch.setattr(gs.asyncio, "to_thread", pending_scoring)
    monkeypatch.setattr(gs, "VARIANT_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(gs.AppealVariantGenerationError) as exc:
        await gs.generate_appeal_variant(CAMPAIGN, 2)
    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_generation_ms_includes_scoring(services, monkeypatch):
    times = iter([100.0, 101.25])
    monkeypatch.setattr(gs, "time", SimpleNamespace(monotonic=lambda: next(times)))
    variant = await gs.generate_appeal_variant(CAMPAIGN, 1)
    assert variant["generation_ms"] == 1250


@pytest.mark.asyncio
async def test_unexpected_provider_exception_is_sanitized(services):
    services.side_effect = RuntimeError("private prompt and credential text")
    with pytest.raises(gs.AppealVariantGenerationError) as exc:
        await gs.generate_appeal_variant(CAMPAIGN, 1)
    assert str(exc.value) == "Variant 2 generation failed (RuntimeError)"
