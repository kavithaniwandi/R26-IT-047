"""Offline contracts for shared lengths and pasted guidance."""
import asyncio
import json

import pytest

from app.models import appeal_guidance_service as guide
from app.models import appeal_generation_service as generation
from app.models.schemas import GenerateAppealRequest


@pytest.mark.parametrize("category,minimum,maximum,target", [
    ("short", 65, 100, (85, 95)), ("medium", 105, 150, (130, 145)),
    ("long", 185, 250, (220, 240)),
])
def test_shared_config_drives_band_prompt_and_warning(category, minimum, maximum, target):
    assert guide.length_band(category) == (minimum, maximum)
    config = guide.length_config(category)
    assert (config["target_minimum"], config["target_maximum"]) == target
    assert target[0] >= (minimum + maximum) / 2
    prompt = generation._prompt({"campaign_type": "Flood Relief", "length_category": category})
    assert f"TARGET: {target[0]}-{target[1]}" in prompt
    assert f"at least {minimum} words" in prompt
    for words in (minimum, maximum):
        assert guide.length_warning("word " * words, category) is None
    for words in (minimum - 1, maximum + 1, 52):
        assert str(words) in guide.length_warning("word " * words, category)


def test_legacy_very_short_still_accepted_but_hidden_from_dropdown():
    request = GenerateAppealRequest(campaign_type="Flood Relief", length_category="very_short")
    assert request.length_category == "very_short"
    assert guide.length_band(request.length_category) == (1, 40)
    assert guide.length_config(request.length_category)["visible"] is False


@pytest.mark.parametrize("words,shown", [(52, True), (59, True), (60, False), (64, False), (65, False)])
@pytest.mark.parametrize("language", ["English", "Sinhala", "Tamil"])
def test_analyzer_pasted_length_is_independent_of_generator_band(monkeypatch, words, shown, language):
    monkeypatch.setattr(guide, "GAP_CHECKS", [])
    monkeypatch.setattr(guide, "batch_score", lambda *args: pytest.fail("No counterfactual scoring"))
    result = guide.guidance("word " * words, language, {"final_label": "low", "class_probs": {"low": .8}}, None)
    assert bool(result["suggestions"]) is shown
    assert result["length_warning"] is None
    if shown:
        assert result["suggestions"][0]["message"] == f"This appeal has {words} words. High-rated appeals in the data are usually about 60 or more."
        assert "requested minimum" not in json.dumps(result)




@pytest.mark.asyncio
async def test_analyzer_route_uses_pasted_length_guidance(monkeypatch):
    from app.models import main, quality_service
    from app.services import mongo_service
    monkeypatch.setattr(quality_service, "get_quality_score", lambda *args, **kwargs: {
        "score": 3.9, "status": "high", "predicted_class": "medium",
        "class_probs": {"low": .1, "medium": .57, "high": .33},
        "method": "ml_model", "confidence": .57, "low_confidence": False,
    })
    async def no_log(*args, **kwargs):
        pass
    monkeypatch.setattr(mongo_service, "log_appeal_analysis", no_log)
    monkeypatch.setattr(guide, "GAP_CHECKS", [])
    result = await main.analyse_appeal({"appeal_text": "word " * 64, "language": "English"})
    assert result["suggestions"] == []
    assert result["length_warning"] is None
    await asyncio.sleep(0)


@pytest.mark.parametrize("channel", ["facebook", "website", "email", "sms", "whatsapp"])
def test_channel_prompts_do_not_override_shared_word_band(channel):
    from app.models import gemini_service
    rule = gemini_service.CHANNEL_RULES[channel]
    assert "words" not in rule
    assert "characters" not in rule
    prompt = gemini_service._build_generation_prompt({"campaign_type": "Flood Relief", "channel": channel, "length_category": "long"})
    assert "Target 220-240 words" in prompt
    assert "at least 185 words" in prompt
