from datetime import datetime, timedelta, timezone

from app.core.security import TokenPayload
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
