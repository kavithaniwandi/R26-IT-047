"""
app/routers/sms.py
------------------
SMS Gateway router for handling inbound carrier webhooks, interactive test simulations,
emergency outbound alerts, and multi-subscriber broadcast dispatches.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.database import get_db
from app.models.sms_log import SMSMessageLog
from app.schemas.sms import (
    InboundSMSRequest,
    SimulateInboundSMSRequest,
    SendSMSRequest,
    BroadcastSMSRequest,
    SMSParsedResultOut,
    SMSLogOut,
    SMSGatewayStatusOut,
)
from app.services import sms_gateway

router = APIRouter(prefix="/sms", tags=["Telecom SMS Gateway"])


@router.post(
    "/webhook",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Carrier webhook for inbound SMS messages",
    description="Receives MO (Mobile Originated) SMS from telecom provider (Dialog/Mobitel/Airtel/Hutch), parses emergency intent, triggers Model 4 priority scoring, and dispatches MT (Mobile Terminated) auto-reply.",
)
def inbound_sms_webhook(
    payload: InboundSMSRequest,
    db: Session = Depends(get_db),
):
    _, result = sms_gateway.process_incoming_sms(
        sender=payload.sender,
        message_text=payload.message,
        recipient=payload.recipient,
        provider=payload.provider,
        db=db,
    )
    return SMSParsedResultOut(**result)


@router.post(
    "/incoming",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Alternative alias for inbound SMS webhook",
)
def inbound_sms_incoming(
    payload: InboundSMSRequest,
    db: Session = Depends(get_db),
):
    _, result = sms_gateway.process_incoming_sms(
        sender=payload.sender,
        message_text=payload.message,
        recipient=payload.recipient,
        provider=payload.provider,
        db=db,
    )
    return SMSParsedResultOut(**result)


@router.post(
    "/simulate-inbound",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Simulate incoming SMS from victim for demonstration & testing",
    description="Interactive endpoint to test emergency SMS parsing (SOS, REG, STATUS, CAMP, HELP) without requiring actual cellular SIM modems.",
)
def simulate_inbound_sms(
    payload: SimulateInboundSMSRequest,
    db: Session = Depends(get_db),
):
    _, result = sms_gateway.process_incoming_sms(
        sender=payload.sender,
        message_text=payload.message,
        recipient="1919",
        provider=payload.provider,
        db=db,
    )
    return SMSParsedResultOut(**result)


@router.post(
    "/send",
    response_model=SMSLogOut,
    dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))],
    status_code=status.HTTP_200_OK,
    summary="Send direct emergency outbound SMS to a phone number",
)
def send_sms_endpoint(
    payload: SendSMSRequest,
    db: Session = Depends(get_db),
):
    sms = sms_gateway.send_direct_sms(
        recipient=payload.recipient,
        message=payload.message,
        message_type=payload.message_type,
        db=db,
    )
    return SMSLogOut(
        id=sms.id,
        direction=sms.direction,
        sender=sms.sender,
        recipient=sms.recipient,
        message_text=sms.message_text,
        message_type=sms.message_type,
        parsed_intent=sms.parsed_intent,
        sos_request_id=sms.sos_request_id,
        victim_id=sms.victim_id,
        status=sms.status,
        gateway_provider=sms.gateway_provider,
        created_at=sms.created_at.isoformat(),
    )


@router.post(
    "/broadcast",
    dependencies=[Depends(require_role(["authority", "admin"]))],
    status_code=status.HTTP_200_OK,
    summary="Broadcast critical disaster alert SMS to registered victims/responders",
)
def broadcast_sms_endpoint(
    payload: BroadcastSMSRequest,
    db: Session = Depends(get_db),
):
    dispatched_count = sms_gateway.broadcast_emergency_sms(
        message=payload.message,
        district=payload.district,
        role=payload.role,
        urgency=payload.urgency,
        db=db,
    )
    return {
        "status": "success",
        "recipients_count": dispatched_count,
        "message": f"Broadcast alert successfully transmitted to {dispatched_count} recipients via SMS gateway.",
    }


@router.get(
    "/logs",
    response_model=List[SMSLogOut],
    dependencies=[Depends(require_role(["authority", "admin"]))],
    summary="List SMS transmission logs with direction and delivery status",
)
def get_sms_logs_endpoint(
    direction: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(SMSMessageLog)
    if direction:
        query = query.filter(SMSMessageLog.direction == direction)
    logs = query.order_by(SMSMessageLog.created_at.desc()).limit(limit).all()

    return [
        SMSLogOut(
            id=log.id,
            direction=log.direction,
            sender=log.sender,
            recipient=log.recipient,
            message_text=log.message_text,
            message_type=log.message_type,
            parsed_intent=log.parsed_intent,
            sos_request_id=log.sos_request_id,
            victim_id=log.victim_id,
            status=log.status,
            gateway_provider=log.gateway_provider,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.get(
    "/gateway-status",
    response_model=SMSGatewayStatusOut,
    summary="Get telecom SMS gateway connection status and metrics",
)
def get_sms_gateway_status_endpoint(db: Session = Depends(get_db)):
    status_data = sms_gateway.get_gateway_telecom_status(db)
    return SMSGatewayStatusOut(**status_data)
