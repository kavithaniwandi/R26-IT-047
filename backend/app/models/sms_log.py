"""
app/models/sms_log.py
---------------------
SMSMessageLog model for tracking all inbound/outbound SMS gateway interactions,
telecom carrier dispatches, parsed emergency alerts, and delivery receipts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SMSMessageLog(Base):
    __tablename__ = "sms_logs"

    id: int = Column(Integer, primary_key=True, index=True)
    direction: str = Column(String(20), nullable=False, index=True)  # 'inbound', 'outbound'
    sender: str = Column(String(50), nullable=False, index=True)      # Phone number or System/Telco ID
    recipient: str = Column(String(50), nullable=False, index=True)   # Destination phone or gateway number
    message_text: str = Column(Text, nullable=False)
    
    # Message Classification
    # Options: EMERGENCY_SOS, VICTIM_REGISTRATION, BROADCAST_ALERT, STATUS_INQUIRY, HELP_INFO, SYSTEM_CONFIRMATION
    message_type: str = Column(String(50), nullable=False, default="EMERGENCY_SOS", index=True)
    
    parsed_intent: str | None = Column(String(50), nullable=True)     # 'SOS_TRIGGER', 'REGISTRATION', 'STATUS_CHECK', 'UNKNOWN'
    parsed_payload_json: str | None = Column(Text, nullable=True)     # JSON string of structured parsed data
    
    # Foreign Key Associations
    sos_request_id: int | None = Column(Integer, ForeignKey("sos_requests.id"), nullable=True)
    victim_id: int | None = Column(Integer, ForeignKey("victims.id"), nullable=True)
    
    # Status: 'received', 'processed', 'queued', 'sent', 'delivered', 'failed'
    status: str = Column(String(30), nullable=False, default="received", index=True)
    gateway_provider: str = Column(String(50), nullable=False, default="SIMULATOR")  # 'SIMULATOR', 'DIALOG_SMSC', 'MOBITEL', 'TWILIO'
    raw_payload: str | None = Column(Text, nullable=True)
    
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    sos_request = relationship("SOSRequest", foreign_keys=[sos_request_id])
    victim = relationship("Victim", foreign_keys=[victim_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SMSMessageLog id={self.id} dir={self.direction} sender={self.sender} status={self.status}>"
