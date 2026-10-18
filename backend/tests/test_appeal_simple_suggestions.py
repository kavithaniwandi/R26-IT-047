# Approved UI consistency pass: shared word bands and upper-half targets replace prior length expectations.
"""Direct suggestion checks: no provider calls or diagnostic model inference."""
import json

import pytest

from app.models import appeal_guidance_service as guide
from app.models.schemas import GenerateAppealRequest, QualityScoreRequest


@pytest.fixture(autouse=True)
def no_probe(monkeypatch):
    monkeypatch.setattr(guide, "GAP_CHECKS", [])
    monkeypatch.setattr(guide, "batch_score", lambda *args: pytest.fail("Suggestions must not run inference"))


def rating(label, confidence, classifier=None):
    return {"final_label": label, "class_probs": {classifier or label: confidence}}


@pytest.mark.parametrize("label,confidence,classifier,shown", [
    ("medium", .8, "medium", True),
    ("low", .95, "low", True),
    ("high", .9, "high", False),
    ("high", .8, "high", False),
    ("high", .6, "high", False),
    ("high", .4, "high", True),
    ("high", .8, "medium", True),
])
def test_rating_gates_suggestions(label, confidence, classifier, shown):
    result = guide.guidance("A short appeal.", "English", rating(label, confidence, classifier))
    assert bool(result["suggestions"]) is shown


@pytest.mark.parametrize("language", ["English", "Sinhala", "Tamil"])
@pytest.mark.parametrize("category,minimum", [("short", 65), ("Medium", 105), ("Long", 185)])
def test_length_uses_requested_minimum_without_scoring(language, category, minimum):
    text = "word " * (minimum - 1)
    result = guide.guidance(text, language, rating("low", .8), category)
    assert result["suggestions"][0]["message"] == f"This appeal has {minimum - 1} words. Appeals under about {minimum} words tend to rate lower."
    assert guide.guidance(text + "word", language, rating("low", .8), category)["suggestions"] == []


def test_dataset_gaps_skip_matches_rank_missing_checks_and_cap_at_two(monkeypatch):
    rules = []
    for index, name in enumerate(guide.SUGGESTION_MESSAGES):
        rules.append({"check": name, "rule": {"common_pattern": f"marker{index}"}, "enabled_languages": ["English"],
                      "per_language": {"English": {"high_minus_low": .8 - index * .1,
                          "classes": {"high": {"share": .9}, "low": {"share": .1}}}}})
    monkeypatch.setattr(guide, "GAP_CHECKS", list(reversed(rules)))
    result = guide.guidance("marker0 " * 65, "English", rating("medium", .8))
    assert [s["check"] for s in result["suggestions"]] == ["human_detail", "specific_call_to_action"]
    assert [s["message"] for s in result["suggestions"]] == ["Mention who is affected.", "End with a specific action."]
    assert all(set(s) == {"check", "message", "evidence"} for s in result["suggestions"])
    assert all("90.0% of high-rated and 10.0% of low-rated English appeals" in s["evidence"] for s in result["suggestions"])
    for language in ("Sinhala", "Tamil"):
        assert [s["check"] for s in guide.guidance("short", language, rating("medium", .8))["suggestions"]] == ["length"]


def test_request_schemas_keep_only_core_inputs():
    assert set(QualityScoreRequest.model_fields) == {"appeal_text", "language", "length_category"}
    assert set(GenerateAppealRequest.model_fields) == {
        "language", "campaign_type", "location", "verified_need", "campaign_goal", "tone", "channel", "length_category",
    }


@pytest.mark.parametrize("language",["Sinhala","Tamil"])
def test_native_languages_never_surface_dataset_gaps(monkeypatch,language):
    monkeypatch.setattr(guide,"GAP_CHECKS",[{"check":"fund_use","enabled_languages":[language],"per_language":{language:{"high_minus_low":0.9}}}])
    score={"quality_score":2.0,"final_label":"low","class_probs":{"low":0.8}}
    monkeypatch.setattr(guide,"batch_score",lambda texts,language:[{"quality_score":3.0,"classifier_confidence":0.7} for _ in texts])
    result=guide.guidance('A short factual appeal.',language,score)
    assert all(s['check']=='length' for s in result['suggestions'])
    assert result['dataset_gap_status']=='not surfaced: likely augmentation artifact'
    assert result['classifier_confidence']==0.8



def test_posthoc_length_and_native_policy_in_saved_json():
    data=json.loads(guide.GAP_PATH.read_text(encoding='utf-8'))
    checks={c['check']:c for c in data['checks']+data['dropped_checks']}
    assert checks['length_at_least_60']['rule']['post_hoc_revision'] is True
    assert checks['length_at_least_60']['per_language']['English']['selected']
    assert not checks['length_band']['per_language']['English']['selected']
    for check in checks.values():
        assert not any(lang in check['enabled_languages'] for lang in ('Sinhala','Tamil'))
        assert check['per_language']['Sinhala']['evidence_note']=='not surfaced: likely augmentation artifact'

