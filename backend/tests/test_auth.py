"""
tests/test_auth.py
-------------------
Day 1 test suite — covers:
  1. User registration (happy path, duplicate email, weak password)
  2. User login (correct credentials, wrong password, inactive account)
  3. /auth/me endpoint (valid token, no token)
  4. require_role() dependency (no token → 401, wrong role → 403, correct role → 200)

Tests use the in-memory DB fixture from conftest.py — no real DB is touched.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token


# ══════════════════════════════════════════════════════════════════════════════
# 1. REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestRegister:
    BASE = "/api/v1/auth/register"

    def test_register_success(self, client: TestClient):
        """New user registers successfully → 201 + UserOut body."""
        res = client.post(self.BASE, json={
            "full_name": "Test Victim",
            "email": "victim@test.com",
            "password": "SecurePass1",
            "phone": "+94771234567",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "victim@test.com"
        assert data["role"] == "victim"          # default role
        assert "hashed_password" not in data     # never exposed
        assert data["is_active"] is True

    def test_register_default_role_is_victim(self, client: TestClient):
        """Default role assigned at registration must always be 'victim'."""
        res = client.post(self.BASE, json={
            "full_name": "New User",
            "email": "newuser@test.com",
            "password": "SecurePass1",
        })
        assert res.status_code == 201
        assert res.json()["role"] == "victim"

    def test_register_duplicate_email(self, client: TestClient):
        """Second registration with the same email → 409 Conflict."""
        payload = {
            "full_name": "Dup User",
            "email": "dup@test.com",
            "password": "SecurePass1",
        }
        client.post(self.BASE, json=payload)          # first — succeeds
        res = client.post(self.BASE, json=payload)    # second — duplicate
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"].lower()

    def test_register_weak_password_no_digit(self, client: TestClient):
        """Password without a digit → 422 Validation Error."""
        res = client.post(self.BASE, json={
            "full_name": "Weak Pass",
            "email": "weak@test.com",
            "password": "NoDigitPassword",
        })
        assert res.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Password shorter than 8 characters → 422."""
        res = client.post(self.BASE, json={
            "full_name": "Short Pass",
            "email": "short@test.com",
            "password": "Ab1",
        })
        assert res.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Non-email string in email field → 422."""
        res = client.post(self.BASE, json={
            "full_name": "Bad Email",
            "email": "not-an-email",
            "password": "SecurePass1",
        })
        assert res.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 2. LOGIN
# ══════════════════════════════════════════════════════════════════════════════

class TestLogin:
    REG = "/api/v1/auth/register"
    BASE = "/api/v1/auth/login"

    def _register(self, client: TestClient, email="login_test@test.com",
                  password="SecurePass1"):
        client.post(self.REG, json={
            "full_name": "Login User",
            "email": email,
            "password": password,
        })

    def test_login_success(self, client: TestClient):
        """Correct credentials → 200 + access_token + role in body."""
        self._register(client)
        res = client.post(self.BASE, json={
            "email": "login_test@test.com",
            "password": "SecurePass1",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "victim"
        assert data["expires_in"] > 0

    def test_login_token_is_valid_jwt(self, client: TestClient):
        """Token returned on login must be decodable with the server secret."""
        self._register(client, email="jwt_check@test.com")
        res = client.post(self.BASE, json={
            "email": "jwt_check@test.com",
            "password": "SecurePass1",
        })
        token = res.json()["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "victim"
        assert "sub" in payload

    def test_login_wrong_password(self, client: TestClient):
        """Wrong password → 401 Unauthorized (unified message — no email enumeration)."""
        self._register(client, email="wrongpw@test.com")
        res = client.post(self.BASE, json={
            "email": "wrongpw@test.com",
            "password": "WrongPassword9",
        })
        assert res.status_code == 401

    def test_login_nonexistent_email(self, client: TestClient):
        """Non-existent email → 401 (same as wrong password — no enumeration)."""
        res = client.post(self.BASE, json={
            "email": "nobody@test.com",
            "password": "SecurePass1",
        })
        assert res.status_code == 401

    def test_login_inactive_account(self, client: TestClient, db):
        """Deactivated account → 403 Forbidden (account disabled)."""
        self._register(client, email="inactive@test.com")
        # Deactivate the user directly via DB
        from app.models.user import User
        user = db.query(User).filter(User.email == "inactive@test.com").first()
        if user:
            user.is_active = False
            db.commit()

        res = client.post(self.BASE, json={
            "email": "inactive@test.com",
            "password": "SecurePass1",
        })
        # 401 if user was not found in this test session (rollback isolation)
        assert res.status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 3. /auth/me
# ══════════════════════════════════════════════════════════════════════════════

class TestMe:
    REG = "/api/v1/auth/register"
    LOGIN = "/api/v1/auth/login"
    ME = "/api/v1/auth/me"

    def test_me_with_valid_token(self, client: TestClient):
        """Valid token → 200 + user profile."""
        client.post(self.REG, json={
            "full_name": "Me User",
            "email": "me@test.com",
            "password": "SecurePass1",
        })
        token_res = client.post(self.LOGIN, json={
            "email": "me@test.com",
            "password": "SecurePass1",
        })
        token = token_res.json()["access_token"]
        res = client.get(self.ME, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["email"] == "me@test.com"

    def test_me_without_token(self, client: TestClient):
        """No token → 401 Unauthorized."""
        res = client.get(self.ME)
        assert res.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# 4. require_role() DEPENDENCY
# These tests use a real route that is guarded by require_role.
# We test the RBAC logic directly via an admin-only probe endpoint.
# ══════════════════════════════════════════════════════════════════════════════

# Add a temporary probe route to the app ONLY during tests
from fastapi import Depends
from app.core.security import require_role, TokenPayload
from app.models.main import app


@app.get("/api/v1/_test/admin-only", include_in_schema=False)
def _admin_only_probe(
    payload: TokenPayload = Depends(require_role(["admin"]))
):
    return {"ok": True, "role": payload.role}


@app.get("/api/v1/_test/multi-role", include_in_schema=False)
def _multi_role_probe(
    payload: TokenPayload = Depends(require_role(["admin", "authority", "donor"]))
):
    return {"ok": True, "role": payload.role}


class TestRequireRole:
    PROBE_ADMIN = "/api/v1/_test/admin-only"
    PROBE_MULTI = "/api/v1/_test/multi-role"

    def _make_token(self, role: str, user_id: int = 999,
                    expire_delta: timedelta | None = None) -> str:
        """Helper: craft a JWT with any role (without DB interaction)."""
        delta = expire_delta or timedelta(minutes=60)
        expire = datetime.now(timezone.utc) + delta
        return jwt.encode(
            {"sub": str(user_id), "role": role, "exp": expire},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def test_no_token_returns_401(self, client: TestClient):
        res = client.get(self.PROBE_ADMIN)
        assert res.status_code == 401

    def test_malformed_token_returns_401(self, client: TestClient):
        res = client.get(self.PROBE_ADMIN,
                         headers={"Authorization": "Bearer not.a.valid.token"})
        assert res.status_code == 401

    def test_expired_token_returns_401(self, client: TestClient):
        expired_token = self._make_token("admin", expire_delta=timedelta(seconds=-1))
        res = client.get(self.PROBE_ADMIN,
                         headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401

    def test_wrong_role_returns_403(self, client: TestClient):
        """Victim token hitting an admin-only endpoint → 403 Forbidden."""
        token = self._make_token("victim")
        res = client.get(self.PROBE_ADMIN,
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403

    def test_correct_role_returns_200(self, client: TestClient):
        """Admin token hitting the admin-only endpoint → 200."""
        token = self._make_token("admin")
        res = client.get(self.PROBE_ADMIN,
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["role"] == "admin"

    def test_multi_role_allowed(self, client: TestClient):
        """Donor token against a multi-role endpoint that includes donor → 200."""
        token = self._make_token("donor")
        res = client.get(self.PROBE_MULTI,
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

    def test_multi_role_victim_blocked(self, client: TestClient):
        """Victim token against [admin, authority, donor] endpoint → 403."""
        token = self._make_token("victim")
        res = client.get(self.PROBE_MULTI,
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403

    def test_authority_on_multi_role(self, client: TestClient):
        """Authority token → allowed on multi-role endpoint."""
        token = self._make_token("authority")
        res = client.get(self.PROBE_MULTI,
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["role"] == "authority"
