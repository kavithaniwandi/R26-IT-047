"""
app/models/donation.py
----------------------
DonationItem and Donation models supporting demand-driven relief and partial pledges.
"""
from __future__ import annotations
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class DonationItem(Base):
    __tablename__ = "donation_items"

    id = Column(Integer, primary_key=True, index=True)
    sos_request_id = Column(Integer, ForeignKey("sos_requests.id"), nullable=False, index=True)
    
    category = Column(String(50), nullable=False) # 'Medicine', 'Consumables', 'Equipment', 'Water', 'Nutrition'
    item_name = Column(String(150), nullable=False)
    quantity_required = Column(Integer, nullable=False)
    quantity_fulfilled = Column(Integer, nullable=False, default=0)
    unit = Column(String(30), nullable=False, default="units") # 'units', 'boxes', 'bottles', 'liters', 'packs'
    
    # Status: 'unmet', 'partially_met', 'fulfilled'
    status = Column(String(30), nullable=False, default="unmet", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sos_request = relationship("SOSRequest", back_populates="donation_items")
    donations = relationship("Donation", back_populates="donation_item", cascade="all, delete-orphan")


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    donation_item_id = Column(Integer, ForeignKey("donation_items.id"), nullable=False, index=True)
    
    quantity_pledged = Column(Integer, nullable=False)
    # Delivery status: 'pledged', 'in_transit', 'delivered', 'cancelled'
    delivery_status = Column(String(30), nullable=False, default="pledged", index=True)
    tracking_code = Column(String(64), unique=True, nullable=False, default=lambda: f"TRK-{uuid.uuid4().hex[:8].upper()}")
    
    pledged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    donor = relationship("User", foreign_keys=[donor_user_id])
    donation_item = relationship("DonationItem", back_populates="donations")
