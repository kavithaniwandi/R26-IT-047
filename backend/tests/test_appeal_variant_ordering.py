"""Agreement-first ordering changes presentation, never the scoring rule."""
import pytest

from app.models import appeal_guidance_service as guidance


def variant(name, label, agreement, confidence, score):
    return {"style": name, "final_label": label, "label_agreement": agreement,
            "classifier_confidence": confidence, "quality_score": score}


def test_agreement_precedes_higher_label_confidence_and_score():
    items = [variant("high-disagrees", "high", False, .99, 4.9),
             variant("low-agrees", "low", True, .4, 1.8),
             variant("medium-agrees", "medium", True, .6, 2.9)]
    ordered = guidance.ordered_variants(items)
    assert [item["style"] for item in ordered] == ["medium-agrees", "low-agrees", "high-disagrees"]
    assert guidance.recommended(items) is ordered[0]
    assert len(ordered) == len(items)
    assert items[0]["style"] == "high-disagrees"  # Caller/cache data is not mutated.


@pytest.mark.parametrize("agreement", [True, False])
def test_label_then_confidence_then_score_even_when_none_agree(agreement):
    items = [variant("low", "low", agreement, .99, 2),
             variant("medium", "medium", agreement, .99, 3),
             variant("high-low-confidence", "high", agreement, .5, 4.9),
             variant("high-lower-score", "high", agreement, .6, 3.9),
             variant("high-best", "high", agreement, .6, 4.1)]
    assert [item["style"] for item in guidance.ordered_variants(items)] == [
        "high-best", "high-lower-score", "high-low-confidence", "medium", "low",
    ]


def test_ties_are_stable_and_all_variants_survive():
    items = [variant(name, "high", False, .57, 3.9) for name in ("formal", "community", "urgent")]
    assert guidance.ordered_variants(items) == items
    assert guidance.recommended([]) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("original,candidate,kept", [
    (("high", True, .7, 4.0), ("high", False, .95, 4.8), False),
    (("high", False, .95, 4.8), ("medium", True, .7, 3.0), False),  # Approved: agreement alone cannot replace a higher visible label.
    (("medium", False, .9, 3.0), ("high", False, .6, 3.9), True),
    (("high", True, .7, 4.0), ("high", True, .7, 4.0), False),
    (("high", True, .7, 3.9), ("high", True, .7, 4.1), True),
])
async def test_improve_candidates_use_agreement_first_order(monkeypatch, tmp_path, original, candidate, kept):
    from app.models import appeal_generation_service as service
    from app.services import appeal_budget as budgets
    text = " ".join(["Families in Malabe need water bottles and tents for 20 people. Please donate today."] * 5)
    def scored(values):
        label, agreement, confidence, score = values
        result = variant("formal", label, agreement, confidence, score)
        classifier = label if agreement else "medium" if label != "medium" else "high"
        return {**result, "raw_quality_score": score, "confidence": confidence,
                "class_probs": {classifier: confidence}, "predicted_class": classifier}
    queue = iter([[scored(original)], [scored(candidate)]])
    monkeypatch.setattr(guidance, "batch_score", lambda *args: next(queue))
    monkeypatch.setattr(guidance, "guidance", lambda *args: {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    rewrite = "Please donate today. " + " ".join(["Families in Malabe need water bottles and tents for 20 people. Please donate today."] * 4) + " Families in Malabe need water bottles and tents for 20 people."
    async def provider(prompt, budget):
        budget.consume()
        budget.account(True)
        return (rewrite if kept else text), "offline-model"
    monkeypatch.setattr(service, "_call", provider)
    budgets.DAILY.clear()
    try:
        result = await service.repair(text, {"language": "English"}, "candidate-order-test")
        assert result["kept"] is kept
        assert result["after"]["final_label"] == (candidate[0] if kept else original[0])
        assert result["gemini_calls_used"] == 1
    finally:
        budgets.DAILY.clear()


@pytest.mark.asyncio
async def test_remaining_generation_returns_sorted_variants_and_caches_them(monkeypatch):
    import json
    from app.models import appeal_generation_service as service
    from app.services import appeal_budget as budgets
    budgets.SESSIONS.clear()
    async def provider(prompt, budget, **kwargs):
        return json.dumps({"appeals": [
            {"style": "community", "appeal_text": "A community appeal asking for support."},
            {"style": "urgent", "appeal_text": "An urgent appeal asking for support."},
        ]}), "offline-model"
    monkeypatch.setattr(service, "_call", provider)
    monkeypatch.setattr(guidance, "batch_score", lambda *args: [
        variant("community", "high", False, .8, 4), variant("urgent", "medium", True, .7, 3),
    ])
    monkeypatch.setattr(guidance, "guidance_many", lambda *args: [
        {"suggestions_ms": 0, "length_warning": None}, {"suggestions_ms": 0, "length_warning": None},
    ])
    payload = {"language": "English", "campaign_type": "Flood Relief", "location": "Malabe",
               "verified_need": "water", "campaign_goal": "support affected families"}
    result = await service.generate(payload, remaining=True, client="ordering-test")
    assert [item["style"] for item in result] == ["urgent", "community"]
    assert await service.generate(payload, remaining=True, client="ordering-test") == result
    budgets.SESSIONS.clear()


@pytest.mark.parametrize("better,worse,category", [
    ({"word_count": 80, "final_label": "low", "label_agreement": False}, {"word_count": 52, "final_label": "high", "label_agreement": True}, "short"),
    ({"label_agreement": True, "final_label": "low"}, {"label_agreement": False, "final_label": "high"}, "short"),
    ({"final_label": "high", "classifier_confidence": .4}, {"final_label": "medium", "classifier_confidence": .99}, "short"),
    ({"classifier_confidence": .8, "quality_score": 3.9}, {"classifier_confidence": .7, "quality_score": 4.9}, "short"),
    ({"quality_score": 4.1}, {"quality_score": 3.9}, "short"),
    ({"word_count": 120, "final_label": "low"}, {"word_count": 80, "final_label": "high"}, "medium"),
    ({"word_count": 220, "final_label": "low"}, {"word_count": 120, "final_label": "high"}, "long"),
    ({"word_count": 80, "final_label": "low"}, {"word_count": 101, "final_label": "high"}, "short"),
])
def test_each_ordering_key_and_selected_length_band(better, worse, category):
    base = {"word_count": 80, "final_label": "high", "label_agreement": True,
            "classifier_confidence": .6, "quality_score": 4.0}
    good = {**base, **better, "style": "better"}
    bad = {**base, **worse, "style": "worse"}
    ordered = guidance.ordered_variants([bad, good], category)
    assert ordered == [good, bad]
    assert guidance.recommended([bad, good], category) is good
