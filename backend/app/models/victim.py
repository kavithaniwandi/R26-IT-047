"""
app/models/victim.py
--------------------
Victim model for comprehensive disaster victim registration, vulnerability assessment,
household demographics, medical needs tracking, and evacuation camp assignments.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Victim(Base):
    __tablename__ = "victims"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int | None = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Identification
    nic: str | None = Column(String(30), nullable=True, index=True)
    full_name: str = Column(String(150), nullable=False)
    phone: str = Column(String(25), nullable=False, index=True)
    alternate_phone: str | None = Column(String(25), nullable=True)
    gender: str | None = Column(String(20), nullable=True)  # male, female, other
    age: int | None = Column(Integer, nullable=True)

    # Location & Administrative division
    district: str = Column(String(100), nullable=False, default="Colombo", index=True)
    ds_division: str | None = Column(String(100), nullable=True)
    gn_division: str | None = Column(String(100), nullable=True)
    current_address: str | None = Column(String(500), nullable=True)
    latitude: float = Column(Float, nullable=False, default=6.9271)
    longitude: float = Column(Float, nullable=False, default=79.8612)

    # Family & Household demographics
    family_members_count: int = Column(Integer, nullable=False, default=1)
    children_count: int = Column(Integer, nullable=False, default=0)
    elderly_count: int = Column(Integer, nullable=False, default=0)
    disabled_count: int = Column(Integer, nullable=False, default=0)
    pregnant_lactating_count: int = Column(Integer, nullable=False, default=0)

    # Evacuation & Safety Status
    # Options: trapped_in_house, safe_at_home, isolated_roof_level, evacuated_to_camp, displaced_with_relatives
    evacuation_status: str = Column(String(50), nullable=False, default="trapped_in_house", index=True)
    assigned_camp_id: int | None = Column(Integer, ForeignKey("medical_camps.id"), nullable=True)

    # Medical & Relief Requirements
    chronic_diseases: str | None = Column(Text, nullable=True)
    immediate_medical_needs: str | None = Column(Text, nullable=True)
    dietary_and_relief_needs: str | None = Column(Text, nullable=True)

    # Computed Vulnerability Index (0.0 to 100.0)
    vulnerability_score: float = Column(Float, nullable=False, default=50.0)

    # Registration Channel & Verification
    # Channels: web_portal, sms_gateway, volunteer_app, camp_intake
    registered_via: str = Column(String(40), nullable=False, default="web_portal")
    is_verified: bool = Column(Boolean, nullable=False, default=False)
    notes: str | None = Column(Text, nullable=True)

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

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_camp = relationship("MedicalCamp", foreign_keys=[assigned_camp_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Victim id={self.id} name={self.full_name} phone={self.phone} district={self.district}>"
