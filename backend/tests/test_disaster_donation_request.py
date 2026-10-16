from datetime import datetime, timezone

import pytest
from bson import ObjectId

from app.core.security import TokenPayload
from app.models.disaster_donation_request import (
    DisasterDonationRequestCreate,
    RequestItem,
)
from app.routers import disaster_officer


class _Cursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, *_args):
        return self

    async def to_list(self, length):
        return self.documents[:length]


class _Collection:
    def __init__(self, documents=None):
        self.documents = documents or []
        self.find_query = None
        self.inserted_document = None
        self.updates = []

    def find(self, query):
        self.find_query = query
        return _Cursor(self.documents)

    async def find_one(self, query):
        self.find_query = query
        return self.documents[0] if self.documents else None

    async def insert_one(self, document):
        self.inserted_document = document

        class _Result:
            inserted_id = ObjectId()

        return _Result()

    async def update_one(self, query, update):
        self.updates.append((query, update))


def _token(user_id="volunteer-7", role="volunteer"):
    return TokenPayload(
        sub=user_id,
        role=role,
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )


def test_needed_quantity_rounds_fractional_requirement_up():
    item = RequestItem(
        itemName="First Aid Kits",
        unit="kits",
        neededQuantity=3.4000000000000004,
    )

    assert item.neededQuantity == 4


def test_needed_quantity_keeps_whole_requirement_unchanged():
    item = RequestItem(
        itemName="Blankets",
        unit="blankets",
        neededQuantity=38,
    )

    assert item.neededQuantity == 38


def test_legacy_fractional_requirement_is_rounded_in_backend_response():
    request = disaster_officer.format_mongo_doc({
        "_id": "legacy-request",
        "items": [{
            "itemName": "First Aid Kits",
            "unit": "kits",
            "neededQuantity": 3.4000000000000004,
            "pledgedQuantity": 0,
            "donatedQuantity": 0,
        }],
        "donations": [],
    })

    assert request.items[0].neededQuantity == 4
    assert request.items[0].remainingQuantity == 4


@pytest.mark.asyncio
async def test_legacy_fractional_requirement_is_persisted_as_whole_units(monkeypatch):
    request_id = ObjectId()
    document = {
        "_id": request_id,
        "status": "remaining",
        "items": [{
            "itemName": "First Aid Kits",
            "unit": "kits",
            "neededQuantity": 3.4000000000000004,
            "pledgedQuantity": 0,
            "donatedQuantity": 0,
            "remainingQuantity": 3.4000000000000004,
            "status": "remaining",
        }],
    }
    collection = _Collection([document])
    monkeypatch.setattr(disaster_officer, "disaster_requests_collection", collection)

    await disaster_officer._persist_whole_required_quantities(document)

    assert document["items"][0]["neededQuantity"] == 4
    assert document["items"][0]["remainingQuantity"] == 4
    assert collection.updates == [(
        {"_id": request_id},
        {"$set": {"items": document["items"], "status": "remaining"}},
    )]


@pytest.mark.asyncio
async def test_volunteer_list_is_filtered_by_authenticated_creator(monkeypatch):
    collection = _Collection()
    monkeypatch.setattr(disaster_officer, "disaster_requests_collection", collection)

    async def _expire_none():
        return 0

    monkeypatch.setattr(disaster_officer, "expire_stale_pledges", _expire_none)

    result = await disaster_officer.get_all_disaster_requests(
        _current_user=_token(),
        db=None,
    )

    assert result == []
    assert collection.find_query == {"createdBy": "volunteer-7"}


@pytest.mark.asyncio
async def test_created_request_stores_authenticated_volunteer_id(monkeypatch):
    collection = _Collection()
    monkeypatch.setattr(disaster_officer, "disaster_requests_collection", collection)
    payload = DisasterDonationRequestCreate(
        disasterType="Flood",
        severity="High",
        dsArea="Kaduwela",
        gnDivision="Ranala",
        reliefCamp="Community Hall",
        people_count=10,
        items=[{
            "itemName": "Blankets",
            "unit": "blankets",
            "neededQuantity": 10,
        }],
    )

    created = await disaster_officer.create_disaster_request(
        payload=payload,
        token_payload=_token(),
    )

    assert collection.inserted_document["createdBy"] == "volunteer-7"
    assert created.createdBy == "volunteer-7"


@pytest.mark.asyncio
async def test_volunteer_detail_lookup_is_scoped_to_creator(monkeypatch):
    collection = _Collection()
    monkeypatch.setattr(disaster_officer, "disaster_requests_collection", collection)

    async def _expire_none():
        return 0

    monkeypatch.setattr(disaster_officer, "expire_stale_pledges", _expire_none)
    request_id = str(ObjectId())

    with pytest.raises(disaster_officer.HTTPException) as error:
        await disaster_officer.get_disaster_request(
            req_id=request_id,
            _current_user=_token(),
            db=None,
        )

    assert error.value.status_code == 404
    assert collection.find_query == {
        "_id": ObjectId(request_id),
        "createdBy": "volunteer-7",
    }
