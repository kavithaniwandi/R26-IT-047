"""
app/models/user.py
-------------------
User model — the single registered-account entity for all stakeholder types.

Key design choices (Section 7.1 of proposal):
  - role_id is a FK to roles.id; role enforcement lives at the API layer
    (via require_role), NOT at the schema level, so the schema stays
    role-agnostic and future access-matrix changes don't require migrations.
  - Default role is 'victim' (set in the auth service at registration).
  - Only an admin can change a user's role via PATCH /api/v1/users/{id}/role.
  - Passwords are stored as bcrypt hashes; the plain-text password is
    NEVER stored or logged anywhere in the system.
  - is_active allows soft-disabling an account without data loss.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)

    # Personal details
    full_name: str = Column(String(120), nullable=False)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)

    # Optional contact info (used by SOS notification system)
    phone: str = Column(String(20), nullable=True)
    address: str = Column(String(500), nullable=True)

    # Role FK — defaults to 'victim' role (set in auth service)
    role_id: int = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")

    # Account state
    is_active: bool = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email} role={self.role_id}>"
