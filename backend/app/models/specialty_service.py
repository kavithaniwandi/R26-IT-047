from __future__ import annotations

from functools import lru_cache
import json
import re
from pathlib import Path
from typing import Any

from app.models.text_negation import is_span_negated, normalize_clinical_text
from app.models.vitals_normalizer import normalized_vital_value


RULES_PATH = Path(__file__).resolve().parents[2] / "ml_models" / "specialty_rules.json"
GERIATRIC_LABEL = "Geriatric"
EMERGENCY_LABEL = "Emergency Medicine"
GENERAL_PRACTICE_LABEL = "General Practice"
PEDIATRIC_LABEL = "Pediatric"
OBSTETRIC_LABEL = "Obstetric & Gynecologic"
RESPIRATORY_LABEL = "Respiratory"
CARDIOVASCULAR_LABEL = "Cardiovascular"
ENDOCRINE_LABEL = "Endocrine & Metabolic"
NEURO_LABEL = "Neurological"
SPO2_RESPIRATORY_BOOST_THRESHOLD = 92.0
SBP_EMERGENCY_BOOST_THRESHOLD = 90.0
HR_EMERGENCY_BOOST_THRESHOLD = 120.0
RESPIRATORY_VITAL_BOOST = 3.0
EMERGENCY_VITAL_BOOST = 4.0
EMERGENCY_MENTAL_STATUS_BOOST = 4.5


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
        if _is_current_patient_evidence(text, match.start(), match.end())
    ]


def _is_current_patient_evidence(text: str, start: int, end: int) -> bool:
    """Conservative local context filtering; does not alter severity text handling."""
    prefix = re.split(r"[.;,!?]|\b(?:but|however|now|current|currently|today)\b", text[:start])[-1]
    if re.match(r"\s+(?:(?:is|are|was|were)\s+)?(?:absent|not present|denied|ruled out|resolved)\b", text[end:]):
        return False
    if is_span_negated(prefix, len(prefix)):
        return False
    # Extend negation across coordinated lists without crossing a new assertion.
    negation = re.search(r"\b(?:no|not|denies|deny|denied|without|negative for)\b(.*)$", prefix)
    if negation and re.search(r"\b(?:or|and|nor)\b", negation.group(1)):
        if not re.search(r"\b(?:with|has|reports|developed|presents)\b", negation.group(1)):
            return False
    if re.search(r"\b(?:family history of|history of|previously|previous|past|resolved|childhood)\b", prefix):
        return False
    if re.search(r"\bknown\s*$", prefix):
        return False
    if re.search(r"\b(?:my|his|her|their|patient s)\s*$", prefix) and re.match(
        r"(?:child|son|daughter)\b", text[start:]
    ):
        return False
    relative = re.search(
        r"\b(?:(?:mother|father|sister|brother|wife|husband|partner)|(?:my|his|her|their|patient s)\s+(?:child|son|daughter))\s+(?:has|had|with|reports|is|was)\b",
        prefix,
    )
    if relative and not re.search(r"\b(?:patient|he|she)\s+(?:has|reports|is)\b", prefix[relative.end():]):
        return False
    return True


def _routine_phrase_preferences_allowed(severity: str, flags: set[str], vitals: dict | None) -> bool:
    if severity not in {"LOW", "MEDIUM"} or flags:
        return False
    # Reuse the model's existing abnormal-vital feature boundaries; do not
    # introduce new clinical thresholds or alter its severity decision.
    from app.models.severity_pipeline import VITAL_THRESHOLDS
    import operator

    comparisons = {"<": operator.lt, ">": operator.gt, ">=": operator.ge, "==": operator.eq}
    hr = _numeric_vital(vitals, "vital_hr")
    if hr is not None and hr > HR_EMERGENCY_BOOST_THRESHOLD:
        return False
    for name, (key, comparison, threshold) in VITAL_THRESHOLDS.items():
        if name == "vf_pain_none":
            continue
        value = _numeric_vital(vitals, key)
        if value is not None and comparisons[comparison](value, threshold):
            return False
    return True


def _rule_keyword_hits(text: str, rule: dict, rules: dict, prefer_specific: bool = False) -> list[str]:
    """Count an equivalent clinical signal once per specialty, longest phrase first."""
    groups = {
        normalize_clinical_text(term): index
        for index, terms in enumerate(rules.get("equivalent_keywords") or [])
        for term in terms
    }
    hits = []
    seen = set()
    occupied = []
    for keyword in sorted(rule.get("keywords") or [], key=lambda term: (-len(term), term)):
        matches = _keyword_matches(text, keyword)
        if prefer_specific:
            specific_spans = [
                span
                for preference in rules.get("specific_phrase_preferences") or []
                if preference["generic_specialty"] == rule["specialty"] and preference["generic"] == keyword
                for span in _keyword_matches(text, preference["specific"])
            ]
            if matches and all(any(a <= start and end <= b for a, b in specific_spans) for start, end in matches):
                continue
        signal = groups.get(normalize_clinical_text(keyword), keyword)
        if signal in seen:
            continue
        for start, end in matches:
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            hits.append(keyword)
            seen.add(signal)
            occupied.append((start, end))
            break
    return hits


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
    return normalized_vital_value(vitals, key)


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


def _matched_terms(text: str, terms: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    matches: list[str] = []
    occupied: list[tuple[int, int]] = []
    for term in sorted(terms, key=lambda value: (-len(str(value)), str(value))):
        term_text = str(term)
        for start, end in _keyword_matches(text, term_text):
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            if term_text not in matches:
                matches.append(term_text)
            occupied.append((start, end))
            break
    return matches


def _cardiac_chest_pain_pattern(text: str, rules: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    config = rules.get("cardiac_chest_pain_pattern") or {}
    required_terms = config.get("required_terms") or ["chest pain"]
    feature_terms = config.get("feature_terms") or []
    exclusion_terms = config.get("exclusion_terms") or []

    has_required = all(_keyword_matches(text, str(term)) for term in required_terms)
    features = _matched_terms(text, feature_terms)
    exclusions = _matched_terms(text, exclusion_terms)
    return bool(has_required and features and not exclusions), features, config


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
    # Mapped model phrases can expand synonyms or lose negation/context. Raw patient
    # text remains authoritative whenever it is available.
    raw_parts = [part.strip() for part in (symptoms or "", clinical_note or "") if part.strip()]
    text = normalize_clinical_text(". ".join(raw_parts or mapped_complaints or []))
    normalized_severity = str(severity).upper()
    active_flags = _active_red_flags(red_flags)
    prefer_specific = _routine_phrase_preferences_allowed(normalized_severity, active_flags, vitals)
    scores: dict[str, float] = {}
    matched_by_specialty: dict[str, list[str]] = {}
    clinical_hit_specialties: set[str] = set()
    review_reasons: list[str] = []
    pediatric = (rules.get("age_boosts") or {}).get("pediatric") or {}
    pediatric_cutoff = int(pediatric.get("age_lt", 12))
    pediatric_terms = ("child", "children", "paediatric", "pediatric", "infant", "toddler", "newborn")
    pediatric_context = any(_keyword_matches(text, term) for term in pediatric_terms)
    pediatric_eligible = age < pediatric_cutoff if age is not None else pediatric_context
    if age is not None and age >= pediatric_cutoff and pediatric_context:
        review_reasons.append("Patient age conflicts with pediatric wording; confirm whose symptoms are described.")
    elif age is None and pediatric_context:
        review_reasons.append("Pediatric wording found but patient age is missing; confirm age.")
    cardiac_pattern, cardiac_features, cardiac_config = _cardiac_chest_pain_pattern(text, rules)

    for rule in rules.get("rules") or []:
        specialty = rule["specialty"]
        if specialty == PEDIATRIC_LABEL and not pediatric_eligible:
            continue
        weight = float(rule.get("weight", 1.0))
        keyword_hits = _rule_keyword_hits(text, rule, rules, prefer_specific)
        for keyword in keyword_hits:
            _add_score(scores, matched_by_specialty, clinical_hit_specialties, specialty, weight, keyword)

        flag_hits = active_flags.intersection(set(rule.get("red_flags") or []))
        if flag_hits:
            for flag in sorted(flag_hits):
                flag_weight = float(rule.get("red_flag_weight", 1.0))
                related = set((rules.get("red_flag_keywords") or {}).get(flag, []))
                # A checkbox and the same symptom in prose are one observation.
                already_scored = weight if related.intersection(keyword_hits) else 0.0
                _add_score(scores, matched_by_specialty, clinical_hit_specialties, specialty, max(0.0, flag_weight - already_scored), flag)

    if cardiac_pattern:
        _add_score(
            scores,
            matched_by_specialty,
            clinical_hit_specialties,
            CARDIOVASCULAR_LABEL,
            float(cardiac_config.get("cardiovascular_boost", 0.0)),
            f"cardiac chest pain pattern: {', '.join(cardiac_features)}",
        )
        _add_score(
            scores,
            matched_by_specialty,
            clinical_hit_specialties,
            EMERGENCY_LABEL,
            float(cardiac_config.get("emergency_boost", 0.0)),
            "possible cardiac chest pain",
        )

    spo2 = _numeric_vital(vitals, "vital_spo2")
    sbp = _numeric_vital(vitals, "vital_sbp")
    hr = _numeric_vital(vitals, "vital_hr")
    if spo2 is not None and spo2 < SPO2_RESPIRATORY_BOOST_THRESHOLD:
        respiratory_spo2_boost = (
            float(cardiac_config.get("respiratory_spo2_boost", RESPIRATORY_VITAL_BOOST))
            if cardiac_pattern
            else RESPIRATORY_VITAL_BOOST
        )
        _add_score(
            scores,
            matched_by_specialty,
            clinical_hit_specialties,
            RESPIRATORY_LABEL,
            respiratory_spo2_boost,
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

    if fallback and normalized_severity != "CRITICAL":
        return {
            "primary": default_primary,
            "secondary": [GERIATRIC_LABEL] if scores.get(GERIATRIC_LABEL) else [],
            "matched_keywords": matched_by_specialty.get(GERIATRIC_LABEL, []),
            "confidence": 0.1,
            "reason": "No specific specialty keywords found",
            "fallback": True,
            "evidence": {GERIATRIC_LABEL: matched_by_specialty[GERIATRIC_LABEL]} if scores.get(GERIATRIC_LABEL) else {},
            "evidence_scores": {key: round(value, 2) for key, value in scores.items()},
            "review_reasons": review_reasons,
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
        if clinical_primary != emergency and scores.get(clinical_primary, 0.0) > 0:
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

    displayed = [primary, *secondary[:2]]
    evidence = {specialty: list(dict.fromkeys(matched_by_specialty.get(specialty, []))) for specialty in displayed}
    reason = f"{primary}: " + ", ".join(evidence.get(primary) or ["highest supported specialty score"])
    if str(severity).upper() == "CRITICAL" and primary == rules.get("critical_primary", "Emergency Medicine"):
        reason = "CRITICAL severity defaults advisory primary to Emergency Medicine"
        evidence[primary] = list(dict.fromkeys(["CRITICAL severity", *evidence[primary]]))
    elif primary == default_primary and clinical_primary != primary:
        reason = f"LOW severity uses General Practice for initial review; {clinical_primary} is supported by the listed evidence."

    if len(ranked) > 1 and non_geriatric_scores[ranked[0]] == non_geriatric_scores[ranked[1]]:
        review_reasons.append("Top specialty evidence scores are tied; review the recommendation.")

    return {
        "primary": primary,
        "secondary": secondary[:2],
        "matched_keywords": ordered_keywords[:8],
        "confidence": _confidence(top_score, total_score, False),
        "reason": reason,
        "fallback": False,
        "evidence": evidence,
        "evidence_scores": {key: round(value, 2) for key, value in scores.items()},
        "review_reasons": review_reasons,
    }
