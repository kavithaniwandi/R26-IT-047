"""
app/routers/auth.py
--------------------
HTTP layer for authentication endpoints.

Routes:
  POST /api/v1/auth/register  → register a new user (default role: victim)
  POST /api/v1/auth/login     → verify credentials, return JWT
  GET  /api/v1/auth/me        → return current user info (any authenticated role)

Design principle: this file handles HTTP concerns only.
All business logic lives in app/services/auth.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import TokenPayload, get_current_user_payload
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Creates a new user with the default **victim** role. "
        "Only an admin can promote the role later via PATCH /users/{id}/role."
    ),
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    return auth_service.register_user(payload, db)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive a JWT",
    description=(
        "Verifies email and password. Returns a Bearer JWT whose payload "
        "contains the user's role — all subsequent require_role() checks "
        "are stateless reads of this claim."
    ),
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.authenticate_user(payload, db)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user info",
    description="Returns the profile of the user identified by the Bearer token.",
)
def me(
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
) -> UserOut:
    from app.models.user import User
    from app.models.role import Role

    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found.")

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
