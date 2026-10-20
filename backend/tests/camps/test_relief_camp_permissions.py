from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.core.security import TokenPayload
from app.models.relief_camp import AssignVolunteersPayload
from app.routers import relief_camps


def volunteer_token(user_id: str = "7") -> TokenPayload:
    return TokenPayload(
        sub=user_id,
        role="volunteer",
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    )


def test_volunteer_can_manage_camp_assigned_to_legacy_account(monkeypatch):
    monkeypatch.setattr(
        relief_camps,
        "volunteer_identity_ids",
        lambda _current_user, _db: ["7", "11"],
    )

    assert relief_camps.can_manage_camp(
        volunteer_token(),
        {"assignedVolunteerIds": ["11"]},
        db=object(),
    )


def test_volunteer_cannot_manage_unassigned_camp(monkeypatch):
    monkeypatch.setattr(
        relief_camps,
        "volunteer_identity_ids",
        lambda _current_user, _db: ["7", "11"],
    )

    assert not relief_camps.can_manage_camp(
        volunteer_token(),
        {"assignedVolunteerIds": ["12"]},
        db=object(),
    )


def test_admin_can_manage_any_camp():
    token = volunteer_token()
    token.role = "admin"

    assert relief_camps.can_manage_camp(
        token,
        {"assignedVolunteerIds": []},
        db=object(),
    )


@pytest.mark.parametrize("ids", [[5], ["5"], [5, "6"]])
@pytest.mark.asyncio
async def test_assignment_normalizes_ids_before_storage(monkeypatch, ids):
    now = datetime.now(timezone.utc)
    collection = SimpleNamespace(find_one_and_update=AsyncMock(return_value={
        "_id": "000000000000000000000001",
        "assignedVolunteerIds": [str(identifier) for identifier in ids],
        "lastUpdated": now,
    }))
    monkeypatch.setattr(relief_camps, "relief_camp_collection", collection)
    token = volunteer_token()
    token.role = "admin"
    payload = AssignVolunteersPayload(volunteerIds=ids)

    result = await relief_camps.assign_volunteers_to_camp(
        "000000000000000000000001", payload, token,
    )

    expected = [str(identifier) for identifier in ids]
    assert payload.volunteerIds == expected
    assert collection.find_one_and_update.await_args.args[1]["$set"]["assignedVolunteerIds"] == expected
    assert result.assignedVolunteerIds == expected


@pytest.mark.parametrize("invalid_id", [None, True, 5.5, {}])
def test_assignment_rejects_other_id_types(invalid_id):
    with pytest.raises(ValidationError):
        AssignVolunteersPayload(volunteerIds=[invalid_id])
