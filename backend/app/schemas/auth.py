"""
app/schemas/auth.py
--------------------
Pydantic v2 request/response schemas for the auth endpoints.

Separating schemas from ORM models (the "schema/model split") is intentional:
  - It prevents leaking internal fields (hashed_password, role_id) to API callers.
  - It lets request validation (RegisterRequest) differ from response shapes (UserOut).
  - All validation is declared once in Pydantic; FastAPI enforces it automatically.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, examples=["Kavitha Perera"])
    email: EmailStr = Field(..., examples=["kavitha@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass1!"])
    phone: str | None = Field(None, pattern=r"^\+?[0-9\s\-]{7,20}$", examples=["+94771234567"])
    address: str | None = Field(None, max_length=500, examples=["12 Kandy Road, Colombo"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Enforce at least one digit and one letter for basic strength."""
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one digit.")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    Standard OAuth2 password-flow body.
    We also expose a /api/v1/auth/login JSON endpoint (not just the form-based one)
    so the React frontend can POST JSON instead of form-data if preferred.
    """
    email: EmailStr = Field(..., examples=["kavitha@example.com"])
    password: str = Field(..., examples=["StrongPass1!"])


# ── Token response ────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds
    role: str                # so frontend can render the correct UI immediately


# ── User output (safe — no hashed_password, no internal IDs) ─────────────────

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    address: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
