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

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenPayload, create_access_token, get_current_user_payload
from app.database import get_db, users_collection
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


@router.post(
    "/component-login",
    response_model=TokenResponse,
    summary="Login with an existing MongoDB component account",
)
async def component_login(payload: LoginRequest) -> TokenResponse:
    """Preserve the individual component's existing Mongo users and ObjectIds."""
    user = await users_collection.find_one({"email": str(payload.email)})

    password_hash = user.get("password") if user else None
    password_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
    try:
        password_valid = bool(password_hash) and password_context.verify(payload.password, password_hash)
    except (TypeError, ValueError):
        password_valid = False

    role = user.get("userType") if user else None
    allowed_roles = {"admin", "donor", "disaster_officer", "volunteer"}
    if not password_valid or role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.get("isActive") is False or user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    return TokenResponse(
        access_token=create_access_token(str(user["_id"]), role),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=role,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user info",
    description="Returns the profile of the user identified by the Bearer token.",
)
async def me(
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
) -> UserOut:
    from app.models.user import User
    from app.models.role import Role

    if not token_data.sub.isdigit():
        from bson import ObjectId

        if not ObjectId.is_valid(token_data.sub):
            raise HTTPException(status_code=404, detail="User not found.")
        mongo_user = await users_collection.find_one({"_id": ObjectId(token_data.sub)})
        if mongo_user is None:
            raise HTTPException(status_code=404, detail="User not found.")
        full_name = " ".join(
            part for part in [mongo_user.get("firstName"), mongo_user.get("lastName")] if part
        ) or mongo_user.get("full_name") or "Component User"
        return UserOut(
            id=token_data.sub,
            full_name=full_name,
            email=mongo_user.get("email"),
            phone=mongo_user.get("phone"),
            address=mongo_user.get("address"),
            role=mongo_user.get("userType", token_data.role),
            is_active=mongo_user.get("isActive", mongo_user.get("is_active", True)),
            created_at=mongo_user.get("createdAt") or mongo_user.get("created_at") or datetime.now(timezone.utc),
        )

    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None:
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
