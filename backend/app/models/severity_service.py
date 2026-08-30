from app.models.severity_ml_service import predict_severity_ml


SUPPORTED_MODES = {"rule_based", "ml"}


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

    # CRITICAL pre-check runs regardless of mode.
    # The ML model was trained on 3 classes (LOW/MEDIUM/HIGH) only.
    # Critical trigger detection is handled exclusively by the rule engine
    # and acts as a hard safety floor before the ML path is reached.
    rule_result = predict_severity(clinical_note, age=age)
    if rule_result["critical_trigger"] is not None:
        result = rule_result
    elif mode == "ml":
        result = predict_severity_ml(
            clinical_note=clinical_note,
            age=age,
            condition_group=condition_group,
            vitals=vitals,
            has_red_flag=has_red_flag,
            red_flag_count=red_flag_count,
            rf_flags=rf_flags,
            symptoms=symptoms,
        )
    else:
        result = rule_result

    normalized_scores = _normalize_scores(result["scores"])
    risk_score = _display_risk_score(result, normalized_scores)
    queue_policy = _build_queue_policy(
        result["severity"],
        risk_score,
        mode,
        result["matched_rules"],
        result["critical_trigger"],
        source=source,
    )
    return {
        "severity": result["severity"],
        "priority_score": result["priority_score"],
        "risk_score": risk_score,
        "method": mode,
        "scores": normalized_scores,
        "matched_rules": result["matched_rules"],
        "critical_trigger": result["critical_trigger"],
        **queue_policy,
    }
