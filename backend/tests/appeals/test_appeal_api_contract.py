import asyncio
import logging

import pytest

from app.models import gemini_service as gs
from app.models import main
from app.models.schemas import GenerateAppealRequest, QualityScoreRequest
from app.models import quality_service
from app.services import mongo_service


@pytest.mark.asyncio
async def test_quality_response_preserves_classifier_and_final_label(monkeypatch):
    monkeypatch.setattr(quality_service, 'get_quality_score', lambda *a, **kw: {
        'score': 4.0, 'status': 'high', 'predicted_class': 'medium',
        'class_probs': {'low': 0.21, 'medium': 0.44, 'high': 0.35},
        'method': 'ml_model', 'confidence': 0.44, 'confidence_normalised': 0.44,
        'confidence_display': '44%', 'low_confidence': True,
    })
    result = await main.evaluate_quality(QualityScoreRequest(appeal_text='Please donate water.'))
    assert result.final_label == 'high'
    assert result.predicted_class == 'medium'
    assert result.class_probs['medium'] == result.confidence == 0.44
    # The Generator evaluation and Analyzer must retain identical scoring metadata.
    async def no_log(*args, **kwargs):
        pass
    monkeypatch.setattr(mongo_service, 'log_appeal_analysis', no_log)
    analysis = await main.analyse_appeal({'appeal_text': 'Please donate water.', 'language': 'English'})
    assert analysis['score'] == result.score
    assert analysis['final_label'] == result.final_label
    assert analysis['raw_quality_score'] == result.raw_quality_score
    assert analysis['class_probs'] == result.class_probs
    assert analysis['classifier_confidence'] == result.classifier_confidence
    assert analysis['confidence_level'] == result.confidence_level
    await asyncio.sleep(0)



@pytest.mark.asyncio
@pytest.mark.parametrize('single', [False, True])
async def test_mongo_failure_warns_and_preserves_generation(monkeypatch, caplog, single):
    variant = {
        'model': 'mock', 'temperature': 0.5, 'appeal_text': 'Donate water today.',
        'quality_label': 'high', 'final_label': 'high', 'quality_score': 4.0,
        'predicted_class': 'medium', 'class_probs': {'medium': 0.44},
        'confidence': 0.44, 'confidence_normalised': 0.44, 'confidence_display': '44%',
    }
    async def generate(*a, **kw):
        return [variant]
    async def fail_log(*a, **kw):
        raise ConnectionError('Private connection details must not be logged')
    monkeypatch.setattr(gs, 'generate_first_appeal_variant', generate)
    monkeypatch.setattr(gs, 'generate_donation_appeal', lambda *a: variant['appeal_text'])
    monkeypatch.setattr(mongo_service, 'log_appeal_generation', fail_log)
    request = GenerateAppealRequest(campaign_type='Flood Relief')
    with caplog.at_level(logging.WARNING, logger=main.__name__):
        if single:
            result = await main.generate_appeal(request)
            assert result.appeal_text == variant['appeal_text']
        else:
            result = await main.generate_appeal_variants_endpoint(request)
            assert result.variants[0].final_label == 'high'
        # Logging runs off the response path; wait for its tracked tasks.
        await asyncio.wait_for(
            asyncio.gather(*tuple(main._APPEAL_LOG_TASKS)), timeout=1.0
        )
    assert any(r.levelno == logging.WARNING and 'ConnectionError' in r.message for r in caplog.records)
    assert 'Private connection details' not in caplog.text
