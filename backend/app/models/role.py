"""
app/models/role.py
-------------------
Role model and the canonical RoleEnum.

Design decision (Section 6.2 of proposal):
  Role names are stored as a string Enum column so that:
  - The DB enforces only valid role names at the schema level.
  - Python code compares roles with type-safe enum members rather than
    raw strings, catching typos at import time.

The five canonical roles:
  admin      — full system access
  victim     — default role assigned at self-registration
  donor      — can view donation needs and make pledges
  authority  — Medical Authority; can approve camps, view all SOS
  volunteer  — can view active SOS and assist with delivery
"""
from __future__ import annotations

import enum

from sqlalchemy import Column, Integer, String, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    victim = "victim"
    donor = "donor"
    authority = "authority"
    volunteer = "volunteer"


class Role(Base):
    __tablename__ = "roles"

    id: int = Column(Integer, primary_key=True, index=True)
    name: RoleEnum = Column(
        SAEnum(RoleEnum, name="role_enum"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Reverse relationship — used by SQLAlchemy for join queries
    users = relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role name={self.name}>"
