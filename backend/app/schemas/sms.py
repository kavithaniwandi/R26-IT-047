"""
app/schemas/sms.py
------------------
Pydantic v2 schemas for SMS gateway ingress, outbound SMS dispatches,
bulk broadcasts, carrier webhook payloads, and simulator logs.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import re

_PHONE_HINT = "E.164 format required, e.g. +94771234567"


class InboundSMSRequest(BaseModel):
    """Payload received from telecom carrier SMSC webhook (Twilio, Dialog, Mobitel)."""
    sender: str = Field(
        ...,
        examples=["+94771234567"],
        description=f"Originating mobile number. {_PHONE_HINT}",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1600,
        examples=["SOS 5 Ranala, Kaduwela 4 Diabetic patient trapped on 2nd floor"],
        description="Raw SMS message body (up to 1600 chars for multi-part SMS).",
    )
    recipient: str = Field(
        "1919",
        description="Emergency shortcode or virtual number that received the SMS.",
    )
    provider: str = Field(
        "DIALOG_SMSC",
        description="Carrier / gateway provider code (DIALOG_SMSC, MOBITEL, TWILIO, etc.).",
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO-8601 timestamp from carrier (optional).",
    )


class SimulateInboundSMSRequest(BaseModel):
    """Payload for interactive SMS simulation (no real SIM card needed)."""
    sender: str = Field(
        "+94771234567",
        description=f"Simulated sender phone number. {_PHONE_HINT}",
    )
    message: str = Field(
        "SOS 5 Ranala, Kaduwela 4 Need insulin and potable water immediately",
        min_length=1,
        max_length=1600,
        description="Raw incoming SMS text to parse and process.",
    )
    provider: str = Field(
        "SIMULATOR",
        description="Simulated carrier name — appears in gateway logs.",
    )


class SendSMSRequest(BaseModel):
    """Request body for sending a direct outbound SMS to one recipient."""
    recipient: str = Field(
        ...,
        description=f"Target phone number. {_PHONE_HINT}",
        examples=["+94771234567"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1600,
        description="SMS message body.",
    )
    message_type: str = Field(
        "SYSTEM_NOTIFICATION",
        description="Classification tag for logging (e.g. SYSTEM_NOTIFICATION, CAMP_ALERT).",
    )


class BroadcastSMSRequest(BaseModel):
    """Request body for bulk emergency broadcast SMS."""
    district: Optional[str] = Field(
        None,
        description="Target district filter (e.g. Colombo, Nuwara Eliya). Omit for nationwide.",
    )
    role: Optional[str] = Field(
        None,
        description="Recipient role filter (victim, volunteer, authority). Omit for all roles.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Emergency alert message body.",
    )
    urgency: str = Field(
        "HIGH",
        description="Urgency level string appended to alert header: CRITICAL | HIGH | MEDIUM | LOW",
    )

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        allowed = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        if v.upper() not in allowed:
            raise ValueError(f"urgency must be one of: {', '.join(sorted(allowed))}")
        return v.upper()


class SMSParsedResultOut(BaseModel):
    """Result returned after processing an inbound SMS message."""
    intent: str
    sender_phone: str
    urgency_level: int
    extracted_district: Optional[str] = None
    extracted_location: Optional[str] = None
    affected_people: int
    medical_needs: Optional[str] = None
    ml_priority_score: Optional[float] = None
    sos_id: Optional[int] = None
    victim_id: Optional[int] = None
    auto_reply_message: str
    sms_dispatch_status: str = "simulated"
    sms_sid: Optional[str] = None
    action_taken: str


class SMSLogOut(BaseModel):
    """Single SMS log entry (inbound or outbound)."""
    id: int
    direction: str
    sender: str
    recipient: str
    message_text: str
    message_type: str
    parsed_intent: Optional[str] = None
    sos_request_id: Optional[int] = None
    victim_id: Optional[int] = None
    status: str
    gateway_provider: str
    created_at: str

    model_config = {"from_attributes": True}


class SMSGatewayStatusOut(BaseModel):
    """Telecom SMS gateway status and live operational metrics."""
    gateway_status: str
    active_carrier: str
    twilio_enabled: bool = False
    signal_strength: str
    total_inbound_processed: int
    total_outbound_sent: int
    sent_count: int = 0
    simulated_count: int = 0
    failed_count: int = 0
    active_emergency_alerts: int
    delivery_success_rate: float
    supported_keywords: list[str]
