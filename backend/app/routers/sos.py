"""
app/routers/sos.py
------------------
SOS submission, priority evaluation with Model 4, and list/filter endpoints.
"""
from __future__ import annotations
from typing import List, Optional
from pathlib import Path
import json
import joblib
import numpy as np
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_role, get_current_user_payload, TokenPayload
from app.database import get_db
from app.models.sos import SOSRequest
from app.models.user import User
from app.models.notification import Notification
from app.services import sms_gateway

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models"

router = APIRouter(prefix="/sos", tags=["Emergency SOS"])

# Load Priority Scorer once
_priority_model = None
_priority_scaler = None

def get_priority_scorer():
    global _priority_model, _priority_scaler
    if _priority_model is None:
        model_p = MODEL_DIR / "priority_score_model.joblib"
        scaler_p = MODEL_DIR / "priority_score_scaler.joblib"
        if model_p.exists() and scaler_p.exists():
            _priority_model = joblib.load(model_p)
            _priority_scaler = joblib.load(scaler_p)
    return _priority_model, _priority_scaler


class SOSCreateRequest(BaseModel):
    latitude: float
    longitude: float
    district: Optional[str] = "Colombo"
    ds_division: Optional[str] = "Kaduwela"
    gn_division: Optional[str] = None
    address_text: Optional[str] = None
    urgency_level: int = Field(..., ge=1, le=5)
    affected_people: int = Field(1, ge=1)
    affected_families: int = Field(1, ge=1)
    has_elderly: bool = False
    has_children: bool = False
    has_disabled: bool = False
    medical_needs_summary: Optional[str] = None

class SOSStatusUpdateRequest(BaseModel):
    status: str # 'active', 'triaged', 'camp_assigned', 'resolved', 'cancelled'

class EmergencyContactSMS(BaseModel):
    name: str
    phone: str
    relation: Optional[str] = "Emergency Contact"

class SOSAlertContactsRequest(BaseModel):
    sos_id: int
    priority_score: float
    victim_name: str
    location_text: str
    latitude: float
    longitude: float
    contacts: List[EmergencyContactSMS]


class SOSOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    latitude: float
    longitude: float
    district: Optional[str]
    ds_division: Optional[str]
    gn_division: Optional[str]
    address_text: Optional[str]
    urgency_level: int
    affected_people: int
    affected_families: int
    has_elderly: bool
    has_children: bool
    has_disabled: bool
    medical_needs_summary: Optional[str]
    priority_score: float
    status: str
    created_at: str

@router.post("", response_model=SOSOut, status_code=status.HTTP_201_CREATED)
def submit_sos(
    payload: SOSCreateRequest,
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Submit an emergency SOS alert. Computes ML priority score via Model 4."""
    user_id = int(token_data.sub)
    user = db.query(User).filter(User.id == user_id).first()

    # Model 4 Inference
    priority = 50.0
    model, scaler = get_priority_scorer()
    if model is not None and scaler is not None:
        try:
            # 11 features: urgency, affected_people, affected_families, has_elderly, has_children,
            # has_disabled, medical_needs_count, flood_risk_score, landslide_risk_score, hours_since_sos, access_difficulty
            med_count = len([x for x in (payload.medical_needs_summary or "").split(",") if x.strip()])
            feat_vec = np.array([[
                float(payload.urgency_level),
                float(payload.affected_people),
                float(payload.affected_families),
                1.0 if payload.has_elderly else 0.0,
                1.0 if payload.has_children else 0.0,
                1.0 if payload.has_disabled else 0.0,
                float(med_count),
                0.65, # default area risk estimate
                0.35,
                0.0,  # 0 hours elapsed
                0.5   # average access
            ]])
            scaled = scaler.transform(feat_vec)
            priority = float(np.clip(model.predict(scaled)[0], 0.0, 100.0))
        except Exception:
            priority = float(payload.urgency_level * 18.0)

    sos = SOSRequest(
        user_id=user_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district=payload.district,
        ds_division=payload.ds_division,
        gn_division=payload.gn_division,
        address_text=payload.address_text,
        urgency_level=payload.urgency_level,
        affected_people=payload.affected_people,
        affected_families=payload.affected_families,
        has_elderly=payload.has_elderly,
        has_children=payload.has_children,
        has_disabled=payload.has_disabled,
        medical_needs_summary=payload.medical_needs_summary,
        priority_score=round(priority, 1),
        status="active",
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)

    # Multi-channel notification audit record
    notif = Notification(
        recipient_user_id=user_id,
        channel="SMS",
        message_type="SOS_ALERT",
        recipient_target=user.phone or "Emergency-Broadcast-911",
        message_content=f"EMERGENCY ALERT: SOS #{sos.id} received from {user.full_name} at ({sos.latitude:.4f}, {sos.longitude:.4f}). Priority: {sos.priority_score}.",
        dispatch_status="sent",
    )
    db.add(notif)
    db.commit()

    return SOSOut(
        id=sos.id,
        user_id=sos.user_id,
        user_name=user.full_name if user else None,
        user_phone=user.phone if user else None,
        latitude=sos.latitude,
        longitude=sos.longitude,
        district=sos.district,
        ds_division=sos.ds_division,
        gn_division=sos.gn_division,
        address_text=sos.address_text,
        urgency_level=sos.urgency_level,
        affected_people=sos.affected_people,
        affected_families=sos.affected_families,
        has_elderly=sos.has_elderly,
        has_children=sos.has_children,
        has_disabled=sos.has_disabled,
        medical_needs_summary=sos.medical_needs_summary,
        priority_score=sos.priority_score,
        status=sos.status,
        created_at=sos.created_at.isoformat(),
    )

@router.get("", response_model=List[SOSOut], dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))])
def list_sos_requests(
    status_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
    min_priority: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List SOS requests sorted by priority score descending."""
    query = db.query(SOSRequest)
    if status_filter:
        query = query.filter(SOSRequest.status == status_filter)
    if district_filter:
        query = query.filter(SOSRequest.district == district_filter)
    if min_priority is not None:
        query = query.filter(SOSRequest.priority_score >= min_priority)
        
    results = query.order_by(SOSRequest.priority_score.desc(), SOSRequest.created_at.desc()).all()
    out = []
    for s in results:
        u = db.query(User).filter(User.id == s.user_id).first()
        out.append(
            SOSOut(
                id=s.id,
                user_id=s.user_id,
                user_name=u.full_name if u else None,
                user_phone=u.phone if u else None,
                latitude=s.latitude,
                longitude=s.longitude,
                district=s.district,
                ds_division=s.ds_division,
                gn_division=s.gn_division,
                address_text=s.address_text,
                urgency_level=s.urgency_level,
                affected_people=s.affected_people,
                affected_families=s.affected_families,
                has_elderly=s.has_elderly,
                has_children=s.has_children,
                has_disabled=s.has_disabled,
                medical_needs_summary=s.medical_needs_summary,
                priority_score=s.priority_score,
                status=s.status,
                created_at=s.created_at.isoformat(),
            )
        )
    return out

@router.patch("/{sos_id}/status", response_model=SOSOut, dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))])
def update_sos_status(sos_id: int, payload: SOSStatusUpdateRequest, db: Session = Depends(get_db)):
    """Update status of an SOS request (e.g. active -> triaged -> resolved)."""
    sos = db.query(SOSRequest).filter(SOSRequest.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found.")
    
    sos.status = payload.status
    db.commit()
    db.refresh(sos)
    u = db.query(User).filter(User.id == sos.user_id).first()
    return SOSOut(
        id=sos.id,
        user_id=sos.user_id,
        user_name=u.full_name if u else None,
        user_phone=u.phone if u else None,
        latitude=sos.latitude,
        longitude=sos.longitude,
        district=sos.district,
        ds_division=sos.ds_division,
        gn_division=sos.gn_division,
        address_text=sos.address_text,
        urgency_level=sos.urgency_level,
        affected_people=sos.affected_people,
        affected_families=sos.affected_families,
        has_elderly=sos.has_elderly,
        has_children=sos.has_children,
        has_disabled=sos.has_disabled,
        medical_needs_summary=sos.medical_needs_summary,
        priority_score=sos.priority_score,
        status=sos.status,
        created_at=sos.created_at.isoformat(),
    )


@router.post("/alert-contacts", status_code=status.HTTP_200_OK)
def alert_emergency_contacts(
    payload: SOSAlertContactsRequest,
    db: Session = Depends(get_db),
):
    """
    Send real SMS alert messages to all provided emergency contacts.
    Works with any number of contacts (1 to N) — no minimum required.
    Each contact receives a personalized message with SOS ID, GPS coordinates,
    priority score and victim details, dispatched via the SMS gateway service.
    """
    if not payload.contacts:
        raise HTTPException(status_code=400, detail="At least 1 emergency contact is required.")

    sent_to = []
    for contact in payload.contacts:
        phone = contact.phone.strip()
        if not phone:
            continue

        message = (
            f"[EMERGENCY SOS ALERT] {payload.victim_name} has triggered Distress Beacon "
            f"#{payload.sos_id} at {payload.location_text} "
            f"({payload.latitude:.4f}°N, {payload.longitude:.4f}°E). "
            f"Urgent medical relief/rescue needed! Priority: {round(payload.priority_score)}/100. "
            f"Emergency services (119/1990) dispatched. - Sri Lanka Disaster Relief System"
        )

        try:
            sms_gateway.send_direct_sms(
                recipient=phone,
                message=message,
                message_type="SOS_EMERGENCY_CONTACT_ALERT",
                db=db,
            )
            sent_to.append({"phone": phone, "name": contact.name, "status": "sent"})
        except Exception as exc:
            sent_to.append({"phone": phone, "name": contact.name, "status": f"error: {str(exc)}"})

    return {
        "sos_id": payload.sos_id,
        "contacts_alerted": len([c for c in sent_to if c["status"] == "sent"]),
        "total_contacts": len(payload.contacts),
        "dispatch_log": sent_to,
        "message": f"SOS alert dispatched to {len([c for c in sent_to if c['status'] == 'sent'])}/{len(payload.contacts)} emergency contacts.",
    }
