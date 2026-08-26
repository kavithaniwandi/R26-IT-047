"""
app/models/risk.py
------------------
RiskPrediction model storing spatial environmental hazard predictions.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.database import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    district = Column(String(100), nullable=False)
    ds_division = Column(String(100), nullable=False)
    gn_division = Column(String(100), nullable=True)
    
    hazard_type = Column(String(30), nullable=False) # 'flood' or 'landslide'
    risk_score = Column(Float, nullable=False)        # 0.0 to 100.0
    risk_tier = Column(String(20), nullable=False)    # 'Low', 'Medium', 'High'
    
    rainfall_mm = Column(Float, nullable=True)
    river_level_m = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    slope_deg = Column(Float, nullable=True)
    
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
