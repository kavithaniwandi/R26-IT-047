"""
app/models/camp.py
------------------
MedicalCamp model for temporary disaster relief medical posts.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class MedicalCamp(Base):
    __tablename__ = "medical_camps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    district = Column(String(100), nullable=False)
    ds_division = Column(String(100), nullable=False)
    gn_division = Column(String(100), nullable=True)
    
    suitability_score = Column(Float, nullable=False, default=75.0) # 0.0 to 100.0
    estimated_capacity = Column(Integer, nullable=False, default=100)
    current_occupancy = Column(Integer, nullable=False, default=0)
    
    # Status: 'proposed', 'approved', 'operational', 'closed'
    status = Column(String(30), nullable=False, default="proposed", index=True)
    
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    approver = relationship("User", foreign_keys=[approved_by_user_id])
