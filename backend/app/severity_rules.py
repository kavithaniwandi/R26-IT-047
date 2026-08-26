import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
RULE_CONFIG_PATH = BASE_DIR / "models" / "severity_rule_based" / "keywords.json"
SEVERITY_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
SCORE_BANDS = {
    "CRITICAL": 80.0,
    "HIGH": 60.0,
    "MEDIUM": 40.0,
    "LOW": 0.0,
}
SCORE_CAPS = {
    "CRITICAL": 19.9,
    "HIGH": 19.9,
    "MEDIUM": 19.9,
    "LOW": 39.9,
}
SCORE_MULTIPLIERS = {
    "CRITICAL": 7.0,
    "HIGH": 7.0,
    "MEDIUM": 15.0,
    "LOW": 10.0,
}


def _load_rules() -> dict:
    with RULE_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_keyword_matches(text: str, keyword_list: list[dict]) -> tuple[float, list[str]]:
    score = 0.0
    matched_rules = []

    for keyword in keyword_list:
        phrase = normalize_text(keyword["text"])
        count = text.count(phrase)

        if count > 0:
            score += count * float(keyword["weight"])
            matched_rules.append(keyword["text"])

    return score, matched_rules


def _age_tie_breaker(age: int | None) -> float:
    if age is None:
        return 0.0
    return min(max(age, 0), 120) / 10000


def _compute_priority_score(
    severity: str,
    scores: dict[str, float],
    age: int | None = None,
    critical_trigger: str | None = None,
) -> float:
    if critical_trigger:
        return 100.0

    if all(score == 0 for score in scores.values()):
        return round(_age_tie_breaker(age), 4)

    base_score = SCORE_BANDS[severity]
    rule_component = min(
        scores[severity] * SCORE_MULTIPLIERS[severity],
        SCORE_CAPS[severity],
    )
    return round(base_score + rule_component + _age_tie_breaker(age), 4)


def predict_severity(clinical_note: str, age: int | None = None) -> dict:
    rules = _load_rules()
    normalized_note = normalize_text(clinical_note)

    for trigger in rules["critical_triggers"]:
        normalized_trigger = normalize_text(trigger)
        if normalized_trigger in normalized_note:
            scores = {
                "CRITICAL": 100.0,
                "HIGH": 0.0,
                "MEDIUM": 0.0,
                "LOW": 0.0,
            }
            return {
                "severity": "CRITICAL",
                "priority_score": _compute_priority_score(
                    "CRITICAL",
                    scores,
                    age=age,
                    critical_trigger=trigger,
                ),
                "scores": scores,
                "matched_rules": [trigger],
                "critical_trigger": trigger,
            }

    scores = {}
    matched_rules = []
    category_map = {
        "CRITICAL": "critical_keywords",
        "HIGH": "high_keywords",
        "MEDIUM": "medium_keywords",
        "LOW": "low_keywords",
    }

    for severity, config_key in category_map.items():
        score, matches = count_keyword_matches(normalized_note, rules[config_key])
        scores[severity] = score
        matched_rules.extend(matches)

    if all(score == 0 for score in scores.values()):
        severity = "LOW"
    else:
        severity = max(SEVERITY_ORDER, key=lambda item: (scores[item], -SEVERITY_ORDER.index(item)))

    return {
        "severity": severity,
        "priority_score": _compute_priority_score(severity, scores, age=age),
        "scores": scores,
        "matched_rules": matched_rules,
        "critical_trigger": None,
    }