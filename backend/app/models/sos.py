"""
app/models/sos.py
-----------------
SOSRequest model for emergency alerts and triage.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SOSRequest(Base):
    __tablename__ = "sos_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Coordinates & Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    ds_division = Column(String(100), nullable=True, index=True)
    gn_division = Column(String(100), nullable=True, index=True)
    address_text = Column(String(500), nullable=True)

    # Triage indicators
    urgency_level = Column(Integer, nullable=False, default=3) # 1 to 5
    affected_people = Column(Integer, nullable=False, default=1)
    affected_families = Column(Integer, nullable=False, default=1)
    has_elderly = Column(Boolean, nullable=False, default=False)
    has_children = Column(Boolean, nullable=False, default=False)
    has_disabled = Column(Boolean, nullable=False, default=False)
    medical_needs_summary = Column(Text, nullable=True)
    
    # ML Computed Priority (0.0 to 100.0)
    priority_score = Column(Float, nullable=False, default=50.0, index=True)
    
    # Status: 'active', 'triaged', 'camp_assigned', 'resolved', 'cancelled'
    status = Column(String(30), nullable=False, default="active", index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", backref="sos_requests")
    donation_items = relationship("DonationItem", back_populates="sos_request", cascade="all, delete-orphan")
