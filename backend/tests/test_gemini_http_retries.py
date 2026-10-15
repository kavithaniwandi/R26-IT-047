import json
from urllib.parse import urlparse

import pytest
import requests
from google import genai

from app.models import gemini_service as gs
from app.services import credit_monitor as cm

TEXT = 'Families in Nawalapitiya need water bottles and tents for 20 people. Donate today.'


@pytest.fixture
def transport(monkeypatch, tmp_path):
    monkeypatch.setattr(cm, 'STATE_FILE', tmp_path / 'credit.json')
    cm._key_state.clear()
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
        model = urlparse(url).path.rsplit('/', 1)[-1].split(':')[0]
        key_index = ['fake-one', 'fake-two'].index(kwargs['headers']['x-goog-api-key']) + 1
        calls.append((model, key_index))
        code, message = replies.pop(0)
        response = requests.Response()
        response.status_code = code
        response._content = json.dumps(
            {'candidates': [{'content': {'role': 'model', 'parts': [{'text': TEXT}]}, 'finishReason': 'STOP'}]}
            if code == 200 else {'error': {'code': code, 'message': message, 'status': 'UNAVAILABLE' if code >= 500 else 'RESOURCE_EXHAUSTED'}}
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
    assert delays == [2.25]
    assert result['generator_status'] == 'live'
    assert result['generator_model'] == 'main-flash'
    assert result['generator_error'] is None
    assert not cm._key_state['gemini_key_1']['exhausted']


@pytest.mark.asyncio
async def test_503_exhausted_then_fallback_model_success(transport):
    replies, calls, delays = transport
    replies.extend([(503, 'overloaded')] * 4 + [(200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5, max_retries=1)
    assert calls == [('main-flash', 1)] * 4 + [('backup-flash', 1)]
    assert delays == [2.25, 4.25, 8.25]
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
async def test_429_per_minute_backs_off_without_exhausting_key(transport):
    replies, calls, delays = transport
    replies.extend([(429, 'RESOURCE_EXHAUSTED GenerateRequestsPerMinute'), (200, '')])
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5, max_retries=1)
    assert calls == [('main-flash', 1)] * 2
    assert delays == [2.25]
    assert not cm._key_state['gemini_key_1']['exhausted']
    assert result['generator_status'] == 'live'


@pytest.mark.asyncio
async def test_all_models_overloaded_preserves_final_cause(transport):
    replies, calls, delays = transport
    replies.extend([(503, 'overloaded')] * 6)
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert calls == [('main-flash', 1)] * 4 + [('backup-flash', 1), ('backup-lite', 1)]
    assert result['generator_model'] == 'backup-lite'
    assert result['generator_error'] == '503 overloaded after 0 retries'
    assert cm._key_state == {}


@pytest.mark.asyncio
async def test_primary_failure_preserves_three_retry_cause(transport, monkeypatch):
    replies, calls, delays = transport
    monkeypatch.setattr(gs.settings, 'GEMINI_FALLBACK_MODELS', '')
    replies.extend([(503, 'overloaded')] * 4)
    result = await gs.call_gemini_with_key_fallback('prompt', 0.5)
    assert result['generator_error'] == '503 overloaded after 3 retries'
    assert len(calls) == 4


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
    replies.extend([(503, 'overloaded')] * 4)
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
    assert result[0]['generator_error'] == '503 overloaded after 3 retries'


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
    assert delays == [2.25]
