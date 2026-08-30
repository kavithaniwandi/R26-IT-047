import json
import os
from datetime import datetime


FEEDBACK_LOG_PATH = os.environ.get("FEEDBACK_LOG_PATH", "feedback_log.jsonl")


def log_generation_event(
    appeal_text: str,
    language: str,
    quality_score: float,
    quality_label: str,
    confidence: float,
    confidence_normalised: float | None = None,
    confidence_display: str | None = None,
    style: str | None = None,
    was_copied: bool = False,
    was_edited: bool = False,
    edited_text: str | None = None,
) -> None:
    """
    Log generation and user interaction signals for future model improvement.
    Each line is one self-contained JSON record.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "language": language,
        "style": style,
        "appeal_text": appeal_text,
        "quality_score": quality_score,
        "quality_label": quality_label,
        "confidence": confidence,
        "confidence_normalised": confidence_normalised,
        "confidence_display": confidence_display,
        "was_copied": was_copied,
        "was_edited": was_edited,
        "edited_text": edited_text,
    }
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_copy_event(
    appeal_text: str,
    language: str,
    quality_score: float,
    quality_label: str,
    confidence: float,
    confidence_normalised: float | None = None,
    confidence_display: str | None = None,
    style: str | None = None,
) -> None:
    log_generation_event(
        appeal_text=appeal_text,
        language=language,
        quality_score=quality_score,
        quality_label=quality_label,
        confidence=confidence,
        confidence_normalised=confidence_normalised,
        confidence_display=confidence_display,
        style=style,
        was_copied=True,
    )


def log_edit_event(
    original_text: str,
    edited_text: str,
    language: str,
    quality_score: float,
    quality_label: str,
    confidence: float,
    confidence_normalised: float | None = None,
    confidence_display: str | None = None,
    style: str | None = None,
) -> None:
    log_generation_event(
        appeal_text=original_text,
        language=language,
        quality_score=quality_score,
        quality_label=quality_label,
        confidence=confidence,
        confidence_normalised=confidence_normalised,
        confidence_display=confidence_display,
        style=style,
        was_copied=True,
        was_edited=True,
        edited_text=edited_text,
    )
