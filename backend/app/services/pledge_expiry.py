"""Expire overdue donor pledges and release their reserved quantities."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.database import disaster_requests_collection
from app.models.disaster_donation_request import whole_required_quantity


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def expire_stale_pledges() -> int:
    """Cancel elapsed 12-hour pledges when donation data is next accessed."""
    now = datetime.now(timezone.utc)
    cursor = disaster_requests_collection.find({
        "donations": {
            "$elemMatch": {
                "status": "pledged",
                "expiresAt": {"$lte": now},
            }
        }
    })
    documents = await cursor.to_list(length=500)
    expired_count = 0

    for document in documents:
        items = document.get("items", [])
        donations = document.get("donations", [])
        changed = False

        for donation in donations:
            expires_at = _as_utc(donation.get("expiresAt"))
            if donation.get("status") != "pledged" or not expires_at or expires_at > now:
                continue

            donation["status"] = "cancelled"
            donation["cancelledAt"] = now
            donation["cancellationReason"] = "Pledge expired after 12 hours"
            expired_count += 1
            changed = True

            for item in items:
                same_id = donation.get("itemId") and item.get("itemId") == donation.get("itemId")
                same_name = item.get("itemName", "").casefold() == donation.get("itemName", "").casefold()
                if not (same_id or same_name):
                    continue
                released = float(donation.get("quantity", 0))
                item["pledgedQuantity"] = max(0.0, float(item.get("pledgedQuantity", 0)) - released)
                item["remainingQuantity"] = max(
                    0.0,
                    float(whole_required_quantity(item.get("neededQuantity", 0)))
                    - float(item.get("donatedQuantity", 0))
                    - float(item.get("pledgedQuantity", 0)),
                )
                if item["remainingQuantity"] > 0:
                    item["status"] = "remaining"
                break

        if changed:
            request_status = (
                "fulfilled"
                if items and all(item.get("status") == "fulfilled" for item in items)
                else "remaining"
            )
            await disaster_requests_collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"donations": donations, "items": items, "status": request_status}},
            )

    return expired_count


async def pledge_expiry_worker(interval_seconds: int = 60) -> None:
    """Continuously expire overdue pledges while the API process is running."""
    while True:
        try:
            await expire_stale_pledges()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - resilience for transient Mongo outages
            print(f"Pledge expiry sweep failed: {exc}")
        await asyncio.sleep(interval_seconds)
