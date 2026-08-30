"""
app/routers/sms.py
------------------
SMS Gateway router — handles:
  POST /sms/webhook              → Carrier SMSC inbound webhook (MO)
  POST /sms/incoming             → Alias for webhook (backward-compat)
  POST /sms/simulate-inbound     → Interactive demo / test simulator
  POST /sms/send                 → Outbound direct SMS (authority/admin/volunteer)
  POST /sms/broadcast            → Bulk emergency alert broadcast (authority/admin)
  GET  /sms/logs                 → Paginated SMS transaction logs
  GET  /sms/gateway-status       → Live Twilio gateway metrics
"""
from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sms", tags=["Telecom SMS Gateway"])


# ---------------------------------------------------------------------------
# Carrier Webhook — Inbound SMS (MO)
# ---------------------------------------------------------------------------

@router.post(
    "/webhook",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Carrier SMSC webhook for inbound SMS (MO)",
    description=(
        "Receives Mobile-Originated (MO) SMS from Dialog/Mobitel/Airtel carrier SMSC. "
        "Parses emergency intent, triggers ML urgency scoring, and dispatches "
        "Mobile-Terminated (MT) auto-reply via Twilio. "
        "This endpoint must be registered as the webhook URL in your Twilio console."
    ),
)
def inbound_sms_webhook(
    payload: InboundSMSRequest,
    db: Session = Depends(get_db),
):
    try:
        _, result = sms_gateway.process_incoming_sms(
            sender=payload.sender,
            message_text=payload.message,
            recipient=payload.recipient,
            provider=payload.provider,
            db=db,
        )
        return SMSParsedResultOut(**result)
    except Exception as exc:
        logger.exception("[SMS-WEBHOOK] Unhandled error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS processing failed: {str(exc)}",
        ) from exc


@router.post(
    "/incoming",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Alias for inbound SMS webhook (backward-compatible)",
)
def inbound_sms_incoming(
    payload: InboundSMSRequest,
    db: Session = Depends(get_db),
):
    try:
        _, result = sms_gateway.process_incoming_sms(
            sender=payload.sender,
            message_text=payload.message,
            recipient=payload.recipient,
            provider=payload.provider,
            db=db,
        )
        return SMSParsedResultOut(**result)
    except Exception as exc:
        logger.exception("[SMS-INCOMING] Unhandled error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS processing failed: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Simulation endpoint (demo / dev testing)
# ---------------------------------------------------------------------------

@router.post(
    "/simulate-inbound",
    response_model=SMSParsedResultOut,
    status_code=status.HTTP_200_OK,
    summary="Simulate incoming SMS from a victim (demo & testing)",
    description=(
        "Interactive endpoint to test emergency SMS parsing (SOS, REG, STATUS, CAMP, HELP) "
        "without requiring actual cellular SIM modems or a Twilio account. "
        "When TWILIO_ENABLED=false in .env, the auto-reply is logged but not actually sent — "
        "perfect for development and demonstrations."
    ),
)
def simulate_inbound_sms(
    payload: SimulateInboundSMSRequest,
    db: Session = Depends(get_db),
):
    try:
        _, result = sms_gateway.process_incoming_sms(
            sender=payload.sender,
            message_text=payload.message,
            recipient="1919",
            provider=payload.provider,
            db=db,
        )
        return SMSParsedResultOut(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("[SMS-SIMULATE] Unhandled error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS simulation failed: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Direct outbound SMS
# ---------------------------------------------------------------------------

@router.post(
    "/send",
    response_model=SMSLogOut,
    dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))],
    status_code=status.HTTP_200_OK,
    summary="Send direct outbound emergency SMS to a phone number",
    description=(
        "Sends a targeted SMS to a single recipient. "
        "Phone number must be in E.164 format (e.g. +94771234567). "
        "Requires authority, admin, or volunteer role."
    ),
)
def send_sms_endpoint(
    payload: SendSMSRequest,
    db: Session = Depends(get_db),
):
    try:
        sms = sms_gateway.send_direct_sms(
            recipient=payload.recipient,
            message=payload.message,
            message_type=payload.message_type,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("[SMS-SEND] Unhandled error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS dispatch failed: {str(exc)}",
        ) from exc

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


# ---------------------------------------------------------------------------
# Broadcast SMS
# ---------------------------------------------------------------------------

@router.post(
    "/broadcast",
    dependencies=[Depends(require_role(["authority", "admin"]))],
    status_code=status.HTTP_200_OK,
    summary="Broadcast critical disaster alert SMS to registered victims/responders",
    description=(
        "Sends an emergency broadcast SMS to all registered victims or users in the target district. "
        "Each recipient gets an individually dispatched message and delivery log entry. "
        "Requires authority or admin role."
    ),
)
def broadcast_sms_endpoint(
    payload: BroadcastSMSRequest,
    db: Session = Depends(get_db),
):
    try:
        dispatched_count = sms_gateway.broadcast_emergency_sms(
            message=payload.message,
            district=payload.district,
            role=payload.role,
            urgency=payload.urgency,
            db=db,
        )
    except Exception as exc:
        logger.exception("[SMS-BROADCAST] Unhandled error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Broadcast failed: {str(exc)}",
        ) from exc

    return {
        "status": "success",
        "recipients_count": dispatched_count,
        "message": (
            f"Broadcast alert transmitted to {dispatched_count} recipients via SMS gateway."
        ),
    }


# ---------------------------------------------------------------------------
# SMS Logs
# ---------------------------------------------------------------------------

@router.get(
    "/logs",
    response_model=List[SMSLogOut],
    dependencies=[Depends(require_role(["authority", "admin"]))],
    summary="List SMS transmission logs with direction and delivery status",
)
def get_sms_logs_endpoint(
    direction: Optional[str] = Query(None, description="Filter by 'inbound' or 'outbound'"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: sent, simulated, failed, received, processed"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    db: Session = Depends(get_db),
):
    query = db.query(SMSMessageLog)
    if direction:
        query = query.filter(SMSMessageLog.direction == direction)
    if status_filter:
        query = query.filter(SMSMessageLog.status == status_filter)
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


# ---------------------------------------------------------------------------
# Gateway Status
# ---------------------------------------------------------------------------

@router.get(
    "/gateway-status",
    response_model=SMSGatewayStatusOut,
    summary="Get live Twilio SMS gateway connection status and metrics",
)
def get_sms_gateway_status_endpoint(db: Session = Depends(get_db)):
    status_data = sms_gateway.get_gateway_telecom_status(db)
    return SMSGatewayStatusOut(**status_data)
