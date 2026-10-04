"""
MongoDB logging service for donation appeal workflows.

Stores generated appeal payloads and analysis events in MongoDB Atlas when
MONGODB_URI is configured. Failures are logged and do not block API responses.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from app.core.config import settings

try:
    import motor.motor_asyncio
except Exception:  # pragma: no cover - allows app startup before motor install
    motor = None
else:
    motor = motor.motor_asyncio


_client: Any = None
_db: Any = None
logger = logging.getLogger(__name__)
_component_client: Any = None
_component_db: Any = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def connect_mongo() -> None:
    """Register MongoDB availability without blocking SQL app startup."""
    if not settings.MONGODB_URI:
        print("MongoDB component disabled: MONGODB_URI is not configured")
    elif motor is None:
        print("MongoDB component disabled: motor is not installed")
    else:
        print(f"MongoDB component configured: {settings.MONGODB_DB_NAME}")


def get_mongo_collection(name: str):
    """Return a lazily-created collection for the individual component."""
    global _client, _db

    if not settings.MONGODB_URI:
        raise RuntimeError("MongoDB is not configured. Set MONGODB_URI in backend/.env.")
    if motor is None:
        raise RuntimeError("MongoDB support requires the 'motor' package.")
    if _client is None:
        _client = motor.AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _db = _client[settings.MONGODB_DB_NAME]
    return _db[name]


def get_component_mongo_collection(name: str):
    """Return a collection from the isolated component database.

    A separate URI/database can be configured without replacing the research
    project's Mongo connection. If it is not configured, the component uses
    the main Mongo database for backwards compatibility.
    """
    global _component_client, _component_db

    uri = settings.COMPONENT_MONGODB_URI or settings.MONGODB_URI
    database_name = settings.COMPONENT_MONGODB_DB_NAME or settings.MONGODB_DB_NAME
    if not uri:
        raise RuntimeError(
            "MongoDB is not configured. Set COMPONENT_MONGODB_URI or MONGODB_URI in backend/.env."
        )
    if motor is None:
        raise RuntimeError("MongoDB support requires the 'motor' package.")
    if settings.COMPONENT_MONGODB_URI is None:
        return get_mongo_collection(name)
    if _component_client is None:
        _component_client = motor.AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _component_db = _component_client[database_name]
    return _component_db[name]


async def close_mongo() -> None:
    """Close the shared MongoDB client on app shutdown."""
    global _client, _db, _component_client, _component_db

    if _client is not None:
        _client.close()
    _client = None
    _db = None
    if _component_client is not None:
        _component_client.close()
    _component_client = None
    _component_db = None


async def log_appeal_generation(
    campaign_data: dict[str, Any],
    variants: list[dict[str, Any]],
) -> None:
    """Store one generation event in the appeal_generations collection."""
    if not settings.MONGODB_URI or motor is None:
        return

    collection = get_mongo_collection("appeal_generations")

    best_variant = max(
        variants,
        key=lambda item: float(item.get("quality_score") or 0),
        default={},
    )
    document = {
        "timestamp": _utc_now(),
        "language": campaign_data.get("language"),
        "campaign_type": campaign_data.get("campaign_type"),
        "location": campaign_data.get("location"),
        "verified_need": campaign_data.get("verified_need"),
        "campaign_goal": campaign_data.get("campaign_goal"),
        "tone": campaign_data.get("tone"),
        "channel": campaign_data.get("channel"),
        "length_category": campaign_data.get("length_category"),
        "best_score": best_variant.get("quality_score"),
        "best_label": best_variant.get("quality_label"),
        "best_provider": best_variant.get("provider"),
        "variants": variants,
    }
    await collection.insert_one(document)


async def log_appeal_analysis(
    appeal_text: str,
    language: str,
    result: dict[str, Any],
    *,
    event_type: str = "analysis",
    source: str | None = None,
) -> None:
    """Log one appeal quality scoring event to MongoDB."""
    try:
        if _db is None:
            return

        quality_label = (
            result.get("quality_label")
            or result.get("status")
            or result.get("label")
            or result.get("improved_label")
        )
        quality_score = (
            result.get("quality_score")
            or result.get("score")
            or result.get("improved_score")
        )
        confidence = result.get("confidence")
        if confidence is None:
            confidence = result.get("improved_confidence", 0.0)

        document = {
            "appeal_text": (appeal_text or "")[:1_000],
            "language": language,
            "quality_label": quality_label,
            "quality_score": quality_score,
            "confidence": confidence,
            "low_confidence": result.get("low_confidence", False),
            "method": result.get("method", "unknown"),
            "source": source or event_type,
            "event_type": event_type,
            "char_count": len(appeal_text or ""),
            "word_count": len((appeal_text or "").split()),
            "timestamp": _utc_now(),
            "issues": result.get("issues"),
            "result": result,
        }
        await _db.appeal_analysis_logs.insert_one(document)
    except Exception as exc:
        logger.warning("Failed to log appeal analysis to MongoDB: %s", exc)


async def save_triage_session(session_data: dict[str, Any]) -> str | None:
    """Create a new triage session document in triage_sessions."""
    if _db is None:
        return None

    try:
        document = {
            "session_id": session_data.get("session_id"),
            "started_at": _utc_now(),
            "camp": session_data.get("camp"),
            "mos": session_data.get("mos", []),
            "status": "active",
        }
        result = await _db.triage_sessions.insert_one(document)
        return str(result.inserted_id)
    except Exception as exc:
        print(f"[mongo] save_triage_session failed: {exc}")
        return None


async def save_triage_patient(patient_data: dict[str, Any]) -> str | None:
    """Store one patient classification record in triage_patients."""
    if _db is None:
        return None

    try:
        document = {
            "session_id": patient_data.get("session_id"),
            "patient_id": patient_data.get("id"),
            "submitted_at": patient_data.get("submittedAt", _utc_now()),
            "camp": patient_data.get("camp"),
            "severity": patient_data.get("severity"),
            "ai_severity": patient_data.get("ai_severity"),
            "risk_score": patient_data.get("risk_score"),
            "priority_score": patient_data.get("priority_score"),
            "method": patient_data.get("method"),
            "symptoms": patient_data.get("symptoms"),
            "age": patient_data.get("age"),
            "red_flags": patient_data.get("red_flags", []),
            "condition_group": patient_data.get("condition_group"),
            "specialty": patient_data.get("specialty"),
            "extracted_symptoms": patient_data.get("extracted_symptoms", []),
            "assigned_mo_id": patient_data.get("assigned_mo_id"),
            "assigned_mo_name": patient_data.get("assigned_mo_name"),
            "queue_reason": patient_data.get("queue_reason"),
            "queue_reason_text": patient_data.get("queue_reason_text"),
            "source": patient_data.get("source"),
            "clinician_override": patient_data.get("clinician_override"),
            "critical_trigger": patient_data.get("critical_trigger"),
            "matched_rules": patient_data.get("matched_rules", []),
            "display_note": patient_data.get("display_note"),
            "recommended_action": patient_data.get("recommended_action"),
        }
        result = await _db.triage_patients.insert_one(document)
        return str(result.inserted_id)
    except Exception as exc:
        print(f"[mongo] save_triage_patient failed: {exc}")
        return None


async def archive_triage_session(
    session_id: str,
    session_data: dict[str, Any],
    patients: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str | None:
    """Archive a completed triage session and mark the active session ended."""
    if _db is None:
        return None

    try:
        ended_at = _utc_now()
        document = {
            "session_id": session_id,
            "camp": session_data.get("camp"),
            "mos": session_data.get("mos", []),
            "started_at": session_data.get("started_at") or session_data.get("startedAt"),
            "ended_at": ended_at,
            "patients": patients,
            "summary": summary,
        }
        result = await _db.triage_archives.insert_one(document)

        await _db.triage_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "ended", "ended_at": ended_at}},
        )

        return str(result.inserted_id)
    except Exception as exc:
        print(f"[mongo] archive_triage_session failed: {exc}")
        return None
    """Store one analysis/improvement event in appeal_analysis_logs."""
    if not settings.MONGODB_URI or motor is None:
        return

    collection = get_mongo_collection("appeal_analysis_logs")

    document = {
        "timestamp": _utc_now(),
        "event_type": event_type,
        "language": language,
        "appeal_text": appeal_text,
        "score": result.get("score") or result.get("improved_score"),
        "label": result.get("label") or result.get("improved_label"),
        "confidence": result.get("confidence") or result.get("improved_confidence"),
        "method": result.get("method"),
        "issues": result.get("issues"),
        "result": result,
    }
    await collection.insert_one(document)
