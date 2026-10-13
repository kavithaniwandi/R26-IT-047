from __future__ import annotations

from functools import lru_cache
import json
import re
from pathlib import Path
from typing import Any

from app.models.text_negation import is_span_negated, normalize_clinical_text


RULES_PATH = Path(__file__).resolve().parents[2] / "ml_models" / "specialty_rules.json"
GERIATRIC_LABEL = "Geriatric"
EMERGENCY_LABEL = "Emergency Medicine"
GENERAL_PRACTICE_LABEL = "General Practice"
PEDIATRIC_LABEL = "Pediatric"
OBSTETRIC_LABEL = "Obstetric & Gynecologic"
RESPIRATORY_LABEL = "Respiratory"
ENDOCRINE_LABEL = "Endocrine & Metabolic"
NEURO_LABEL = "Neurological"
SPO2_RESPIRATORY_BOOST_THRESHOLD = 92.0
SBP_EMERGENCY_BOOST_THRESHOLD = 90.0
HR_EMERGENCY_BOOST_THRESHOLD = 120.0
RESPIRATORY_VITAL_BOOST = 3.0
EMERGENCY_VITAL_BOOST = 4.0
EMERGENCY_MENTAL_STATUS_BOOST = 4.5
ZERO_IS_MISSING_VITAL_KEYS = {"vital_spo2", "vital_hr", "vital_sbp"}


@lru_cache(maxsize=1)
def _load_rules() -> dict[str, Any]:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    specialties = set(rules.get("specialties") or [])
    for rule in rules.get("rules") or []:
        specialty = rule.get("specialty")
        if specialty not in specialties:
            raise ValueError(f"Specialty rule uses unknown label: {specialty}")
    return rules


def _whole_word_pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![a-z0-9_]){re.escape(phrase.lower())}(?![a-z0-9_])")


def _keyword_matches(text: str, keyword: str) -> list[tuple[int, int]]:
    normalized_keyword = normalize_clinical_text(keyword)
    if not normalized_keyword:
        return []
    pattern = _whole_word_pattern(normalized_keyword)
    return [
        (match.start(), match.end())
        for match in pattern.finditer(text)
        if not is_span_negated(text, match.start())
    ]


def _active_red_flags(red_flags: Any) -> set[str]:
    if not red_flags:
        return set()
    if isinstance(red_flags, dict):
        return {str(key) for key, value in red_flags.items() if value}
    if isinstance(red_flags, (list, tuple, set)):
        return {str(value) for value in red_flags if value}
    return {str(red_flags)}


def _confidence(top_score: float, total_score: float, fallback: bool) -> float:
    if fallback or total_score <= 0:
        return 0.1
    return round(max(0.0, min(1.0, top_score / total_score)), 4)


def _numeric_vital(vitals: dict | None, key: str) -> float | None:
    value = (vitals or {}).get(key)
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    # A literal zero for SpO2, HR, or SBP is physiologically implausible here;
    # treat it as missing so blank UI values cannot become threshold hits.
    if key in ZERO_IS_MISSING_VITAL_KEYS and numeric <= 0:
        return None
    return numeric


def _add_score(
    scores: dict[str, float],
    matched_by_specialty: dict[str, list[str]],
    clinical_hit_specialties: set[str],
    specialty: str,
    weight: float,
    keyword: str,
) -> None:
    scores[specialty] = scores.get(specialty, 0.0) + weight
    matched_by_specialty.setdefault(specialty, []).append(keyword)
    clinical_hit_specialties.add(specialty)


def suggest_specialty(
    symptoms: str | None,
    clinical_note: str | None,
    red_flags: Any,
    age: int | None,
    severity: str,
    mapped_complaints: list[str] | None,
    vitals: dict | None = None,
) -> dict:
    rules = _load_rules()
    text = normalize_clinical_text(
        " ".join(
            item
            for item in [
                symptoms or "",
                clinical_note or "",
                " ".join(mapped_complaints or []),
            ]
            if item
        )
    )
    normalized_severity = str(severity).upper()
    active_flags = _active_red_flags(red_flags)
    scores: dict[str, float] = {}
    matched_by_specialty: dict[str, list[str]] = {}
    clinical_hit_specialties: set[str] = set()

    for rule in rules.get("rules") or []:
        specialty = rule["specialty"]
        weight = float(rule.get("weight", 1.0))
        for keyword in rule.get("keywords") or []:
            if _keyword_matches(text, keyword):
                _add_score(scores, matched_by_specialty, clinical_hit_specialties, specialty, weight, keyword)

        flag_hits = active_flags.intersection(set(rule.get("red_flags") or []))
        if flag_hits:
            boost = float(rule.get("red_flag_weight", 1.0)) * len(flag_hits)
            for flag in sorted(flag_hits):
                _add_score(scores, matched_by_specialty, clinical_hit_specialties, specialty, boost / len(flag_hits), flag)

    spo2 = _numeric_vital(vitals, "vital_spo2")
    sbp = _numeric_vital(vitals, "vital_sbp")
    hr = _numeric_vital(vitals, "vital_hr")
    if spo2 is not None and spo2 < SPO2_RESPIRATORY_BOOST_THRESHOLD:
        _add_score(
            scores,
            matched_by_specialty,
            clinical_hit_specialties,
            RESPIRATORY_LABEL,
            RESPIRATORY_VITAL_BOOST,
            f"SpO2 < {SPO2_RESPIRATORY_BOOST_THRESHOLD:g}",
        )
        if normalized_severity in {"HIGH", "CRITICAL"}:
            _add_score(
                scores,
                matched_by_specialty,
                clinical_hit_specialties,
                EMERGENCY_LABEL,
                EMERGENCY_VITAL_BOOST,
                f"SpO2 < {SPO2_RESPIRATORY_BOOST_THRESHOLD:g}",
            )

    if normalized_severity == "HIGH":
        if sbp is not None and sbp < SBP_EMERGENCY_BOOST_THRESHOLD:
            _add_score(
                scores,
                matched_by_specialty,
                clinical_hit_specialties,
                EMERGENCY_LABEL,
                EMERGENCY_VITAL_BOOST,
                f"SBP < {SBP_EMERGENCY_BOOST_THRESHOLD:g}",
            )
        if hr is not None and hr > HR_EMERGENCY_BOOST_THRESHOLD:
            _add_score(
                scores,
                matched_by_specialty,
                clinical_hit_specialties,
                EMERGENCY_LABEL,
                EMERGENCY_VITAL_BOOST,
                f"HR > {HR_EMERGENCY_BOOST_THRESHOLD:g}",
            )

    mental_status_terms = ("altered consciousness", "altered mental status", "confusion", "confused", "drowsy")
    if any(_keyword_matches(text, term) for term in mental_status_terms):
        _add_score(
            scores,
            matched_by_specialty,
            clinical_hit_specialties,
            EMERGENCY_LABEL,
            EMERGENCY_MENTAL_STATUS_BOOST,
            "altered mental status",
        )

    age_boosts = rules.get("age_boosts") or {}
    if age is not None:
        pediatric = age_boosts.get("pediatric") or {}
        if age < int(pediatric.get("age_lt", -1)):
            specialty = pediatric.get("specialty")
            scores[specialty] = scores.get(specialty, 0.0) + float(pediatric.get("weight", 0.0))
            matched_by_specialty.setdefault(specialty, []).append(f"age < {pediatric.get('age_lt')}")

        geriatric = age_boosts.get("geriatric") or {}
        if age >= int(geriatric.get("age_gte", 10_000)):
            specialty = geriatric.get("specialty")
            scores[specialty] = scores.get(specialty, 0.0) + float(geriatric.get("weight", 0.0))
            matched_by_specialty.setdefault(specialty, []).append(f"age >= {geriatric.get('age_gte')}")

    non_geriatric_scores = {
        specialty: score
        for specialty, score in scores.items()
        if specialty != GERIATRIC_LABEL and score > 0
    }
    default_primary = rules.get("default_primary", GENERAL_PRACTICE_LABEL)
    fallback = not bool(clinical_hit_specialties - {GERIATRIC_LABEL}) and not non_geriatric_scores

    if fallback:
        return {
            "primary": default_primary,
            "secondary": [GERIATRIC_LABEL] if scores.get(GERIATRIC_LABEL) else [],
            "matched_keywords": matched_by_specialty.get(GERIATRIC_LABEL, []),
            "confidence": 0.1,
            "reason": "No specific specialty keywords found",
            "fallback": True,
        }

    ranked = sorted(non_geriatric_scores, key=lambda item: (-non_geriatric_scores[item], item))
    clinical_primary = ranked[0] if ranked else default_primary
    endocrine_emergency = False

    if (
        clinical_primary == NEURO_LABEL
        and scores.get(EMERGENCY_LABEL, 0.0) > 0
        and scores.get(RESPIRATORY_LABEL, 0.0) > 0
        and spo2 is not None
        and spo2 < SPO2_RESPIRATORY_BOOST_THRESHOLD
    ):
        clinical_primary = EMERGENCY_LABEL

    if scores.get(EMERGENCY_LABEL, 0.0) > 0 and scores.get(ENDOCRINE_LABEL, 0.0) > 0:
        if any(_keyword_matches(text, term) for term in ("insulin", "diabetes", "diabetic", "glucose", "sugar")):
            clinical_primary = EMERGENCY_LABEL
            endocrine_emergency = True

    primary = clinical_primary
    secondary: list[str] = []

    if normalized_severity == "CRITICAL":
        emergency = rules.get("critical_primary", EMERGENCY_LABEL)
        primary = emergency
        if clinical_primary != emergency:
            secondary.append(clinical_primary)
    elif normalized_severity == "LOW" and clinical_primary not in {PEDIATRIC_LABEL, OBSTETRIC_LABEL}:
        primary = default_primary
        if clinical_primary != default_primary:
            secondary.append(clinical_primary)

    if primary == EMERGENCY_LABEL and endocrine_emergency:
        for specialty in (ENDOCRINE_LABEL, NEURO_LABEL):
            if scores.get(specialty, 0.0) > 0 and specialty not in secondary:
                secondary.append(specialty)

    threshold = float(rules.get("secondary_threshold", 1.5))
    for specialty in ranked:
        if endocrine_emergency and specialty == RESPIRATORY_LABEL:
            continue
        if specialty == primary or specialty in secondary:
            continue
        if non_geriatric_scores[specialty] >= threshold:
            secondary.append(specialty)
        if len(secondary) >= 2:
            break

    if scores.get(GERIATRIC_LABEL) and GERIATRIC_LABEL not in secondary and primary != GERIATRIC_LABEL:
        if len(secondary) < 2:
            secondary.append(GERIATRIC_LABEL)

    top_score = scores.get(primary, non_geriatric_scores.get(clinical_primary, 0.0))
    total_score = sum(scores.values())
    ordered_keywords: list[str] = []
    for specialty in [primary, *secondary, clinical_primary]:
        for keyword in matched_by_specialty.get(specialty, []):
            if keyword not in ordered_keywords:
                ordered_keywords.append(keyword)

    reason = f"Matched {primary} from clinical keywords"
    if str(severity).upper() == "CRITICAL" and primary == rules.get("critical_primary", "Emergency Medicine"):
        reason = "CRITICAL severity defaults advisory primary to Emergency Medicine"

    return {
        "primary": primary,
        "secondary": secondary[:2],
        "matched_keywords": ordered_keywords[:8],
        "confidence": _confidence(top_score, total_score, False),
        "reason": reason,
        "fallback": False,
    }
