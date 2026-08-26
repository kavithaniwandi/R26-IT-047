"""
app/core/security.py
---------------------
JWT encoding/decoding and the `require_role` FastAPI dependency.

Design decisions (see Section 6 of the project proposal):
- Stateless: role check is a pure function of the JWT claim — no DB hit.
- Fail-closed: missing / malformed / expired token → 401 Unauthorized.
- Wrong role → 403 Forbidden  (so frontend can distinguish "log in" vs "no permission").
- The role claim is embedded at login time; a role change only takes effect
  after the current token expires (token lifetime ≤ 60 min, see .env).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

# ── OAuth2 scheme ────────────────────────────────────────────────────────────
# FastAPI will look for Bearer <token> in the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Token payload model ──────────────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str          # user_id as string
    role: str         # one of: admin, victim, donor, authority, volunteer
    exp: int          # unix timestamp


# ── JWT helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str) -> str:
    """
    Create a signed JWT that embeds user_id and role.

    The role is embedded at issuance so that every subsequent
    require_role() check is a pure, zero-DB-hit function call.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT.  Raises 401 on any failure so the caller
    never has to handle a partially-valid token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        exp: int = payload.get("exp")
        if user_id is None or role is None:
            raise credentials_exception
        return TokenPayload(sub=user_id, role=role, exp=exp)
    except JWTError:
        raise credentials_exception


# ── RBAC dependency ──────────────────────────────────────────────────────────

def require_role(allowed_roles: List[str]):
    """
    Factory that returns a FastAPI dependency enforcing role-based access.

    Usage:
        @router.get("/camps/{id}/approve",
                    dependencies=[Depends(require_role(["admin", "authority"]))])

    Or to also get the token payload in the handler:
        @router.get("/sos")
        async def list_sos(payload: TokenPayload = Depends(require_role(["admin", "authority"]))):
            ...

    Raises:
        401  if the token is missing, expired, or malformed.
        403  if the token is valid but the role is not in allowed_roles.
    """
    def _dependency(token: str = Depends(oauth2_scheme)) -> TokenPayload:
        token_data = decode_token(token)   # raises 401 on failure
        if token_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{token_data.role}' is not permitted to access this resource. "
                       f"Required: {allowed_roles}",
            )
        return token_data

    return _dependency


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Convenience dependency that validates the token but does NOT enforce
    a specific role — useful for endpoints open to any authenticated user.
    """
    return decode_token(token)
