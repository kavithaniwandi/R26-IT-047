from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String)
    home_lat = Column(Float)
    home_lng = Column(Float)
    emergency_contacts = Column(String)  # JSON string


class SOSRequest(Base):
    __tablename__ = "sos_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    disaster_type = Column(String, nullable=False)  # 'flood' or 'landslide'
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    num_affected = Column(Integer, default=1)
    has_children = Column(Boolean, default=False)
    has_elderly = Column(Boolean, default=False)
    has_injured = Column(Boolean, default=False)
    needed_item = Column(String, default="food")
    status = Column(String, default="open")
    priority_score = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskZone(Base):
    __tablename__ = "risk_zones"
    id = Column(Integer, primary_key=True, index=True)
    gn_division = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    disaster_type = Column(String)
    base_risk_score = Column(Float)
    live_risk_score = Column(Float)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Donor(Base):
    __tablename__ = "donors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    item_type = Column(String)
    quantity = Column(Integer)
    available = Column(Boolean, default=True)


class CampRecommendation(Base):
    __tablename__ = "camp_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    gn_division = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    sos_count = Column(Integer)
    injured_count = Column(Integer)
    nearest_hospital_km = Column(Float)
    recommended = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
