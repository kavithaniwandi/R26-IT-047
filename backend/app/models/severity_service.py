from app.models.severity_ml_service import diagnose_complaint_mapping, predict_severity_ml_detailed
from app.models.config import settings
from app.models.specialty_service import suggest_specialty
from app.models.vitals_normalizer import ML_VITAL_KEYS, normalize_vitals_for_scoring


SUPPORTED_MODES = {"rule_based", "ml"}
MIN_VITALS_FOR_ML = 4
COMPLAINT_MAPPING_REVIEW_REASON = "complaint not recognised - review"
COMPLAINT_REASON_NO_MAPPING = "NO_MAPPING"
COMPLAINT_REASON_LOW_COVERAGE = "LOW_COVERAGE"
COMPLAINT_REASON_PARTIAL_MATCH = "PARTIAL_MATCH"
COMPLAINT_REASON_DANGER_TERM_UNMAPPED = "DANGER_TERM_UNMAPPED"
DANGER_TERM_REVIEW_REASON = "danger term unmapped - review"
SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
def _count_numeric_vitals(vitals: dict | None) -> int:
    normalized = normalize_vitals_for_scoring(vitals)
    return sum(1 for key in ML_VITAL_KEYS if normalized.get(key) is not None)


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {
            "CRITICAL": 0.0,
            "HIGH": 0.0,
            "MEDIUM": 0.0,
            "LOW": 1.0,
        }
    return {
        severity: round(score / total, 4)
        for severity, score in scores.items()
    }


def _compute_risk_score(normalized_scores: dict[str, float]) -> int:
    return round(
        100
        * (
            1.0 * normalized_scores["CRITICAL"]
            + 0.6 * normalized_scores["HIGH"]
            + 0.3 * normalized_scores["MEDIUM"]
            + 0.0 * normalized_scores["LOW"]
        )
    )


def _display_risk_score(result: dict, normalized_scores: dict[str, float]) -> int:
    priority_score = result.get("priority_score")
    if isinstance(priority_score, (int, float)):
        return round(max(0, min(100, priority_score)))

    return _compute_risk_score(normalized_scores)


def _floor_rule_result(result: dict, floor: str, reason: str) -> dict:
    floor = (floor or "MEDIUM").upper()
    if floor not in SEVERITY_RANK:
        floor = "MEDIUM"
    if SEVERITY_RANK[result["severity"]] >= SEVERITY_RANK[floor]:
        return result

    raised = dict(result)
    raised["severity"] = floor
    raised["priority_score"] = max(float(raised.get("priority_score", 0.0)), {"MEDIUM": 40.0, "HIGH": 60.0}.get(floor, 40.0))
    scores = dict(raised.get("scores") or {})
    scores[floor] = max(float(scores.get(floor, 0.0)), 1.0)
    raised["scores"] = scores
    matched = list(raised.get("matched_rules") or [])
    if reason not in matched:
        matched.append(reason)
    raised["matched_rules"] = matched
    return raised


def _append_reason(result: dict, reason: str) -> dict:
    updated = dict(result)
    matched = list(updated.get("matched_rules") or [])
    if reason not in matched:
        matched.append(reason)
    updated["matched_rules"] = matched
    return updated


def _complaint_reason_code(mapped_terms: list[str], unmapped_terms: list[str], coverage: float, threshold: float) -> str | None:
    if not mapped_terms:
        return COMPLAINT_REASON_NO_MAPPING
    if coverage < threshold:
        return COMPLAINT_REASON_LOW_COVERAGE
    if unmapped_terms:
        return COMPLAINT_REASON_PARTIAL_MATCH
    return None


def _coverage_below_threshold(coverage: float, threshold: float) -> bool:
    """Floor applies only when coverage < threshold; coverage == threshold does not floor."""
    return coverage < threshold


def _complaint_mapping_payload(
    result: dict,
    threshold: float,
    floor_applied: bool = False,
    floor_changed_result: bool = False,
    reason_code: str | None = None,
) -> dict:
    diagnostic = dict(result.get("mapping_diagnostic") or {})
    mapped_terms = list(diagnostic.get("mapped_terms") or result.get("mapped_complaints") or [])
    unmapped_terms = list(diagnostic.get("unmapped_terms") or [])
    coverage = float(diagnostic.get("coverage", result.get("mapping_confidence") or 0.0))
    return {
        "mapped_terms": mapped_terms,
        "unmapped_terms": unmapped_terms,
        "coverage": coverage,
        "threshold": threshold,
        "floor_applied": floor_applied,
        "floor_changed_result": floor_changed_result,
        "reason_code": reason_code or _complaint_reason_code(mapped_terms, unmapped_terms, coverage, threshold),
        "danger_terms": list(result.get("danger_terms") or []),
    }


def _complaint_coverage_mode() -> str:
    mode = str(getattr(settings, "COMPLAINT_COVERAGE_MODE", "legacy") or "legacy").lower()
    return "clinical" if mode == "clinical" else "legacy"


def _approved_synonyms_enabled() -> bool:
    return bool(getattr(settings, "COMPLAINT_APPROVED_SYNONYMS_ENABLED", False))


def _conditional_synonyms_enabled() -> list[str]:
    return list(getattr(settings, "COMPLAINT_CONDITIONAL_SYNONYMS_ENABLED", []) or [])


def _danger_term_floor_enabled() -> bool:
    return bool(getattr(settings, "COMPLAINT_DANGER_TERM_FLOOR_ENABLED", False))


def _age65_abnormal_vital_count(age: int | None, vitals: dict | None) -> int:
    if age is None or age < 65:
        return 0
    checks = (
        ("vital_spo2", lambda value: value < 94),
        ("vital_sbp", lambda value: value < 90),
        ("vital_hr", lambda value: value > 110),
        ("vital_rr", lambda value: value > 22),
    )
    count = 0
    for key, predicate in checks:
        value = normalize_vitals_for_scoring(vitals).get(key)
        if value is not None:
            count += int(predicate(value))
    return count


def apply_age65_abnormal_vitals_layer(result: dict, age: int | None, vitals: dict | None, enabled: bool | None = None) -> dict:
    if enabled is None:
        enabled = settings.ENABLE_AGE65_ABNORMAL_VITALS
    if not enabled:
        return result

    abnormal_count = _age65_abnormal_vital_count(age, vitals)
    if abnormal_count <= 0:
        return result

    floor = "HIGH" if abnormal_count >= 2 else "MEDIUM"
    return _floor_rule_result(result, floor, f"age65_abnormal_vitals:{abnormal_count}")


def _build_queue_policy(
    severity: str,
    risk_score: int,
    method: str,
    matched_rules: list[str],
    critical_trigger: str | None,
    source: str = "TRIAGE",
) -> dict:
    source = source.upper()

    if severity in {"CRITICAL", "HIGH"}:
        reason = "auto_triage"
        threshold = 80 if severity == "CRITICAL" else 50
        title = f"{severity} risk - {source} review"
        description = (
            f"Auto-triage assigned {severity} severity "
            f"(risk score {risk_score}). Meets prompt review threshold "
            f"for {source} cases."
        )
        reason_text = (
            f"Included: {severity} severity + risk {risk_score} >= "
            f"{threshold} ({source})."
        )
        action = "Review and confirm severity or escalate as needed."
        should_queue = True
    elif severity == "MEDIUM" and risk_score >= 40:
        reason = "auto_triage"
        threshold = 40
        title = f"MEDIUM risk - {source} review"
        description = (
            "Auto-triage assigned MEDIUM severity "
            f"(risk score {risk_score}). Meets review threshold "
            f"for {source} cases."
        )
        reason_text = (
            f"Included: MEDIUM severity + risk {risk_score} >= "
            f"{threshold} ({source})."
        )
        action = "Review and confirm severity within the standard workflow."
        should_queue = True
    elif severity == "LOW" and matched_rules:
        reason = "audit_sample"
        title = f"Triage audit - LOW {source} sample"
        description = (
            f"Audit sample from {source} stream. "
            f"Auto-classified as LOW (risk score {risk_score}). "
            "Verify classification and documentation quality."
        )
        reason_text = (
            f"Included: LOW severity audit sample with matched rule evidence "
            f"({source})."
        )
        action = "Verify classification as an audit/sample item."
        should_queue = True
    else:
        reason = "not_queued"
        title = "No priority queue item created"
        description = (
            f"Auto-triage assigned {severity} severity with risk score {risk_score}. "
            "Does not meet the threshold for queue inclusion."
        )
        reason_text = f"Excluded: {severity} severity + risk {risk_score} below threshold."
        action = "No queue action required."
        should_queue = False

    if critical_trigger:
        reason = "rule_flag"
        title = f"CRITICAL risk - {source} rule-flagged review"
        description = (
            f"Flagged by critical trigger: {critical_trigger}. "
            f"Auto-classified as CRITICAL (risk score {risk_score}). "
            "Review immediately for potential escalation."
        )
        reason_text = f"Included: critical trigger '{critical_trigger}' ({source})."
        action = "Review immediately for potential escalation."
        should_queue = True

    return {
        "should_queue": should_queue,
        "queue_reason": reason,
        "queue_title": title,
        "queue_description": description,
        "queue_reason_text": reason_text,
        "recommended_action": action,
        "display_note": _display_note(severity, risk_score, reason, source),
        "method": method,
    }


def _display_note(severity: str, risk_score: int, reason: str, source: str) -> str:
    if severity == "CRITICAL":
        return f"Risk score {risk_score} / 100 - Immediate medical review required."
    if severity == "HIGH":
        return f"Risk score {risk_score} / 100 - Prompt clinical review required."
    if severity == "MEDIUM":
        return f"Risk score {risk_score} / 100 - Standard clinical review workflow."
    if reason == "audit_sample":
        return f"Risk score {risk_score} / 100 - Audit sample, verify classification."
    return f"Risk score {risk_score} / 100 - No queue action required."


def classify_note(
    clinical_note: str,
    age: int | None = None,
    mode: str = "rule_based",
    source: str = "TRIAGE",
    condition_group: str = "Unknown",
    vitals: dict | None = None,
    has_red_flag: int = 0,
    red_flag_count: int = 0,
    rf_flags: dict | None = None,
    symptoms: str = "",
) -> dict:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported severity classification mode: {mode}")

    from app.models.severity_rules import predict_severity

    normalized_vitals = normalize_vitals_for_scoring(vitals)
    scoring_vitals = normalized_vitals.values
    vitals_warnings = normalized_vitals.warnings
    numeric_vital_count = normalized_vitals.count_for_ml()
    incomplete_vitals = numeric_vital_count < MIN_VITALS_FOR_ML
    incomplete_reason = "incomplete vitals — review"

    # CRITICAL pre-check runs regardless of mode.
    # The ML model was trained on 3 classes (LOW/MEDIUM/HIGH) only.
    # Critical trigger detection is handled exclusively by the rule engine
    # and acts as a hard safety floor before the ML path is reached.
    rule_result = predict_severity(clinical_note, age=age)
    effective_method = mode
    ml_skipped_reason = None
    mapping_probe = (
        diagnose_complaint_mapping(
            symptoms=symptoms,
            clinical_note=clinical_note,
            coverage_mode=_complaint_coverage_mode(),
            approved_synonyms=_approved_synonyms_enabled(),
            conditional_synonyms=_conditional_synonyms_enabled(),
        )
        if mode == "ml"
        else {}
    )
    complaint_mapping = _complaint_mapping_payload(
        mapping_probe,
        settings.COMPLAINT_MAPPING_COVERAGE_THRESHOLD,
    )
    if rule_result["critical_trigger"] is not None:
        result = rule_result
    elif mode == "ml":
        if incomplete_vitals:
            result = dict(rule_result)
            result = _floor_rule_result(result, settings.INCOMPLETE_VITALS_FLOOR, incomplete_reason)
            result["method"] = "rule_based"
            result["ml_skipped_reason"] = "insufficient_vitals"
            effective_method = "rule_based"
            ml_skipped_reason = "insufficient_vitals"
        else:
            result = predict_severity_ml_detailed(
                clinical_note=clinical_note,
                age=age,
                condition_group=condition_group,
                vitals=scoring_vitals,
                has_red_flag=has_red_flag,
                red_flag_count=red_flag_count,
                rf_flags=rf_flags,
                symptoms=symptoms,
                coverage_mode=_complaint_coverage_mode(),
                approved_synonyms=_approved_synonyms_enabled(),
                conditional_synonyms=_conditional_synonyms_enabled(),
            )
            mapping_confidence = float(result.get("mapping_confidence") or 0.0)
            mapped_complaints = result.get("mapped_complaints") or []
            base_complaint_mapping = _complaint_mapping_payload(
                result,
                settings.COMPLAINT_MAPPING_COVERAGE_THRESHOLD,
            )
            danger_terms = list(result.get("danger_terms") or [])
            danger_floor = _danger_term_floor_enabled() and bool(danger_terms)
            low_mapping_coverage = (
                not mapped_complaints
                or _coverage_below_threshold(
                    mapping_confidence,
                    settings.COMPLAINT_MAPPING_COVERAGE_THRESHOLD,
                )
            )
            if danger_floor or low_mapping_coverage:
                reason = DANGER_TERM_REVIEW_REASON if danger_floor else COMPLAINT_MAPPING_REVIEW_REASON
                reason_code = COMPLAINT_REASON_DANGER_TERM_UNMAPPED if danger_floor else None
                floor_changed_result = (
                    SEVERITY_RANK[result["severity"]]
                    < SEVERITY_RANK.get(settings.COMPLAINT_MAPPING_FLOOR.upper(), SEVERITY_RANK["MEDIUM"])
                )
                result = _floor_rule_result(result, settings.COMPLAINT_MAPPING_FLOOR, reason)
                result = _append_reason(result, reason)
                result["mapped"] = False
                result["mapping_review_reason"] = reason
                complaint_mapping = {
                    **base_complaint_mapping,
                    "floor_applied": True,
                    "floor_changed_result": floor_changed_result,
                    "reason_code": reason_code or base_complaint_mapping["reason_code"],
                    "danger_terms": danger_terms,
                }
            else:
                complaint_mapping = base_complaint_mapping
    else:
        result = rule_result

    danger_terms = list(mapping_probe.get("danger_terms") or result.get("danger_terms") or [])
    if mode == "ml" and _danger_term_floor_enabled() and danger_terms:
        floor_changed_result = (
            SEVERITY_RANK[result["severity"]]
            < SEVERITY_RANK.get(settings.COMPLAINT_MAPPING_FLOOR.upper(), SEVERITY_RANK["MEDIUM"])
        )
        result = _floor_rule_result(result, settings.COMPLAINT_MAPPING_FLOOR, DANGER_TERM_REVIEW_REASON)
        result = _append_reason(result, DANGER_TERM_REVIEW_REASON)
        result["mapping_review_reason"] = DANGER_TERM_REVIEW_REASON
        complaint_mapping = {
            **complaint_mapping,
            "floor_applied": True,
            "floor_changed_result": floor_changed_result,
            "reason_code": COMPLAINT_REASON_DANGER_TERM_UNMAPPED,
            "danger_terms": danger_terms,
        }

    result = apply_age65_abnormal_vitals_layer(result, age, scoring_vitals)

    normalized_scores = _normalize_scores(result["scores"])
    risk_score = _display_risk_score(result, normalized_scores)
    queue_policy = _build_queue_policy(
        result["severity"],
        risk_score,
        effective_method,
        result["matched_rules"],
        result["critical_trigger"],
        source=source,
    )
    red_flag_payload = dict(rf_flags or {})
    if has_red_flag and not red_flag_payload:
        red_flag_payload["has_red_flag"] = 1
    suggested_specialty = suggest_specialty(
        symptoms=symptoms,
        clinical_note=clinical_note,
        red_flags=red_flag_payload,
        age=age,
        severity=result["severity"],
        mapped_complaints=result.get("mapped_complaints", []),
        vitals=scoring_vitals,
    )
    return {
        "severity": result["severity"],
        "priority_score": result["priority_score"],
        "risk_score": risk_score,
        "method": effective_method,
        "ml_skipped_reason": ml_skipped_reason,
        "scores": normalized_scores,
        "matched_rules": result["matched_rules"],
        "critical_trigger": result["critical_trigger"],
        "incomplete_vitals": incomplete_vitals,
        "incomplete_vitals_reason": incomplete_reason if incomplete_vitals else None,
        "vitals_warnings": vitals_warnings,
        "can_override": result["critical_trigger"] is None,
        "mapped_complaints": result.get("mapped_complaints", []),
        "high_acuity_terms": result.get("high_acuity_terms", []),
        "model_symptoms": result.get("model_symptoms"),
        "original_symptoms_text": result.get("original_symptoms_text"),
        "interpreted_as": {
            "mapped_phrases": result.get("mapped_complaints", []),
            "high_acuity_terms": result.get("high_acuity_terms", []),
        },
        "mapped": bool(result.get("mapped", result.get("mapped_complaints") or result.get("high_acuity_terms"))),
        "mapping_confidence": float(result.get("mapping_confidence", 1.0 if result.get("mapped_complaints") or result.get("high_acuity_terms") else 0.0)),
        "mapping_review_reason": result.get("mapping_review_reason"),
        "complaint_mapping": complaint_mapping,
        "suggested_specialty": suggested_specialty,
        **queue_policy,
    }
