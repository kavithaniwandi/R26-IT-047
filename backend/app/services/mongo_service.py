"""
MongoDB logging service for donation appeal workflows.

Stores generated appeal payloads and analysis events in MongoDB Atlas when
MONGODB_URI is configured. Failures are logged and do not block API responses.
"""
from __future__ import annotations

from datetime import datetime, timezone
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
) -> None:
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
