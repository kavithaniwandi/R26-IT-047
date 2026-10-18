"""
tests/test_textlk_sms.py
------------------------
Unit and integration tests for the Text.lk SMS gateway integration.

These tests run entirely with TEXTLK_ENABLED=false (simulation mode).
No real HTTP requests are made to the Text.lk API; no SMS units are consumed.

Coverage:
  - _dispatch_textlk() simulation path (disabled integration)
  - _dispatch_textlk() with missing API token
  - _dispatch_textlk() with invalid phone number
  - _dispatch_sms() routing: Text.lk takes priority when enabled
  - send_direct_sms() logs a simulated record when Text.lk disabled
  - POST /sos/alert-contacts: empty contacts list rejected (400)
  - POST /sos/alert-contacts: single contact dispatched (200, simulated)
  - GET  /sms/gateway-status: reports TEXTLK status fields
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.sos import SOSRequest
from app.models.sms_log import SMSMessageLog
from app.core.security import create_access_token
from app.services.auth import _hash_password
from app.services import sms_gateway
from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_victim_user(db: Session, email: str = "victim_tlk@test.lk") -> tuple[User, str]:
    role = db.query(Role).filter(Role.name == RoleEnum.victim).first()
    user = User(
        full_name="Textlk Test Victim",
        email=email,
        hashed_password=_hash_password("Pass1234!"),
        phone="+94770001111",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, role=RoleEnum.victim.value)
    return user, token


def _create_admin_user(db: Session, email: str = "admin_tlk@test.lk") -> tuple[User, str]:
    role = db.query(Role).filter(Role.name == RoleEnum.admin).first()
    user = User(
        full_name="Textlk Test Admin",
        email=email,
        hashed_password=_hash_password("Pass1234!"),
        phone="+94770002222",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, role=RoleEnum.admin.value)
    return user, token


def _create_user_by_role(db: Session, email: str, role_name: RoleEnum) -> tuple[User, str]:
    role = db.query(Role).filter(Role.name == role_name).first()
    user = User(
        full_name=f"Textlk {role_name.value.title()}",
        email=email,
        hashed_password=_hash_password("Pass1234!"),
        phone="+94770009999",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, role=role_name.value)
    return user, token



# ---------------------------------------------------------------------------
# Unit tests for _dispatch_textlk()
# ---------------------------------------------------------------------------

class TestDispatchTextlk:
    """
    Tests for the _dispatch_textlk() function in simulation mode.
    All tests run with TEXTLK_ENABLED=false so no HTTP requests are made.
    """

    def test_simulated_when_disabled(self):
        """TEXTLK_ENABLED=false must return simulated status without HTTP call."""
        assert settings.TEXTLK_ENABLED is False, (
            "Test must run with TEXTLK_ENABLED=false to avoid real API calls."
        )
        result = sms_gateway._dispatch_textlk("+94771234567", "Test message")
        assert result["status"] == "simulated"
        assert result["provider"] == "TEXTLK_SIMULATOR"
        assert result["sid"] is None
        assert "no SMS was sent" in result["message"].lower() or "disabled" in result["message"].lower()

    def test_missing_token_when_enabled(self):
        """With TEXTLK_ENABLED=true but empty token, must return failed without HTTP call."""
        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", ""):
            result = sms_gateway._dispatch_textlk("+94771234567", "Test message")
        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert "token" in result["message"].lower() or "TEXTLK_API_TOKEN" in result["message"]

    def test_invalid_phone_when_enabled(self):
        """With a malformed phone number, must return failed with a validation error."""
        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"):
            result = sms_gateway._dispatch_textlk("not-a-phone", "Test message")
        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"

    def test_empty_body_when_enabled(self):
        """Empty message body must return failed without making an HTTP request."""
        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"):
            result = sms_gateway._dispatch_textlk("+94771234567", "   ")
        assert result["status"] == "failed"
        assert "empty" in result["message"].lower()


class TestDispatchSmsRouting:
    """Tests that _dispatch_sms() routes to Text.lk when TEXTLK_ENABLED=true."""

    def test_routes_to_textlk_when_enabled(self):
        """_dispatch_sms() must call _dispatch_textlk() when TEXTLK_ENABLED=true."""
        mock_result = {"status": "simulated", "sid": None, "provider": "TEXTLK_SIMULATOR",
                       "message": "mocked"}
        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch("app.services.sms_gateway._dispatch_textlk",
                   return_value=mock_result) as mock_fn:
            result = sms_gateway._dispatch_sms("+94771234567", "Test message")
        mock_fn.assert_called_once_with("+94771234567", "Test message")
        assert result == mock_result

    def test_simulated_when_both_disabled(self):
        """When both TEXTLK_ENABLED=false and SMSGO_ENABLED=false, returns simulated."""
        with patch.object(settings, "TEXTLK_ENABLED", False), \
             patch.object(settings, "SMSGO_ENABLED", False):
            result = sms_gateway._dispatch_sms("+94771234567", "Test message")
        assert result["status"] == "simulated"
        assert result["provider"] == "SMSGO_SIMULATOR"

    def test_does_not_call_textlk_when_disabled(self):
        """_dispatch_textlk() must NOT be called when TEXTLK_ENABLED=false."""
        with patch.object(settings, "TEXTLK_ENABLED", False), \
             patch.object(settings, "SMSGO_ENABLED", False), \
             patch("app.services.sms_gateway._dispatch_textlk") as mock_fn:
            sms_gateway._dispatch_sms("+94771234567", "Test message")
        mock_fn.assert_not_called()


class TestPhoneForTextlk:
    """Tests for _phone_for_textlk() number normalisation."""

    def test_converts_e164_to_textlk_format(self):
        assert sms_gateway._phone_for_textlk("+94771234567") == "94771234567"

    def test_converts_local_format(self):
        assert sms_gateway._phone_for_textlk("0771234567") == "94771234567"

    def test_converts_94_prefix(self):
        assert sms_gateway._phone_for_textlk("94771234567") == "94771234567"


# ---------------------------------------------------------------------------
# Integration tests via FastAPI TestClient
# ---------------------------------------------------------------------------

class TestSOSAlertContactsEndpoint:
    """Tests for POST /sos/alert-contacts with security, authentication, and contact verification."""

    def _submit_sos(self, client: TestClient, token: str) -> int:
        """Helper: submit a SOS and return its id."""
        payload = {
            "latitude": 6.9364,
            "longitude": 79.9572,
            "district": "Colombo",
            "ds_division": "Kaduwela",
            "urgency_level": 5,
            "affected_people": 4,
            "affected_families": 1,
        }
        res = client.post(
            "/api/v1/sos",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, f"SOS creation failed: {res.text}"
        return res.json()["id"]

    def test_unauthenticated_request_rejected(self, client: TestClient, db: Session):
        """POST /sos/alert-contacts without Authorization header must return 401."""
        res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": 1,
                "priority_score": 80.0,
                "victim_name": "Test",
                "location_text": "Colombo",
            },
        )
        assert res.status_code == 401

    def test_cannot_alert_another_users_sos(self, client: TestClient, db: Session):
        """User B cannot dispatch alerts for User A's SOS request (must return 403 Forbidden)."""
        _, token_a = _create_victim_user(db, "user_a_sec@test.lk")
        _, token_b = _create_victim_user(db, "user_b_sec@test.lk")

        # User A saves a verified contact and creates an SOS
        client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Contact A", "phone": "+94770001111", "relation": "Friend"}],
            headers={"Authorization": f"Bearer {token_a}"},
        )
        sos_id_a = self._submit_sos(client, token_a)

        # User B saves a contact too
        client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Contact B", "phone": "+94770002222", "relation": "Friend"}],
            headers={"Authorization": f"Bearer {token_b}"},
        )

        # User B attempts to trigger alerts on User A's SOS request
        res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": sos_id_a,
                "priority_score": 90.0,
                "victim_name": "Intruder",
                "location_text": "Colombo",
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 403, f"Expected 403 Forbidden, got: {res.status_code}"

    def test_no_saved_contacts_rejected(self, client: TestClient, db: Session):
        """POST /sos/alert-contacts when user has 0 saved contacts must return 400."""
        _, token = _create_victim_user(db, "tlk_ec_nocontacts@test.lk")
        sos_id = self._submit_sos(client, token)
        res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": sos_id,
                "priority_score": 90.0,
                "victim_name": "Test Victim",
                "location_text": "Ranala, Colombo",
                "latitude": 6.9364,
                "longitude": 79.9572,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "contact" in res.json()["detail"].lower()

    def test_arbitrary_unregistered_contact_rejected(self, client: TestClient, db: Session):
        """Arbitrary contacts in request body not genuinely saved in user's profile are rejected."""
        _, token = _create_victim_user(db, "arbitrary_contact_test@test.lk")
        client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Verified Contact", "phone": "+94770003333", "relation": "Family"}],
            headers={"Authorization": f"Bearer {token}"},
        )
        sos_id = self._submit_sos(client, token)

        # Request passes an arbitrary unverified phone number
        res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": sos_id,
                "priority_score": 85.0,
                "victim_name": "Test Victim",
                "location_text": "Ranala, Colombo",
                "contacts": [
                    {"name": "Malicious Number", "phone": "+94779998888", "relation": "Unknown"}
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "no valid" in res.json()["detail"].lower() or "contact" in res.json()["detail"].lower()

    def test_single_contact_dispatched_simulated(self, client: TestClient, db: Session):
        """
        POST /sos/alert-contacts with genuine saved contact must return 200.
        With TEXTLK_ENABLED=false the SMS is simulated — no real SMS is sent.
        The dispatch_log should contain one entry with status='simulated'.
        """
        assert settings.TEXTLK_ENABLED is False, "Test must run with Text.lk disabled."
        _, token = _create_victim_user(db, "tlk_ec_single_verified@test.lk")

        # Save a genuine contact first
        save_res = client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Kamal Perera", "phone": "+94770005555", "relation": "Brother"}],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert save_res.status_code == 200

        sos_id = self._submit_sos(client, token)

        res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": sos_id,
                "priority_score": 85.0,
                "victim_name": "Test Victim",
                "location_text": "Ranala, Colombo",
                "latitude": 6.9364,
                "longitude": 79.9572,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["total_contacts"] == 1
        assert len(data["dispatch_log"]) == 1
        log_entry = data["dispatch_log"][0]
        # Status must be "simulated" (not "sent") when Text.lk is disabled
        assert log_entry["status"] == "simulated", (
            f"Expected 'simulated' but got '{log_entry['status']}'. "
            "The integration must not claim 'sent' when TEXTLK_ENABLED=false."
        )

    def test_successful_sos_creation_followed_by_contact_dispatch(self, client: TestClient, db: Session):
        """
        Verify that a victim can successfully create an SOS distress beacon,
        receive the committed SOS ID and priority score, and immediately pass that
        SOS ID to /api/v1/sos/alert-contacts to dispatch emergency SMS to saved contacts.
        """
        assert settings.TEXTLK_ENABLED is False, "Test must run with Text.lk disabled (simulation mode)."
        victim, token = _create_victim_user(db, "tlk_ec_full_flow@test.lk")

        # 1. Save verified emergency contacts
        contacts_data = [
            {"name": "Nimal Perera", "phone": "+94771122334", "relation": "Brother"},
            {"name": "Sunil Silva", "phone": "+94715566778", "relation": "Neighbor"},
        ]
        save_res = client.put(
            "/api/v1/sos/contacts",
            json=contacts_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert save_res.status_code == 200

        # 2. Victim creates SOS
        sos_payload = {
            "latitude": 6.9364,
            "longitude": 79.9572,
            "district": "Colombo",
            "ds_division": "Kaduwela",
            "gn_division": "Ranala",
            "urgency_level": 5,
            "affected_people": 4,
            "affected_families": 1,
            "has_elderly": True,
            "has_children": True,
            "has_disabled": False,
            "medical_needs_summary": "Insulin vials",
        }
        sos_res = client.post(
            "/api/v1/sos",
            json=sos_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sos_res.status_code == 201, f"SOS creation failed: {sos_res.text}"
        sos_data = sos_res.json()
        sos_id = sos_data["id"]
        priority_score = sos_data["priority_score"]
        assert sos_id > 0
        assert sos_data["user_id"] == victim.id

        # 3. Contact dispatch using the returned SOS ID
        alert_res = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": sos_id,
                "priority_score": priority_score,
                "victim_name": victim.full_name,
                "location_text": "Ranala, Kaduwela, Colombo",
                "latitude": 6.9364,
                "longitude": 79.9572,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert alert_res.status_code == 200, f"Alert contacts failed: {alert_res.text}"
        alert_data = alert_res.json()
        assert alert_data["sos_id"] == sos_id
        assert alert_data["total_contacts"] == 2
        assert alert_data["contacts_alerted"] == 2
        assert len(alert_data["dispatch_log"]) == 2
        for log in alert_data["dispatch_log"]:
            assert log["status"] == "simulated"
            assert "SIMULATOR" in log["provider"] or "LOCAL" in log["provider"]

    def test_invalid_or_missing_sos_id(self, client: TestClient, db: Session):
        """
        Verify that POST /api/v1/sos/alert-contacts returns:
        - 404 Not Found when sos_id does not exist in the database (e.g. 999999 or 999).
        - 422 Unprocessable Entity when sos_id is omitted or invalid type.
        """
        victim, token = _create_victim_user(db, "tlk_ec_missing_id@test.lk")
        client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Kamal Perera", "phone": "+94770005555", "relation": "Brother"}],
            headers={"Authorization": f"Bearer {token}"},
        )

        # Non-existent SOS ID -> 404
        res_404 = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": 999999,
                "priority_score": 95.0,
                "victim_name": "Test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_404.status_code == 404
        assert "sos request not found" in res_404.json()["detail"].lower()

        # Missing sos_id -> 422
        res_missing = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "priority_score": 95.0,
                "victim_name": "Test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_missing.status_code == 422

        # Invalid string sos_id -> 422
        res_invalid_type = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": "not-an-id",
                "priority_score": 95.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_invalid_type.status_code == 422

    def test_failed_sos_creation_must_not_trigger_sms_dispatch(self, client: TestClient, db: Session):
        """
        Verify that a failed SOS creation (e.g., validation failure) does NOT create an SOS record,
        and SMS dispatch is not triggered / cannot succeed without a committed SOS record.
        """
        victim, token = _create_victim_user(db, "tlk_ec_failed_create@test.lk")
        client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Valid Contact", "phone": "+94771239999", "relation": "Parent"}],
            headers={"Authorization": f"Bearer {token}"},
        )

        # Attempt to create SOS with invalid urgency_level (> 5)
        bad_payload = {
            "latitude": 6.9364,
            "longitude": 79.9572,
            "district": "Colombo",
            "urgency_level": 99,  # Invalid: Field(..., ge=1, le=5)
            "affected_people": 2,
        }
        res_bad = client.post(
            "/api/v1/sos",
            json=bad_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_bad.status_code == 422

        # Verify no SOS record was created for this user
        user_sos_count = db.query(SOSRequest).filter(SOSRequest.user_id == victim.id).count()
        assert user_sos_count == 0

        # Verify that attempting to alert contacts without an SOS record fails with 404
        res_alert = client.post(
            "/api/v1/sos/alert-contacts",
            json={
                "sos_id": 99999,
                "priority_score": 80.0,
                "victim_name": "Test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_alert.status_code == 404
        assert "sos request not found" in res_alert.json()["detail"].lower()

    def test_placeholder_contact_rejected_in_put(self, client: TestClient, db: Session):
        """Saving placeholder demo phone numbers must be rejected with 400."""
        _, token = _create_victim_user(db, "placeholder_reject_test@test.lk")
        res = client.put(
            "/api/v1/sos/contacts",
            json=[{"name": "Fake Demo", "phone": "+94 77 123 4567", "relation": "Mock"}],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "placeholder" in res.json()["detail"].lower()

    def test_max_four_contacts_limit(self, client: TestClient, db: Session):
        """Attempting to save 5 contacts must be rejected with 400."""
        _, token = _create_victim_user(db, "five_contacts_limit@test.lk")
        five = [
            {"name": f"Contact {i}", "phone": f"+9477000000{i}", "relation": "Friend"}
            for i in range(1, 6)
        ]
        res = client.put(
            "/api/v1/sos/contacts",
            json=five,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "maximum of 4" in res.json()["detail"].lower()

    def test_get_contacts_returns_saved(self, client: TestClient, db: Session):
        """GET /sos/contacts returns genuinely saved contacts for the user."""
        _, token = _create_victim_user(db, "get_contacts_test@test.lk")
        contacts_in = [
            {"name": "Alice Silva", "phone": "+94771112222", "relation": "Sister"},
            {"name": "Bob Silva", "phone": "+94772223333", "relation": "Uncle"},
        ]
        client.put(
            "/api/v1/sos/contacts",
            json=contacts_in,
            headers={"Authorization": f"Bearer {token}"},
        )
        res = client.get(
            "/api/v1/sos/contacts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        saved = res.json()
        assert len(saved) == 2
        assert saved[0]["name"] == "Alice Silva"
        assert saved[1]["phone"] == "+94772223333"


class TestSOSWorkflowAndPermissions:
    """
    Tests verifying SOS workflow role-based access control and ownership checks:
    - Authenticated victims can create their own SOS beacons.
    - Victims can retrieve only their permitted (owned) SOS records.
    - Victims cannot access another user's private SOS record.
    - Victims cannot access privileged authority endpoints (e.g. status updates).
    - Unauthenticated callers are rejected (401).
    - Non-permitted roles (e.g. donor) are rejected (403).
    - Authority/admin roles can access all SOS records and update status.
    """

    def _sample_sos_payload(self) -> dict:
        return {
            "latitude": 6.9364,
            "longitude": 79.9572,
            "district": "Colombo",
            "ds_division": "Kaduwela",
            "gn_division": "Ranala",
            "address_text": "45 River View Lane, Ranala",
            "urgency_level": 5,
            "affected_people": 4,
            "affected_families": 1,
            "has_elderly": True,
            "has_children": True,
            "has_disabled": False,
            "medical_needs_summary": "Insulin, Clean Water",
        }

    def test_victim_can_create_own_sos(self, client: TestClient, db: Session):
        victim, token = _create_victim_user(db, "victim_create_sos@test.lk")
        res = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["user_id"] == victim.id
        assert data["status"] == "active"
        assert data["priority_score"] >= 0.0

    def test_victim_can_retrieve_only_own_records(self, client: TestClient, db: Session):
        victim_a, token_a = _create_victim_user(db, "victim_a_records@test.lk")
        victim_b, token_b = _create_victim_user(db, "victim_b_records@test.lk")

        # Victim A submits an SOS
        res_a = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token_a}"},
        )
        sos_a_id = res_a.json()["id"]

        # Victim B submits an SOS
        res_b = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token_b}"},
        )
        sos_b_id = res_b.json()["id"]

        # Victim A lists SOS records
        list_a = client.get(
            "/api/v1/sos",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_a.status_code == 200
        records_a = list_a.json()
        sos_ids_a = [r["id"] for r in records_a]
        assert sos_a_id in sos_ids_a
        assert sos_b_id not in sos_ids_a
        assert all(r["user_id"] == victim_a.id for r in records_a)

        # Victim B lists SOS records
        list_b = client.get(
            "/api/v1/sos",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert list_b.status_code == 200
        records_b = list_b.json()
        sos_ids_b = [r["id"] for r in records_b]
        assert sos_b_id in sos_ids_b
        assert sos_a_id not in sos_ids_b
        assert all(r["user_id"] == victim_b.id for r in records_b)

    def test_victim_can_get_own_sos_by_id(self, client: TestClient, db: Session):
        victim, token = _create_victim_user(db, "victim_own_by_id@test.lk")
        res = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        sos_id = res.json()["id"]

        get_res = client.get(
            f"/api/v1/sos/{sos_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_res.status_code == 200
        assert get_res.json()["id"] == sos_id
        assert get_res.json()["user_id"] == victim.id

    def test_victim_cannot_access_other_user_sos_by_id(self, client: TestClient, db: Session):
        _, token_a = _create_victim_user(db, "victim_user_a_priv@test.lk")
        _, token_b = _create_victim_user(db, "victim_user_b_priv@test.lk")

        res_a = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token_a}"},
        )
        sos_a_id = res_a.json()["id"]

        # Victim B attempts to view Victim A's private SOS record
        get_res = client.get(
            f"/api/v1/sos/{sos_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_res.status_code == 403
        assert "private sos record" in get_res.json()["detail"].lower()

    def test_victim_cannot_access_privileged_authority_endpoint(self, client: TestClient, db: Session):
        _, token = _create_victim_user(db, "victim_try_status@test.lk")
        res = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        sos_id = res.json()["id"]

        # Victim tries to update status via privileged PATCH endpoint
        patch_res = client.patch(
            f"/api/v1/sos/{sos_id}/status",
            json={"status": "resolved"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_res.status_code == 403
        assert "not permitted" in patch_res.json()["detail"].lower()

    def test_authority_and_admin_can_access_all_sos_and_update_status(self, client: TestClient, db: Session):
        _, victim_token = _create_victim_user(db, "victim_for_authority@test.lk")
        _, auth_token = _create_user_by_role(db, "authority_user_sos@test.lk", RoleEnum.authority)
        _, admin_token = _create_admin_user(db, "admin_user_sos@test.lk")

        sos_res = client.post(
            "/api/v1/sos",
            json=self._sample_sos_payload(),
            headers={"Authorization": f"Bearer {victim_token}"},
        )
        sos_id = sos_res.json()["id"]

        # Authority can view any SOS by id
        auth_get = client.get(
            f"/api/v1/sos/{sos_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert auth_get.status_code == 200

        # Authority can list all SOS
        auth_list = client.get(
            "/api/v1/sos",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert auth_list.status_code == 200
        assert any(r["id"] == sos_id for r in auth_list.json())

        # Authority can update status
        patch_res = client.patch(
            f"/api/v1/sos/{sos_id}/status",
            json={"status": "triaged"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "triaged"

        # Admin can view and update status
        admin_get = client.get(
            f"/api/v1/sos/{sos_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_get.status_code == 200

    def test_unauthenticated_requests_rejected(self, client: TestClient):
        assert client.post("/api/v1/sos", json=self._sample_sos_payload()).status_code == 401
        assert client.get("/api/v1/sos").status_code == 401
        assert client.get("/api/v1/sos/1").status_code == 401
        assert client.patch("/api/v1/sos/1/status", json={"status": "resolved"}).status_code == 401

    def test_donor_role_cannot_create_or_list_sos(self, client: TestClient, db: Session):
        _, donor_token = _create_user_by_role(db, "donor_sos_test@test.lk", RoleEnum.donor)
        headers = {"Authorization": f"Bearer {donor_token}"}
        assert client.post("/api/v1/sos", json=self._sample_sos_payload(), headers=headers).status_code == 403
        assert client.get("/api/v1/sos", headers=headers).status_code == 403
        assert client.patch("/api/v1/sos/1/status", json={"status": "resolved"}, headers=headers).status_code == 403


class TestSMSGatewayStatusEndpoint:
    """Tests for GET /sms/gateway-status with Text.lk fields."""

    def test_gateway_status_includes_textlk_fields(self, client: TestClient, db: Session):
        """Gateway status response must include textlk_enabled field."""
        res = client.get("/api/v1/sms/gateway-status")
        assert res.status_code == 200, res.text
        data = res.json()
        assert "textlk_enabled" in data, "Response must include textlk_enabled"
        assert "gateway_status" in data
        assert "ONLINE" in data["gateway_status"]
        # With defaults (TEXTLK_ENABLED=false, SMSGO_ENABLED=false), must be simulation mode
        assert data["textlk_enabled"] is False
        assert "simulat" in data["gateway_status"].lower() or "disabled" in data["gateway_status"].lower()


# ---------------------------------------------------------------------------
# Mocked HTTP tests — _dispatch_textlk() with TEXTLK_ENABLED=true
# These tests mock urllib.request.urlopen so NO real HTTP call is made.
# ---------------------------------------------------------------------------

class TestDispatchTextlkMockedHTTP:
    """
    Tests for _dispatch_textlk() with TEXTLK_ENABLED=true and mocked HTTP.
    Validates request construction, response parsing, and error handling
    without consuming any real Text.lk SMS credits.
    """

    def _make_mock_response(self, body: dict, status_code: int = 200):
        """Create a mock HTTP response object."""
        mock_resp = MagicMock()
        mock_resp.status = status_code
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_successful_send_returns_sent(self):
        """A 200 response with status=success from Text.lk should return status='sent'."""
        api_response = {
            "status": "success",
            "data": {"uid": "tlk-uid-12345", "status": "Delivered"},
        }
        mock_resp = self._make_mock_response(api_response, 200)

        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token-12345"), \
             patch("app.services.sms_gateway.urlopen", return_value=mock_resp) as mock_urlopen:

            result = sms_gateway._dispatch_textlk("+94771234567", "Test SOS alert")

        assert result["status"] == "sent"
        assert result["provider"] == "TEXTLK"
        assert result["sid"] == "tlk-uid-12345"
        assert result["environment"] == "live"
        assert "accepted" in result["message"].lower()
        assert "not yet confirmed" in result["message"].lower()

        # Verify the HTTP request was correctly constructed
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.get_method() == "POST"
        assert req.get_header("Authorization") == "Bearer fake-test-token-12345"
        assert req.get_header("Content-type") == "application/json"
        body = json.loads(req.data.decode("utf-8"))
        assert body["recipient"] == "94771234567"
        assert body["sender_id"] == "TextLKDemo"
        assert body["type"] == "plain"
        assert body["message"] == "Test SOS alert"

    def test_http_401_returns_failed(self):
        """A 401 Unauthorized from Text.lk should return status='failed'."""
        from urllib.error import HTTPError
        import io

        error_body = json.dumps({"message": "Unauthenticated."}).encode("utf-8")
        http_error = HTTPError(
            url="https://app.text.lk/api/v3/sms/send",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(error_body),
        )

        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "bad-token"), \
             patch("app.services.sms_gateway.urlopen", side_effect=http_error):

            result = sms_gateway._dispatch_textlk("+94771234567", "Test message")

        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert result["http_status"] == 401
        assert "unauthenticated" in result["message"].lower()

    def test_network_timeout_returns_failed(self):
        """A network timeout should return status='failed' with connection message."""
        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"), \
             patch("app.services.sms_gateway.urlopen", side_effect=TimeoutError("timed out")):

            result = sms_gateway._dispatch_textlk("+94771234567", "Urgent SOS")

        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert "connect" in result["message"].lower() or "network" in result["message"].lower()

    def test_invalid_json_response_returns_failed(self):
        """A non-JSON response from Text.lk should return status='failed'."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"<html>Server Error</html>"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"), \
             patch("app.services.sms_gateway.urlopen", return_value=mock_resp):

            result = sms_gateway._dispatch_textlk("+94771234567", "Test message")

        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert "invalid json" in result["message"].lower()

    def test_api_reports_unsuccessful_returns_failed(self):
        """When Text.lk returns status != 'success', result should be 'failed'."""
        api_response = {
            "status": "error",
            "message": "Insufficient balance",
        }
        mock_resp = self._make_mock_response(api_response, 200)

        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"), \
             patch("app.services.sms_gateway.urlopen", return_value=mock_resp):

            result = sms_gateway._dispatch_textlk("+94771234567", "Test message")

        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert "insufficient balance" in result["message"].lower()

    def test_url_error_returns_failed(self):
        """A URLError (DNS failure, etc.) should return status='failed'."""
        from urllib.error import URLError

        with patch.object(settings, "TEXTLK_ENABLED", True), \
             patch.object(settings, "TEXTLK_API_TOKEN", "fake-test-token"), \
             patch("app.services.sms_gateway.urlopen",
                   side_effect=URLError("Name resolution failed")):

            result = sms_gateway._dispatch_textlk("+94771234567", "Test message")

        assert result["status"] == "failed"
        assert result["provider"] == "TEXTLK"
        assert "connect" in result["message"].lower()


# ---------------------------------------------------------------------------
# send_direct_sms() DB logging test — verifies SMSMessageLog is created
# ---------------------------------------------------------------------------

class TestSendDirectSmsLog:
    """Tests that send_direct_sms() correctly logs to the DB in simulation mode."""

    def test_creates_sms_log_record(self, db: Session):
        """send_direct_sms() must create an SMSMessageLog with status='simulated'."""
        assert settings.TEXTLK_ENABLED is False

        sms_record = sms_gateway.send_direct_sms(
            recipient="+94771234567",
            message="Test emergency update via Text.lk simulation",
            message_type="TEST_NOTIFICATION",
            db=db,
        )

        assert sms_record.id is not None
        assert sms_record.direction == "outbound"
        assert sms_record.status == "simulated"
        assert sms_record.recipient == "+94771234567"
        assert sms_record.message_type == "TEST_NOTIFICATION"
        assert sms_record.gateway_provider in ("SMSGO_SIMULATOR", "TEXTLK_SIMULATOR")

    def test_empty_message_raises_value_error(self, db: Session):
        """send_direct_sms() with empty message must raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sms_gateway.send_direct_sms(
                recipient="+94771234567",
                message="   ",
                message_type="TEST",
                db=db,
            )

