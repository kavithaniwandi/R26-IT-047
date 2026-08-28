"""
app/schemas/sms.py
------------------
Pydantic v2 schemas for SMS gateway ingress, outbound SMS dispatches,
bulk broadcasts, carrier webhook payloads, and simulator logs.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class InboundSMSRequest(BaseModel):
    """Payload received from telecom carrier SMSC webhook."""
    sender: str = Field(..., examples=["+94771234567"], description="Originating mobile number")
    message: str = Field(..., min_length=1, examples=["SOS 5 Ranala, Kaduwela 4 Diabetic patient trapped on 2nd floor"])
    recipient: str = Field("1919", description="Emergency Shortcode or virtual number")
    provider: str = Field("DIALOG_SMSC", description="Carrier / Gateway provider code")
    timestamp: str | None = None


class SimulateInboundSMSRequest(BaseModel):
    sender: str = Field("+94771234567", description="Simulated sender phone number")
    message: str = Field(
        "SOS 5 Ranala, Kaduwela 4 Need insulin and potable water immediately",
        description="Raw incoming SMS text"
    )
    provider: str = Field("SIMULATOR", description="Simulated carrier name")


class SendSMSRequest(BaseModel):
    recipient: str = Field(..., description="Target phone number (e.g. +94771234567)")
    message: str = Field(..., min_length=1, max_length=500, description="SMS text content")
    message_type: str = Field("SYSTEM_NOTIFICATION", description="Classification tag")


class BroadcastSMSRequest(BaseModel):
    district: str | None = Field(None, description="Optional target district filter (e.g. Colombo, Nuwara Eliya)")
    role: str | None = Field(None, description="Optional recipient role filter (e.g. victim, volunteer, authority)")
    message: str = Field(..., min_length=1, max_length=500, description="Emergency broadcast alert text")
    urgency: str = Field("HIGH", description="CRITICAL | HIGH | MEDIUM | LOW")


class SMSParsedResultOut(BaseModel):
    intent: str
    sender_phone: str
    urgency_level: int
    extracted_district: str | None
    extracted_location: str | None
    affected_people: int
    medical_needs: str | None
    ml_priority_score: float | None
    sos_id: int | None
    victim_id: int | None
    auto_reply_message: str
    action_taken: str


class SMSLogOut(BaseModel):
    id: int
    direction: str
    sender: str
    recipient: str
    message_text: str
    message_type: str
    parsed_intent: str | None
    sos_request_id: int | None
    victim_id: int | None
    status: str
    gateway_provider: str
    created_at: str

    model_config = {"from_attributes": True}


class SMSGatewayStatusOut(BaseModel):
    gateway_status: str
    active_carrier: str
    signal_strength: str
    total_inbound_processed: int
    total_outbound_sent: int
    active_emergency_alerts: int
    delivery_success_rate: float
    supported_keywords: list[str]
