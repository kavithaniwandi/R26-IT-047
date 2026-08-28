"""
app/models/notification.py
--------------------------
Notification audit log model for multi-channel dispatches.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    channel = Column(String(20), nullable=False) # 'SMS', 'Email', 'Push'
    message_type = Column(String(50), nullable=False) # 'SOS_ALERT', 'CAMP_UPDATE', 'DONATION_MATCH', 'SYSTEM'
    recipient_target = Column(String(255), nullable=False)
    message_content = Column(Text, nullable=False)
    
    dispatch_status = Column(String(20), nullable=False, default="sent") # 'pending', 'sent', 'failed'
    dispatched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_user_id])
