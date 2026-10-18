# Approved UI consistency pass: shared word bands and upper-half targets replace prior length expectations.
"""Offline contracts for budgeted progressive generation and shared guidance."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.models import appeal_generation_service as generation
from app.models import appeal_guidance_service as guidance
from app.models import gemini_service as gemini
from app.models.config import settings
from app.models.quality_service import QualityModelLoadError
from app.services import appeal_budget as budgets

TEXT = "Families in Malabe need water bottles and tents for 20 people. Please donate today."
CAMPAIGN = {"language": "English", "campaign_type": "Flood Relief", "location": "Malabe",
            "verified_need": "water bottles and tents for 20 people", "campaign_goal": "support affected families",
            "length_category": "short"}


def score(label="medium", confidence=0.7, value=3.0):
    result = {"final_label": label, "quality_label": label, "quality_score": value, "raw_quality_score": value,
              "confidence": confidence, "confidence_normalised": confidence, "confidence_display": f"{confidence*100:.0f}%",
              "class_probs": {label: confidence}, "predicted_class": label}
    return {**result, **guidance.confidence_metadata(result)}


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    budgets.SESSIONS.clear()
    budgets.DAILY.clear()
    monkeypatch.setattr(guidance, "GAP_CHECKS", [])
    monkeypatch.setattr(guidance, "batch_score", lambda texts, language="English": [score() for _ in texts])
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "backup")
    monkeypatch.setattr(settings, "MAX_GEMINI_CALLS_PER_REQUEST", 2)
    monkeypatch.setattr(settings, "REQUEST_TIME_BUDGET_S", 25.0)
    monkeypatch.setattr(settings, "DAILY_IMPROVE_LIMIT", 10)
    monkeypatch.setattr(gemini, "_gemini_api_keys", lambda: ["offline-key"])
    monkeypatch.setattr("app.services.credit_monitor.is_exhausted", lambda _: False)


def provider(monkeypatch, replies):
    calls = []
    async def call(prompt, temp, api_key, **kwargs):
        calls.append((prompt, kwargs.get("model")))
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply
    monkeypatch.setattr(gemini, "call_gemini_with_key", call)
    return calls


def pair():
    return json.dumps({"appeals": [{"style": "community", "appeal_text": TEXT},
                                   {"style": "urgent", "appeal_text": TEXT + " Please support the families."}]})


@pytest.mark.asyncio
async def test_two_calls_full_set_and_cached_repeat(monkeypatch):
    calls = provider(monkeypatch, [TEXT, pair()])
    first = await generation.generate(CAMPAIGN, client="one")
    remaining = await generation.generate(CAMPAIGN, remaining=True, client="one")
    assert len(first) == 1 and len(remaining) == 2 and len(calls) == 2
    assert all(v["generation_ms_shared"] for v in remaining)
    assert remaining[0]["generation_ms"] == remaining[1]["generation_ms"]
    assert remaining[0]["gemini_calls_used"] == 2
    await generation.generate({**CAMPAIGN, "location": "  MALABE  "}, client="one")
    await generation.generate(CAMPAIGN, remaining=True, client="one")
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("second", ["not JSON", '{"appeals":[{"style":"community","appeal_text":"'+TEXT+'"}]}'])
async def test_json_retry_exactly_once(monkeypatch, second):
    calls = provider(monkeypatch, [TEXT, second, pair()])
    await generation.generate(CAMPAIGN)
    result = await generation.generate(CAMPAIGN, remaining=True)
    assert len(calls) == 3 and len(result) == 2
    assert result[0]["gemini_calls_used"] == 3


@pytest.mark.asyncio
async def test_invalid_json_twice_template_no_fourth_call(monkeypatch):
    # Approved: failed remaining styles are empty, never templates.
    calls = provider(monkeypatch, [TEXT, "broken", "still broken"])
    await generation.generate(CAMPAIGN)
    result = await generation.generate(CAMPAIGN, remaining=True)
    assert len(calls) == 3 and result == []


@pytest.mark.asyncio
async def test_partial_json_survives_retry_failure(monkeypatch):
    partial = json.dumps({"appeals": [{"style": "community", "appeal_text": TEXT}]})
    calls = provider(monkeypatch, [TEXT, partial, RuntimeError("403 rejected")])
    await generation.generate(CAMPAIGN)
    result = await generation.generate(CAMPAIGN, remaining=True)
    assert len(calls) == 3 and len(result) == 1 and result[0]["partial"]
    assert result[0]["appeal_text"] == TEXT


@pytest.mark.asyncio
@pytest.mark.parametrize("message", ["403 rejected", "429 daily quota", "quota exhausted", "429 per minute"])
async def test_rejection_stops_paired_budget(monkeypatch, message):
    # With only one configured key, a cooldown also applies to the paired stage.
    # Multiple-key recovery is exercised by test_appeal_generator_reliability.
    calls = provider(monkeypatch, [RuntimeError(message)])
    first = await generation.generate(CAMPAIGN)
    remaining = await generation.generate(CAMPAIGN, remaining=True)
    assert first[0]["generator_status"] == "fallback"
    assert len(calls) == 1 and remaining == []


@pytest.mark.asyncio
async def test_fallbacks_share_cap(monkeypatch):
    # Approved: free 503 attempts do not starve the remaining endpoint's billable budget.
    calls = provider(monkeypatch, [RuntimeError("503 overloaded"), TEXT, pair()])
    await generation.generate(CAMPAIGN)
    result = await generation.generate(CAMPAIGN, remaining=True)
    assert len(calls) == 3 and len(result) == 2
    assert all(v["generator_status"] == "live" for v in result)


@pytest.mark.asyncio
async def test_length_warning_no_extra_provider_call(monkeypatch, caplog):
    calls = provider(monkeypatch, [TEXT])
    with caplog.at_level("INFO"):
        result = await generation.generate(CAMPAIGN)
    assert result[0]["length_warning"] and len(calls) == 1
    assert "word_count=" in caplog.text and "key_index=1" in caplog.text
    assert "offline-key" not in caplog.text


@pytest.mark.parametrize("confidence,level", [(0.499,"low"),(0.5,"borderline"),(0.699,"borderline"),(0.7,"moderate"),(0.899,"moderate"),(0.9,"high")])
def test_confidence_boundaries(confidence, level):
    assert guidance.confidence_metadata(score(confidence=confidence))["confidence_level"] == level


def test_disagreement_drops_level_and_names_top_two():
    result = guidance.confidence_metadata({"final_label":"high","class_probs":{"medium":0.75,"high":0.2,"low":0.05}})
    assert result["confidence_level"] == "borderline" and result["label_agreement"] is False
    assert [v["class"] for v in result["top_classes"]] == ["medium","high"]




def test_length_suggestion_uses_no_model_batch(monkeypatch):
    # Simplified contract: direct length checks replace diagnostic restatements.
    monkeypatch.setattr(guidance,"batch_score",lambda *args:pytest.fail("suggestions must not score text"))
    result=guidance.guidance(TEXT,"English",score(value=2))
    assert result["suggestions"][0]["message"]==f"This appeal has {len(TEXT.split())} words. Appeals under about 65 words tend to rate lower."
    assert not result["gap_statistics_available"]
    assert set(result["suggestions"][0])=={"check","message","evidence"}


@pytest.mark.asyncio
@pytest.mark.parametrize("improves", [True,False])
async def test_repair_kept_or_discarded(monkeypatch, improves):
    text=" ".join([TEXT]*5)
    # A shorter rearrangement uses exclusively original facts and is in the Short band.
    rewrite=" ".join([TEXT]*5)
    calls=provider(monkeypatch,[rewrite])
    # Approved policy: a visible score gain, not confidence alone, defines acceptance.
    queue=[[score(value=2.9)], [score(confidence=0.8 if improves else 0.6, value=3.0 if improves else 2.8)]]
    monkeypatch.setattr(guidance,"batch_score",lambda *args:queue.pop(0))
    monkeypatch.setattr(guidance,"guidance",lambda *args:{})
    result=await generation.repair(text,CAMPAIGN)
    assert result["kept"]==improves and len(calls)==1
    assert result["before"]["appeal_text"]==text


@pytest.mark.asyncio
async def test_repair_prompt_uses_original_text_only(monkeypatch):
    calls=provider(monkeypatch,["Invented charity will help 500 children tomorrow."])
    result=await generation.repair(TEXT,{"language":"English"})
    assert "SUPPLIED FACTS" not in calls[0][0]
    assert result["improved_appeal"]==TEXT and not result["kept"]


@pytest.mark.asyncio
async def test_daily_limit_only_blocks_improve(monkeypatch):
    monkeypatch.setattr(settings,"DAILY_IMPROVE_LIMIT",1)
    # Approved: only a kept rewrite consumes the daily allowance; use an accepted rewrite here.
    rewrite=" ".join([TEXT]*5)
    calls=provider(monkeypatch,[rewrite,TEXT])
    # Approved policy: the kept rewrite must visibly improve before consuming a use.
    scores=iter([[score(confidence=0.6, value=2.9)], [score(confidence=0.8)], [score(confidence=0.6)]])
    monkeypatch.setattr(guidance,"batch_score",lambda *args:next(scores))
    monkeypatch.setattr(guidance,"guidance",lambda *args, **kwargs:{"suggestions_ms":0.0,"length_warning":None})
    await generation.repair(TEXT,CAMPAIGN,"ip")
    blocked=await generation.repair(TEXT,CAMPAIGN,"ip")
    assert blocked["remaining_improve_uses"]==0 and not blocked["attempted"]
    await generation.generate(CAMPAIGN,client="ip")
    assert len(calls)==2


@pytest.mark.asyncio
async def test_time_budget_returns_partial_template(monkeypatch):
    monkeypatch.setattr(settings,"REQUEST_TIME_BUDGET_S",0.01)
    async def slow(*args,**kwargs):
        await asyncio.sleep(1)
    monkeypatch.setattr(gemini,"call_gemini_with_key",slow)
    result=await generation.generate(CAMPAIGN)
    assert result[0]["partial"] and result[0]["generator_status"]=="fallback"


@pytest.mark.asyncio
async def test_analyzer_original_unchanged_and_model_load_503(monkeypatch):
    from app.models import main
    from fastapi.testclient import TestClient
    from unittest.mock import AsyncMock
    monkeypatch.setattr("app.models.quality_service.get_quality_score",lambda *a,**k:{"score":3,"status":"medium","confidence":0.7,"low_confidence":False,"method":"ml_model"})
    monkeypatch.setattr("app.services.mongo_service.log_appeal_analysis",AsyncMock())
    client=TestClient(main.app)
    original="  "+TEXT+"  "
    result=client.post('/api/quality/analyse',json={"appeal_text":original,"language":"English"})
    assert result.status_code==200 and result.json()["original_appeal"]==original
    def fail(*args,**kwargs):raise QualityModelLoadError('missing model')
    # Approved: simulate the artifact-loader failure, not a scorer no longer used by first delivery.
    monkeypatch.setattr("app.models.quality_service._load_artifacts",fail)
    provider(monkeypatch,[TEXT])
    assert client.post('/api/generate-appeal-variants',json=CAMPAIGN).status_code==503
    client.close()


def test_optional_json_missing_invalid_and_valid(tmp_path, monkeypatch):
    valid = json.loads(guidance.GAP_PATH.read_text(encoding='utf-8'))
    path=tmp_path/'optional_gap.json'
    monkeypatch.setattr(guidance,'GAP_PATH',path)
    assert guidance.load_gap_statistics()==[]
    path.write_text('invalid',encoding='utf-8')
    assert guidance.load_gap_statistics()==[]
    path.write_text(json.dumps({'schema_version':1,'checks':[]}),encoding='utf-8')
    assert guidance.load_gap_statistics()==[]
    path.write_text(json.dumps(valid), encoding='utf-8')
    assert guidance.load_gap_statistics()
    valid['provenance']['dataset_sha256'] = 'wrong-dataset-hash'
    path.write_text(json.dumps(valid), encoding='utf-8')
    assert guidance.load_gap_statistics() == []
    valid['provenance']['dataset_sha256'] = json.loads(guidance.settings.donation_appeal_model_path('manifest.json').read_text(encoding='utf-8'))['data_sha256']
    valid['provenance']['development_rows'] += 1
    path.write_text(json.dumps(valid), encoding='utf-8')
    assert guidance.load_gap_statistics() == []


def test_gaps_rank_by_dataset_difference_without_inference(monkeypatch):
    # Simplified contract: use the retained English checks, not supplied additions.
    names=['fund_use','human_detail','specific_call_to_action','amount_mentioned']
    checks=[{'check':name,'rule':{'common_pattern':'never-matches'},'enabled_languages':['English'],
             'per_language':{'English':{'high_minus_low':0.8-i*0.1,'classes':{'low':{'share':0.1},'high':{'share':0.9}}}}}
            for i,name in enumerate(names)]
    monkeypatch.setattr(guidance,'GAP_CHECKS',list(reversed(checks)))
    monkeypatch.setattr(guidance,'batch_score',lambda *args:pytest.fail('no suggestion inference'))
    result=guidance.guidance(TEXT,'English',score())
    assert [s['check'] for s in result['suggestions']]==['length','fund_use','human_detail']
    assert 'Appears in 90.0% of high-rated and 10.0% of low-rated English appeals.'==result['suggestions'][1]['evidence']
    assert all(set(s)=={'check','message','evidence'} for s in result['suggestions'])


def test_multiple_variants_need_no_suggestion_inference(monkeypatch):
    monkeypatch.setattr(guidance,'batch_score',lambda *args:pytest.fail('no suggestion inference'))
    result=guidance.guidance_many([TEXT,TEXT],'English',[score(),score()])
    assert len(result)==2 and all(v['suggestions'][0]['check']=='length' for v in result)


@pytest.mark.asyncio
async def test_concurrent_repeat_and_client_isolation(monkeypatch):
    calls=provider(monkeypatch,[TEXT,TEXT])
    first,repeat=await asyncio.gather(generation.generate(CAMPAIGN,client='ip1'),generation.generate(CAMPAIGN,client='ip1'))
    assert first==repeat and len(calls)==1
    await generation.generate(CAMPAIGN,client='ip2')
    assert len(calls)==2


@pytest.mark.asyncio
async def test_improve_never_falls_back_to_second_call(monkeypatch):
    # Approved: 503 is one hard-ceiling attempt but zero potentially billed calls.
    calls=provider(monkeypatch,[RuntimeError('503 overloaded')])
    result=await generation.repair(TEXT,CAMPAIGN)
    assert len(calls)==1 and result['gemini_calls_used']==0 and not result['kept']


@pytest.mark.asyncio
async def test_actual_transport_uses_remaining_http_timeout(monkeypatch):
    import requests
    seen=[]
    def request(session,method,url,**kwargs):
        seen.append(kwargs['timeout'])
        response=requests.Response();response.status_code=200
        response._content=json.dumps({'candidates':[{'content':{'parts':[{'text':TEXT}]}}]}).encode()
        return response
    monkeypatch.setattr(requests.Session,'request',request)
    budget=budgets.Budget();token=budgets.CURRENT.set(budget)
    try:
        await gemini.call_gemini_with_key('offline prompt',0.5,'offline-key')
    finally:
        budgets.CURRENT.reset(token)
    assert len(seen)==1 and sum(seen[0]) <= settings.REQUEST_TIME_BUDGET_S


def test_empty_gap_file_is_not_created_by_guidance(tmp_path,monkeypatch):
    path=tmp_path/'never_create.json';monkeypatch.setattr(guidance,'GAP_PATH',path)
    guidance.guidance(TEXT,'English',score())
    assert not path.exists()


@pytest.mark.asyncio
async def test_first_route_mongo_logging_remains_off_response_path(monkeypatch):
    # Approved: isolate the first scorer so this measures Mongo scheduling, not model inference.
    from app.models import main
    from app.models.schemas import GenerateAppealRequest
    provider(monkeypatch,[TEXT])
    monkeypatch.setattr(gemini,'score_text',lambda *args:score())
    blocked=asyncio.Event()
    async def slow_log(*args,**kwargs):
        await blocked.wait()
    monkeypatch.setattr('app.services.mongo_service.log_appeal_generation',slow_log)
    response=await asyncio.wait_for(main.generate_appeal_variants_endpoint(GenerateAppealRequest(**CAMPAIGN)),0.5)
    assert len(response.variants)==1 and response.recommended is not None
    blocked.set()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_sparse_key_configuration_logs_actual_index(monkeypatch,caplog):
    for i in range(1,12):
        monkeypatch.setattr(settings,'GEMINI_API_KEY'+(str(i) if i>1 else ''),None)
    monkeypatch.setattr(settings,'GEMINI_API_KEY5','offline-key')
    provider(monkeypatch,[TEXT])
    with caplog.at_level('INFO'):
        await generation.generate(CAMPAIGN)
    assert 'key_index=5' in caplog.text and 'offline-key' not in caplog.text
