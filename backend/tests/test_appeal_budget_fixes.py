# Approved UI consistency pass: shared word bands and upper-half targets replace prior length expectations.
"""Offline regression coverage for the October 17 budget/contract corrections."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models import appeal_generation_service as service
from app.models import appeal_guidance_service as guide
from app.models import gemini_service as gs
from app.models.config import settings
from app.services import appeal_budget as budgets

TEXT = "Affected families in Malabe need water bottles and tents for 20 people. Please donate today."
PAYLOAD = {"language":"English","campaign_type":"Flood Relief","location":"Malabe",
           "verified_need":"water bottles and tents for 20 people","campaign_goal":"support affected families","length_category":"short"}


def score(*args):
    result = {"quality_label":"medium","final_label":"medium","quality_score":3.0,
            "raw_quality_score":3.0,"confidence":0.7,"confidence_normalised":0.7,"confidence_display":"70%",
            "class_probs":{"medium":0.7,"high":0.2,"low":0.1},"predicted_class":"medium"}
    return {**result, **guide.confidence_metadata(result)}


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    budgets.SESSIONS.clear();budgets.DAILY.clear()
    monkeypatch.setattr(settings,"GEMINI_MODEL","main")
    monkeypatch.setattr(settings,"GEMINI_FALLBACK_MODELS","fallback,lite")
    monkeypatch.setattr(settings,"MAX_GEMINI_CALLS_PER_REQUEST",2)
    monkeypatch.setattr(settings,"MAX_GEMINI_PROVIDER_ATTEMPTS_PER_FLOW",6)
    monkeypatch.setattr(settings,"REQUEST_TIME_BUDGET_S",25)
    monkeypatch.setattr(gs,"_gemini_api_keys",lambda:["offline"])
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted",lambda _:False)
    monkeypatch.setattr(gs,"score_text",score)
    monkeypatch.setattr(guide,"batch_score",lambda texts,language:[score() for _ in texts])
    monkeypatch.setattr(guide,"GAP_CHECKS",[])
    monkeypatch.setattr(service.asyncio,"sleep",AsyncMock())
    yield
    budgets.SESSIONS.clear();budgets.DAILY.clear()


def pair():
    return json.dumps({"appeals":[{"style":"community","appeal_text":TEXT},
                                   {"style":"urgent","appeal_text":TEXT+" Support families."}]})


def provider(monkeypatch,replies):
    calls=[]
    async def send(*args,**kwargs):
        calls.append(kwargs.get("model","main"))
        response=replies.pop(0)
        if isinstance(response,Exception):raise response
        return response
    monkeypatch.setattr(gs,"call_gemini_with_key",send)
    return calls


@pytest.mark.asyncio
async def test_503_fallback_leaves_remaining_full_billable_budget(monkeypatch):
    calls=provider(monkeypatch,[RuntimeError("503 overloaded"),RuntimeError("503 overloaded"),TEXT,pair()])
    await service.generate(PAYLOAD)
    state=budgets.session(PAYLOAD)
    assert state["budget"].calls==1 and state["remaining_budget"].calls==0
    remaining=await service.generate(PAYLOAD,remaining=True)
    assert len(remaining)==2 and all(v["generator_status"]=="live" for v in remaining)
    assert state["remaining_budget"].calls==1 and len(calls)==4


@pytest.mark.asyncio
async def test_full_flow_never_exceeds_six_attempts(monkeypatch):
    calls=provider(monkeypatch,[RuntimeError("503 overloaded") for _ in range(10)])
    first=await service.generate(PAYLOAD)
    remaining=await service.generate(PAYLOAD,remaining=True)
    state=budgets.session(PAYLOAD)
    assert first[0]["generator_status"]=="fallback" and remaining==[]
    assert len(calls)==state["flow"].attempts==6
    assert state["budget"].calls==state["remaining_budget"].calls==0


@pytest.mark.asyncio
async def test_403_stops_both_endpoints(monkeypatch):
    calls=provider(monkeypatch,[RuntimeError("403 forbidden")])
    await service.generate(PAYLOAD)
    assert await service.generate(PAYLOAD,remaining=True)==[]
    assert len(calls)==1 and budgets.session(PAYLOAD)["flow"].stopped


@pytest.mark.asyncio
async def test_429_retry_hint_backoff_is_billable_and_retried_once(monkeypatch):
    error=RuntimeError("429 per minute")
    error.response=SimpleNamespace(headers={"Retry-After":"2"})
    calls=provider(monkeypatch,[error,TEXT,pair()])
    await service.generate(PAYLOAD)
    state=budgets.session(PAYLOAD)
    assert state["budget"].calls==2
    service.asyncio.sleep.assert_awaited_once_with(2.0)
    assert len(await service.generate(PAYLOAD,remaining=True))==2 and len(calls)==3


@pytest.mark.asyncio
async def test_daily_quota_billed_and_stops_everything(monkeypatch):
    calls=provider(monkeypatch,[RuntimeError("429 daily quota exhausted")])
    await service.generate(PAYLOAD)
    assert await service.generate(PAYLOAD,remaining=True)==[]
    assert len(calls)==1 and budgets.session(PAYLOAD)["budget"].calls==1


@pytest.mark.asyncio
async def test_connection_failure_is_free_but_counts_attempt(monkeypatch):
    calls=provider(monkeypatch,[ConnectionError("offline"),TEXT])
    await service.generate(PAYLOAD)
    state=budgets.session(PAYLOAD)
    assert len(calls)==2 and state["budget"].calls==1 and state["flow"].attempts==2


@pytest.mark.asyncio
async def test_failed_remaining_http_empty_and_partial(monkeypatch):
    from fastapi.testclient import TestClient
    from app.models import main
    provider(monkeypatch,[RuntimeError("403 forbidden")])
    response=TestClient(main.app).post('/api/generate-appeal-variants/remaining',json=PAYLOAD)
    assert response.status_code==200
    assert response.json()["variants"]==[] and response.json()["partial"] is True




@pytest.mark.asyncio
async def test_first_response_includes_direct_suggestions_without_extra_model_batch(monkeypatch):
    provider(monkeypatch,[TEXT])
    def must_not_score(*args):raise AssertionError("extra model batch delays first delivery")
    monkeypatch.setattr(guide,"batch_score",must_not_score)
    result=await service.generate(PAYLOAD)
    assert result[0]["quality_score"]==3 and result[0]["suggestions"][0]["check"]=="length"


@pytest.mark.asyncio
async def test_malformed_remaining_one_retry_no_extension_call(monkeypatch):
    calls=provider(monkeypatch,[TEXT,"bad json",pair()])
    await service.generate(PAYLOAD)
    result=await service.generate(PAYLOAD,remaining=True)
    assert len(calls)==3 and len(result)==2
    assert all(v["length_warning"] for v in result)
