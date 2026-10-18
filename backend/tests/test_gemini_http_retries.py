import json
from itertools import count
from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
import requests
from google import genai

from app.models import gemini_service as gs
from app.services import credit_monitor as cm

TEXT = 'Families in Nawalapitiya need water bottles and tents for 20 people. Donate today.'


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.models.main import app

    test_client = TestClient(app)
    yield test_client
    test_client.close()


@pytest.fixture
def transport(monkeypatch, tmp_path):
    monkeypatch.setattr(cm, 'STATE_FILE', tmp_path / 'credit.json')
    monkeypatch.setattr(cm, '_key_state', {})
    monkeypatch.setattr(gs, '_KEY_STARTS', count())
    gs._RESULT_CACHE.clear()
    monkeypatch.setattr(gs.settings, 'GEMINI_MODEL', 'main-flash')
    monkeypatch.setattr(gs.settings, 'GEMINI_FALLBACK_MODELS', 'backup-flash,backup-lite')
    monkeypatch.setattr(gs.settings, 'GEMINI_MAX_KEYS_PER_REQUEST', 3)
    monkeypatch.setattr(gs.settings, 'GENERATOR_MODE', 'live')
    monkeypatch.setattr(gs.settings, 'HF_API_KEY', None)
    monkeypatch.setattr(gs, '_gemini_api_keys', lambda: ['fake-one', 'fake-two'])
    # Exercise SDK decoding with the HTTP transport mocked below.
    monkeypatch.setattr(gs, '_get_gemini_client', lambda key: genai.Client(api_key=key))
    calls, delays, replies = [], [], []

    def request(session, method, url, **kwargs):
        from app.services.appeal_budget import CURRENT
        if CURRENT.get() is None:
            assert kwargs['timeout'] == (5.0, 15.0)
        else:
            assert 0 < kwargs['timeout'][0] <= 5.0
            assert sum(kwargs['timeout']) <= gs.settings.REQUEST_TIME_BUDGET_S
        model = urlparse(url).path.rsplit('/', 1)[-1].split(':')[0]
        key_index = ['fake-one', 'fake-two'].index(kwargs['headers']['x-goog-api-key']) + 1
        calls.append((model, key_index))
        code, message, *extra = replies.pop(0)
        options = extra[0] if extra else {}
        response = requests.Response()
        response.status_code = code
        response.headers.update(options.get("headers", {}))
        response._content = json.dumps(
            {'candidates': [{'content': {'role': 'model', 'parts': [{'text': TEXT}]}, 'finishReason': 'STOP'}]}
            if code == 200 else {'error': {'code': code, 'message': message, 'status': 'UNAVAILABLE' if code >= 500 else 'RESOURCE_EXHAUSTED', 'details': options.get('details', [])}}
        ).encode()
        return response

    async def sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr(requests.Session, 'request', request)
    monkeypatch.setattr(gs.asyncio, 'sleep', sleep)
    monkeypatch.setattr(gs.random, 'uniform', lambda *args: 0.25)
    yield replies, calls, delays
    gs._RESULT_CACHE.clear()
    cm._key_state.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize('code', [500, 503, 504])
async def test_transient_then_success_same_key(transport, code):
    replies, calls, delays = transport
    replies.extend([(code, 'overloaded'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5, max_retries=1)
    assert calls == [('main-flash', 1)] * 2
    assert delays == ([1.0] if code == 503 else [2.25])
    assert result['generator_status'] == 'live'
    assert result['generator_model'] == 'main-flash'
    assert result['generator_error'] is None
    assert not cm._key_state['gemini_key_1']['exhausted']


@pytest.mark.asyncio
async def test_503_exhausted_then_fallback_model_success(transport):
    replies, calls, delays = transport
    replies.extend([(503, 'overloaded')] * 2 + [(200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5, max_retries=1)
    assert calls == [('main-flash', 1)] * 2 + [('backup-flash', 1)]
    assert delays == [1.0]
    assert result['generator_status'] == 'live'
    assert result['generator_model'] == 'backup-flash'
    assert result['generator_error'] is None


@pytest.mark.asyncio
async def test_429_daily_rotates_key(transport):
    replies, calls, delays = transport
    replies.extend([(429, 'RESOURCE_EXHAUSTED GenerateRequestsPerDay daily quota'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1), ('main-flash', 2)]
    assert delays == []
    assert cm._key_state['gemini_key_1']['exhausted']
    assert result['provider'] == 'gemini_key_2'


@pytest.mark.asyncio
async def test_429_per_minute_rotates_without_exhausting_key(transport):
    replies, calls, delays = transport
    replies.extend([(429, 'RESOURCE_EXHAUSTED GenerateRequestsPerMinute'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5, max_retries=1)
    assert calls == [('main-flash', 1), ('main-flash', 2)]
    assert delays == []
    assert result['provider'] == 'gemini_key_2'
    assert not cm._key_state['gemini_key_1']['exhausted']
    assert result['generator_status'] == 'live'


@pytest.mark.asyncio
async def test_all_models_overloaded_preserves_final_cause(transport):
    replies, calls, delays = transport
    replies.extend([(503, 'overloaded')] * 4)
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1)] * 2 + [('backup-flash', 1), ('backup-lite', 1)]
    assert result['generator_model'] == 'backup-lite'
    assert result['generator_error'] == '503 overloaded after 0 retries'
    assert cm._key_state == {}


@pytest.mark.asyncio
async def test_primary_failure_preserves_one_retry_cause(transport, monkeypatch):
    replies, calls, delays = transport
    monkeypatch.setattr(gs.settings, 'GEMINI_FALLBACK_MODELS', '')
    replies.extend([(503, 'overloaded')] * 2)
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert result['generator_error'] == '503 overloaded after 1 retries'
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_404_uses_fallback_model_without_key_penalty(transport):
    replies, calls, delays = transport
    replies.extend([(404, 'model not found'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1), ('backup-flash', 1)]
    assert not cm._key_state['gemini_key_1']['exhausted']
    assert result['generator_model'] == 'backup-flash'

@pytest.mark.asyncio
async def test_template_variant_preserves_terminal_cause(transport, monkeypatch):
    replies, calls, delays = transport
    monkeypatch.setattr(gs.settings, 'GEMINI_FALLBACK_MODELS', '')
    replies.extend([(503, 'overloaded')] * 2)
    monkeypatch.setattr(gs, 'score_text', lambda *a, **kw: {
        'quality_label': 'medium', 'quality_score': 3.0, 'confidence': 0.5,
        'confidence_normalised': 0.5, 'confidence_display': '50%',
    })
    result = await gs.generate_first_appeal_variant({
        'language': 'English', 'campaign_type': 'Flood Relief',
        'location': 'Nawalapitiya', 'verified_need': 'water and tents for 20 people',
        'campaign_goal': 'provide water and shelter',
    })
    assert result[0]['generator_status'] == 'fallback'
    assert result[0]['generator_model'] == 'main-flash'
    assert result[0]['generator_error'] == '503 overloaded after 1 retries'


@pytest.mark.asyncio
async def test_single_appeal_uses_shared_transient_retries(transport):
    replies, calls, delays = transport
    replies.extend([(503, 'overloaded'), (200, '')])
    result = await gs.asyncio.to_thread(gs.generate_donation_appeal, {
        'language': 'English', 'campaign_type': 'Flood Relief',
        'location': 'Nawalapitiya', 'verified_need': 'water and tents for 20 people',
        'campaign_goal': 'provide water and shelter',
    })
    assert result == TEXT
    assert calls == [('main-flash', 1)] * 2
    assert delays == [1.0]


def test_all_models_failed_returns_http_200_template(transport, client, monkeypatch):
    from app.services import mongo_service

    replies, calls, delays = transport
    replies.extend([(503, 'overloaded')] * 4)
    monkeypatch.setattr(gs, 'score_text', lambda *a, **kw: {
        'quality_label': 'medium', 'quality_score': 3.0, 'confidence': 0.5,
        'confidence_normalised': 0.5, 'confidence_display': '50%',
    })

    async def no_logging(*args, **kwargs):
        pass

    monkeypatch.setattr(mongo_service, 'log_appeal_generation', no_logging)
    response = client.post('/api/generate-appeal-variants', json={
        'language': 'English', 'campaign_type': 'Flood Relief',
        'location': 'Nawalapitiya', 'verified_need': 'water and tents for 20 people',
        'campaign_goal': 'provide water and shelter',
    })
    assert response.status_code == 200
    variant = response.json()['variants'][0]
    assert variant['generator_status'] == 'fallback'
    assert variant['model'] == 'fallback_template'
    assert variant['appeal_text']
    assert variant['generator_model'] == 'backup-lite'
    assert variant['generator_error'] == '503 overloaded after 0 retries'
    assert calls == [('main-flash', 1)] * 2 + [('backup-flash', 1), ('backup-lite', 1)]
    assert delays == [1.0]


@pytest.mark.asyncio
async def test_unsupported_thinking_config_does_not_exhaust_key(transport):
    replies, calls, delays = transport
    replies.extend([(400, 'Invalid thinking configuration for this model'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1), ('backup-flash', 1)]
    assert not cm._key_state['gemini_key_1']['exhausted']
    assert result['generator_status'] == 'live'
    assert result['generator_model'] == 'backup-flash'


@pytest.mark.asyncio
@pytest.mark.parametrize('message', [
    'You exceeded your current quota: GenerateRequestsPerMinute; retry in 30s',
    'quota_exceeded billing RESOURCE_EXHAUSTED',
    'Too many requests; retry in 3s',
])
async def test_generic_429_never_exhausts_and_rotates(transport, message):
    replies, calls, delays = transport
    replies.extend([(429, message), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1), ('main-flash', 2)]
    assert delays == []
    assert not cm._key_state['gemini_key_1']['exhausted']
    assert result['provider'] == 'gemini_key_2'


@pytest.mark.asyncio
@pytest.mark.parametrize('message', [
    'GenerateRequestsPerDayPerProject quota', 'requests per day limit',
    'requests per_day limit', 'day_limit', 'daily quota exhausted',
])
async def test_explicit_daily_quota_exhausts(transport, message):
    replies, calls, delays = transport
    replies.extend([(429, message), (200, '')])
    await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert cm._key_state['gemini_key_1']['exhausted']
    assert calls == [('main-flash', 1), ('main-flash', 2)]
    assert delays == []


@pytest.mark.asyncio
@pytest.mark.parametrize('code', [400, 401, 403])
async def test_auth_rejection_still_exhausts(transport, code):
    replies, calls, delays = transport
    replies.extend([(code, 'key rejected'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert cm._key_state['gemini_key_1']['exhausted']
    assert result['provider'] == 'gemini_key_2'


@pytest.mark.asyncio
@pytest.mark.parametrize('hint', [3.5, 10, 10.01, 30])
@pytest.mark.parametrize('source', ['header', 'details', 'text'])
async def test_503_long_retry_hint_moves_model_without_rotating(transport, hint, source):
    replies, calls, delays = transport
    options = {}
    message = 'overloaded'
    if source == 'header':
        options['headers'] = {'Retry-After': str(hint)}
    elif source == 'details':
        options['details'] = [{'@type': 'type.googleapis.com/google.rpc.RetryInfo',
                               'retryDelay': f'{hint}s'}]
    else:
        message += f'; retry in {hint}s'
    replies.extend([(503, message, options), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1), ('backup-flash', 1)]
    assert delays == []
    assert result['provider'] == 'gemini_key_1'
    assert not cm._key_state['gemini_key_1']['exhausted']


def test_retry_after_http_date_and_malformed_hints(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(gs, 'datetime', Clock)
    exc = SimpleNamespace(response=SimpleNamespace(headers={
        'Retry-After': 'Fri, 16 Oct 2026 12:00:08 GMT'}))
    assert gs._retry_delay_seconds(exc, '') == 8
    for hint in ['invalid', 'NaN', 'inf', '-1']:
        exc.response.headers['Retry-After'] = hint
        assert gs._retry_delay_seconds(exc, '') == 0


@pytest.mark.asyncio
async def test_uncached_requests_rotate_but_cache_hits_do_not(transport):
    replies, calls, delays = transport
    replies.extend([(200, '')] * 3)
    for prompt in ['first', 'first', 'second', 'third']:
        await gs.call_gemini_with_key_fallback(prompt, 0.5)
    assert calls == [('main-flash', 1), ('main-flash', 2), ('main-flash', 1)]


@pytest.mark.asyncio
async def test_rotation_honors_offsets_and_skips_exhausted_keys(transport):
    replies, calls, delays = transport
    replies.append((200, ''))
    result = await gs.call_gemini_with_key_fallback('offset', 0.5, key_offset=1)
    assert result['provider'] == 'gemini_key_2'
    cm.mark_exhausted('gemini_key_1')
    replies.append((200, ''))
    # Next base offset is one; explicit offset one starts at exhausted key one.
    result = await gs.call_gemini_with_key_fallback('skip', 0.5, key_offset=1)
    assert result['provider'] == 'gemini_key_2'


@pytest.mark.asyncio
async def test_failure_logging_never_echoes_provider_text(transport, caplog):
    replies, calls, delays = transport
    secret = 'AIzaDO_NOT_LOG_THIS_KEY'
    prompt = 'DO_NOT_LOG_THIS_PROMPT'
    replies.extend([(429, f'{secret} {prompt} GenerateRequestsPerMinute retry in 60s'), (200, '')])
    await gs.call_gemini_with_key_fallback(prompt, 0.5)
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith('Gemini failure ')]
    assert lines == ['Gemini failure key=1 http_status=429 quota_reason=PerMinute']
    assert secret not in caplog.text
    assert prompt not in caplog.text
    assert len(lines[0].split('quota_reason=')[1]) <= 120
