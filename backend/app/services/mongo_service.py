"""
MongoDB logging service for donation appeal workflows.

Stores generated appeal payloads and analysis events in MongoDB Atlas when
MONGODB_URI is configured. Failures are logged and do not block API responses.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from app.models.config import settings

try:
    import motor.motor_asyncio
except Exception:  # pragma: no cover - allows app startup before motor install
    motor = None
else:
    motor = motor.motor_asyncio


_client: Any = None
_db: Any = None
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def connect_mongo() -> None:
    """Create one shared MongoDB client and verify the connection."""
    global _client, _db

    if not settings.MONGODB_URI:
        print("MongoDB skipped: MONGODB_URI is not configured")
        return

    if motor is None:
        print("MongoDB skipped: motor is not installed")
        return

    _client = motor.AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client[settings.MONGODB_DB_NAME]
    await _client.admin.command("ping")
    print(f"MongoDB connected: {settings.MONGODB_DB_NAME}")


async def close_mongo() -> None:
    """Close the shared MongoDB client on app shutdown."""
    global _client, _db

    if _client is not None:
        _client.close()
    _client = None
    _db = None


async def log_appeal_generation(
    campaign_data: dict[str, Any],
    variants: list[dict[str, Any]],
) -> None:
    """Store one generation event in the appeal_generations collection."""
    if _db is None:
        return

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
    await _db.appeal_generations.insert_one(document)


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


async def get_triage_stats(camp_id: str | None = None) -> dict:
    """Aggregate analytics over archived triage sessions (triage_archives)."""
    if _db is None:
        return {"camps": [], "patients": {}}

    match = {"camp.id": camp_id} if camp_id else {}

    # 1) Session/camp level
    camp_pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$camp.id",
                "camp_name": {"$first": "$camp.name"},
                "district": {"$first": "$camp.district"},
                "sessions": {"$sum": 1},
                "patients": {"$sum": "$summary.total"},
                "CRITICAL": {"$sum": {"$ifNull": ["$summary.CRITICAL", 0]}},
                "HIGH": {"$sum": {"$ifNull": ["$summary.HIGH", 0]}},
                "MEDIUM": {"$sum": {"$ifNull": ["$summary.MEDIUM", 0]}},
                "LOW": {"$sum": {"$ifNull": ["$summary.LOW", 0]}},
                "avg_session_minutes": {
                    "$avg": {
                        "$divide": [
                            {
                                "$subtract": [
                                    {"$toDate": "$ended_at"},
                                    {"$toDate": "$started_at"},
                                ]
                            },
                            60000,
                        ]
                    }
                },
            }
        },
        {"$sort": {"patients": -1}},
    ]

    # 2) Patient level
    patient_pipeline = [
        {"$match": match},
        {"$unwind": "$patients"},
        {"$replaceRoot": {"newRoot": "$patients"}},
        {
            "$facet": {
                "flags": [
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": 1},
                            "avg_risk_score": {"$avg": "$risk_score"},
                            "critical_by_trigger": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$and": [
                                                {"$eq": ["$severity", "CRITICAL"]},
                                                {
                                                    "$ne": [
                                                        {
                                                            "$ifNull": [
                                                                "$critical_trigger",
                                                                None,
                                                            ]
                                                        },
                                                        None,
                                                    ]
                                                },
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "critical_by_keywords": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$and": [
                                                {"$eq": ["$severity", "CRITICAL"]},
                                                {
                                                    "$eq": [
                                                        {
                                                            "$ifNull": [
                                                                "$critical_trigger",
                                                                None,
                                                            ]
                                                        },
                                                        None,
                                                    ]
                                                },
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "clinician_overridden": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$ne": [
                                                {"$ifNull": ["$clinician_override", None]},
                                                None,
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "rule_matched": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$gt": [
                                                {
                                                    "$size": {
                                                        "$ifNull": [
                                                            "$matched_rules",
                                                            [],
                                                        ]
                                                    }
                                                },
                                                0,
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                        }
                    }
                ],
                "override_direction": [
                    {"$match": {"$expr": {"$ne": ["$severity", "$ai_severity"]}}},
                    {
                        "$addFields": {
                            "_delta": {
                                "$subtract": [
                                    {
                                        "$indexOfArray": [
                                            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                                            "$severity",
                                        ]
                                    },
                                    {
                                        "$indexOfArray": [
                                            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                                            "$ai_severity",
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$cond": [
                                    {"$gt": ["$_delta", 0]},
                                    "escalated",
                                    "de_escalated",
                                ]
                            },
                            "n": {"$sum": 1},
                        }
                    },
                ],
                "model_vs_final": [
                    {
                        "$group": {
                            "_id": {"ai": "$ai_severity", "final": "$severity"},
                            "n": {"$sum": 1},
                        }
                    },
                ],
                "by_condition": [
                    {
                        "$group": {
                            "_id": "$condition_group",
                            "n": {"$sum": 1},
                            "avg_risk": {"$avg": "$risk_score"},
                        }
                    },
                    {"$sort": {"n": -1}},
                ],
                "by_method": [
                    {"$group": {"_id": "$method", "n": {"$sum": 1}}},
                ],
                "top_red_flags": [
                    {
                        "$unwind": {
                            "path": "$red_flags",
                            "preserveNullAndEmptyArrays": False,
                        }
                    },
                    {"$group": {"_id": "$red_flags", "n": {"$sum": 1}}},
                    {"$sort": {"n": -1}},
                    {"$limit": 10},
                ],
                "top_rules": [
                    {
                        "$unwind": {
                            "path": "$matched_rules",
                            "preserveNullAndEmptyArrays": False,
                        }
                    },
                    {"$group": {"_id": "$matched_rules", "n": {"$sum": 1}}},
                    {"$sort": {"n": -1}},
                    {"$limit": 10},
                ],
            }
        },
    ]

    camps = await _db.triage_archives.aggregate(camp_pipeline).to_list(None)
    patients = await _db.triage_archives.aggregate(patient_pipeline).to_list(None)
    return {"camps": camps, "patients": patients[0] if patients else {}}
