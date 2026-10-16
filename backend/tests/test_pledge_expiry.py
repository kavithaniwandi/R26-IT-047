from datetime import datetime, timedelta, timezone

import pytest

from app.routers.disaster_officer import format_mongo_doc
from app.services import pledge_expiry


class _Cursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length):
        return self.documents[:length]


class _Collection:
    def __init__(self, documents):
        self.documents = documents
        self.updates = []

    def find(self, _query):
        return _Cursor(self.documents)

    async def update_one(self, query, update):
        self.updates.append((query, update))


@pytest.mark.asyncio
async def test_expired_pledge_is_cancelled_and_quantity_released(monkeypatch):
    now = datetime.now(timezone.utc)
    document = {
        "_id": "request-1",
        "status": "remaining",
        "items": [{
            "itemId": "water",
            "itemName": "Water",
            "neededQuantity": 50,
            "pledgedQuantity": 20,
            "donatedQuantity": 10,
            "remainingQuantity": 20,
            "status": "remaining",
        }],
        "donations": [{
            "donationId": "donation-1",
            "itemId": "water",
            "itemName": "Water",
            "quantity": 20,
            "status": "pledged",
            "expiresAt": now - timedelta(minutes=1),
        }],
    }
    collection = _Collection([document])
    monkeypatch.setattr(pledge_expiry, "disaster_requests_collection", collection)

    expired = await pledge_expiry.expire_stale_pledges()

    assert expired == 1
    assert document["donations"][0]["status"] == "cancelled"
    assert document["items"][0]["pledgedQuantity"] == 0
    assert document["items"][0]["remainingQuantity"] == 40
    assert len(collection.updates) == 1


@pytest.mark.asyncio
async def test_active_pledge_is_not_changed(monkeypatch):
    document = {
        "_id": "request-2",
        "items": [],
        "donations": [{
            "donationId": "donation-2",
            "status": "pledged",
            "expiresAt": datetime.now(timezone.utc) + timedelta(hours=1),
        }],
    }
    collection = _Collection([document])
    monkeypatch.setattr(pledge_expiry, "disaster_requests_collection", collection)

    expired = await pledge_expiry.expire_stale_pledges()

    assert expired == 0
    assert document["donations"][0]["status"] == "pledged"
    assert collection.updates == []


def test_request_remaining_quantity_excludes_active_pledges():
    request = format_mongo_doc({
        "_id": "request-3",
        "items": [{
            "itemId": "food",
            "itemName": "Food Packs",
            "unit": "packs",
            "neededQuantity": 50,
            "pledgedQuantity": 12,
            "donatedQuantity": 8,
            "status": "remaining",
        }],
        "donations": [],
    })

    assert request.items[0].remainingQuantity == 30
