"""
app/services/auth.py
---------------------
Business-logic layer for user registration and authentication.

Keeping this separate from the router means:
  - The router handles HTTP concerns (request parsing, status codes, responses).
  - This service handles business rules (duplicate-email check, password
    hashing, role lookup, token issuance).
  - Tests can call these functions directly without spinning up HTTP.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.role import Role, RoleEnum
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

# ── Password hashing via passlib + bcrypt ─────────────────────────────────────
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(payload: RegisterRequest, db: Session) -> UserOut:
    """
    Create a new user account with the default 'victim' role.

    Steps:
      1. Guard against duplicate email (409 Conflict).
      2. Look up the 'victim' role row (guaranteed to exist after DB seed).
      3. Hash the password — the plain-text password is discarded immediately.
      4. Persist the new User row.
      5. Return a safe UserOut projection (no password hash).

    Why default to 'victim'?
      Self-registration represents a member of the public who needs help.
      An admin can later promote them to donor, authority, or volunteer.
    """
    # 1. Duplicate email check
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    # 2. Resolve the default 'victim' role
    victim_role = db.query(Role).filter(Role.name == RoleEnum.victim).first()
    if victim_role is None:
        # Should never happen after init_db() seeds roles, but fail clearly.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role table is not seeded. Contact the administrator.",
        )

    # 3. Hash password
    hashed = _hash_password(payload.password)

    # 4. Persist
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hashed,
        phone=payload.phone,
        address=payload.address,
        role_id=victim_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 5. Return safe projection
    return _user_to_out(user, db)


# ── Login ─────────────────────────────────────────────────────────────────────

def authenticate_user(payload: LoginRequest, db: Session) -> TokenResponse:
    """
    Verify credentials and issue a JWT.

    Security considerations:
      - We return 401 for BOTH "no such email" and "wrong password"
        to prevent email-enumeration attacks.
      - The JWT payload includes the role so that subsequent require_role()
        checks are stateless (no DB round-trip per request).
    """
    user = db.query(User).filter(User.email == payload.email).first()

    # Unified 401 — do not distinguish "no user" from "bad password"
    if user is None or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact an administrator.",
        )

    # Resolve the role name string
    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name: str = role.name.value if role else "victim"

    token = create_access_token(user_id=user.id, role=role_name)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=role_name,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_to_out(user: User, db: Session) -> UserOut:
    """Build a safe UserOut from a User ORM object."""
    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = role.name.value if role else "victim"
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
