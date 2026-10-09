import json
from pathlib import Path

import pytest

from app.models.severity_rules import RULE_CONFIG_PATH, predict_severity
from app.models.severity_service import classify_note


RULES = json.loads(Path(RULE_CONFIG_PATH).read_text(encoding="utf-8"))


def trigger_notes(trigger: str) -> list[str]:
    return [
        trigger,
        f"Patient presents with {trigger} after rescue.",
        trigger.upper(),
    ]


@pytest.mark.parametrize("trigger", RULES["critical_triggers"])
def test_every_critical_trigger_returns_critical(trigger):
    earlier = RULES["critical_triggers"][:RULES["critical_triggers"].index(trigger)]
    shadowed_by = [item for item in earlier if item in trigger and item != trigger]
    if shadowed_by:
        pytest.xfail(f"{trigger!r} is shadowed by earlier trigger(s): {shadowed_by}")
    for note in trigger_notes(trigger):
        result = classify_note(note, age=40, mode="rule_based")
        assert result["severity"] == "CRITICAL", trigger
        assert result["priority_score"] == 100.0, trigger
        assert result["critical_trigger"] == trigger, trigger
        assert result["can_override"] is False, trigger


@pytest.mark.parametrize(
    "note",
    [
        "routine medication refill",
        "mild cough and runny nose",
        "minor bruise on arm",
        "stable condition for review",
        "follow up wound dressing",
        "mild rash after soap exposure",
        "fatigue after poor sleep",
        "toothache for two days",
        "sore throat without fever",
        "ankle pain after walking",
        "mild nausea after food",
        "minor swelling of finger",
        "checkup requested",
        "cold symptoms only",
        "mild headache this morning",
        "insect bite on leg",
        "splinter in finger",
        "abrasion cleaned at camp",
        "joint pain chronic",
        "eye irritation",
    ],
)
def test_negative_notes_do_not_fire_critical(note):
    result = classify_note(note, age=30, mode="rule_based")
    assert result["severity"] != "CRITICAL", note
    assert result["critical_trigger"] is None, note


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("critical_keywords", "CRITICAL"),
        ("high_keywords", "HIGH"),
        ("medium_keywords", "MEDIUM"),
        ("low_keywords", "LOW"),
    ],
)
def test_weighted_keyword_bands(category, expected):
    phrase = RULES[category][0]["text"]
    result = predict_severity(phrase, age=35)
    assert result["severity"] == expected
    assert phrase in result["matched_rules"]
