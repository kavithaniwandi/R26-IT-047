"""
app/routers/sos.py
------------------
SOS submission, priority evaluation with Model 4, and list/filter endpoints.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
import re
from typing import List, Optional
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

logger = logging.getLogger(__name__)

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
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=7, max_length=30)
    relation: Optional[str] = "Emergency Contact"
    notifySMS: Optional[bool] = True
    notifyCall: Optional[bool] = False

class SOSAlertContactsRequest(BaseModel):
    sos_id: int
    priority_score: float
    victim_name: Optional[str] = "Victim"
    location_text: Optional[str] = "Sri Lanka"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contacts: Optional[List[EmergencyContactSMS]] = None


_PLACEHOLDER_PHONES = {
    "+94771234567",
    "+94718899112",
    "+94763456789",
    "+94709988776",
    "0771234567",
    "0718899112",
    "0763456789",
    "0709988776",
    "94771234567",
    "94718899112",
    "94763456789",
    "94709988776",
}


def _is_placeholder_phone(phone: str) -> bool:
    """Detect whether a phone number matches any of the legacy demo/placeholder numbers."""
    clean = re.sub(r"[\s\-\(\)\.]", "", str(phone or "").strip())
    return clean in _PLACEHOLDER_PHONES


def _get_user_saved_contacts(user: User) -> List[EmergencyContactSMS]:
    """Retrieve verified emergency contacts saved for a user, filtering out placeholder numbers."""
    if not user or not user.emergency_contacts:
        return []
    try:
        data = json.loads(user.emergency_contacts)
        if isinstance(data, list):
            valid = []
            for item in data:
                if isinstance(item, dict):
                    p = item.get("phone", "")
                    if p and not _is_placeholder_phone(p):
                        valid.append(EmergencyContactSMS(**item))
            return valid
    except Exception as exc:
        logger.warning("[SOS] Failed to parse emergency contacts for user %s: %s", getattr(user, "id", "?"), exc)
    return []


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
    token_data: TokenPayload = Depends(require_role(["victim", "authority", "admin", "volunteer"])),
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

    # ── Multi-channel notification audit record ──────────────────────────────
    notif = Notification(
        recipient_user_id=user_id,
        channel="SMS",
        message_type="SOS_ALERT",
        recipient_target=user.phone or "Emergency-Broadcast-911",
        message_content=(
            f"EMERGENCY ALERT: SOS #{sos.id} received from {user.full_name} "
            f"at ({sos.latitude:.4f}, {sos.longitude:.4f}). "
            f"Priority: {sos.priority_score}."
        ),
        dispatch_status="sent",
    )
    db.add(notif)
    db.commit()

    # ── Auto-dispatch SMS to user's saved emergency contacts ─────────────────
    # Runs immediately after SOS creation so contacts are notified even if the
    # frontend /alert-contacts call is delayed or skipped.
    # Errors are fully isolated — a SMS failure will never block the SOS response.
    try:
        saved_contacts = _get_user_saved_contacts(user)
        if saved_contacts:
            loc_text = (
                f"{sos.gn_division or sos.ds_division or ''}, {sos.district or 'Sri Lanka'}"
            ).strip(", ")
            sms_body = (
                f"[EMERGENCY SOS ALERT] {user.full_name or 'A victim'} has triggered "
                f"Distress Beacon #{sos.id} at {loc_text} "
                f"({sos.latitude:.4f}°N, {sos.longitude:.4f}°E). "
                f"Urgent relief/rescue needed! Priority: {round(sos.priority_score)}/100. "
                f"Emergency services (119/1990) dispatched. - Sri Lanka Disaster Relief System"
            )
            for contact in saved_contacts:
                phone = (contact.phone or "").strip()
                if not phone or _is_placeholder_phone(phone):
                    continue
                if not contact.notifySMS:
                    continue
                try:
                    sms_gateway.send_direct_sms(
                        recipient=phone,
                        message=sms_body,
                        message_type="SOS_EMERGENCY_CONTACT_ALERT",
                        db=db,
                    )
                    logger.info(
                        "[SOS-AUTOALERT] SMS dispatched to contact '%s' for SOS #%s",
                        contact.name, sos.id,
                    )
                except Exception as sms_exc:
                    logger.warning(
                        "[SOS-AUTOALERT] SMS to '%s' failed for SOS #%s: %s",
                        contact.name, sos.id, sms_exc,
                    )
        else:
            logger.info(
                "[SOS-AUTOALERT] No saved emergency contacts for user %s — skipping auto-SMS.",
                user_id,
            )
    except Exception as auto_sms_exc:
        logger.error(
            "[SOS-AUTOALERT] Unexpected error during auto-SMS dispatch for SOS #%s: %s",
            sos.id, auto_sms_exc,
        )

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

@router.get("", response_model=List[SOSOut])
def list_sos_requests(
    status_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
    min_priority: Optional[float] = None,
    token_data: TokenPayload = Depends(require_role(["authority", "admin", "volunteer", "victim"])),
    db: Session = Depends(get_db)
):
    """
    List SOS requests sorted by priority score descending.
    Victims can only retrieve their own SOS records (ownership check enforced).
    Authority, admin, and volunteer roles can view all SOS requests.
    """
    query = db.query(SOSRequest)
    if token_data.role == "victim":
        query = query.filter(SOSRequest.user_id == int(token_data.sub))
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


@router.get(
    "/contacts",
    response_model=List[EmergencyContactSMS],
    summary="Get authenticated user's saved emergency contacts (max 4)",
)
def get_user_emergency_contacts(
    token_data: TokenPayload = Depends(require_role(["victim", "authority", "admin", "volunteer"])),
    db: Session = Depends(get_db),
):
    """Retrieve verified emergency contacts saved for the authenticated user (max 4)."""
    user_id = int(token_data.sub)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _get_user_saved_contacts(user)


@router.put(
    "/contacts",
    response_model=List[EmergencyContactSMS],
    summary="Save authenticated user's emergency contacts (max 4, rejects placeholders)",
)
def update_user_emergency_contacts(
    contacts: List[EmergencyContactSMS],
    token_data: TokenPayload = Depends(require_role(["victim", "authority", "admin", "volunteer"])),
    db: Session = Depends(get_db),
):
    """Save up to 4 emergency contacts for the authenticated user. Never accepts placeholder numbers."""
    user_id = int(token_data.sub)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if len(contacts) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 4 emergency contacts is allowed.",
        )

    clean_contacts = []
    for idx, c in enumerate(contacts):
        p_clean = c.phone.strip()
        if not p_clean:
            continue
        if _is_placeholder_phone(p_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Placeholder phone number '{p_clean}' is not allowed. Please enter a real phone number.",
            )
        try:
            sms_gateway._validate_phone(p_clean)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Contact '{c.name}': {str(exc)}",
            )
        clean_contacts.append({
            "id": c.id or (idx + 1),
            "name": c.name.strip(),
            "phone": p_clean,
            "relation": (c.relation or "Emergency Contact").strip(),
            "notifySMS": c.notifySMS if c.notifySMS is not None else True,
            "notifyCall": c.notifyCall if c.notifyCall is not None else False,
        })

    user.emergency_contacts = json.dumps(clean_contacts)
    db.commit()
    db.refresh(user)
    return _get_user_saved_contacts(user)


@router.post(
    "/alert-contacts",
    status_code=status.HTTP_200_OK,
    summary="Dispatch emergency alert SMS to genuinely saved contacts of authenticated user",
)
def alert_emergency_contacts(
    payload: SOSAlertContactsRequest,
    token_data: TokenPayload = Depends(require_role(["victim", "authority", "admin", "volunteer"])),
    db: Session = Depends(get_db),
):
    """
    Send SMS alert messages ONLY to emergency contacts genuinely saved for the authenticated user.
    Rejects unauthenticated callers, mismatched SOS ownership, placeholder numbers,
    and untrusted arbitrary contact lists.
    """
    user_id = int(token_data.sub)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    sos = db.query(SOSRequest).filter(SOSRequest.id == payload.sos_id).first()
    if not sos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS request not found.")

    # Authorization check: user must own this SOS request (or be admin/authority)
    user_role = token_data.role if hasattr(token_data, "role") else None
    if sos.user_id != user_id and user_role not in ("admin", "authority"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot dispatch alerts for another user's SOS request.",
        )

    # Use the genuinely saved emergency contacts from the authenticated user profile
    saved_contacts = _get_user_saved_contacts(user)
    if not saved_contacts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No saved emergency contacts found for this account. Please add contacts first.",
        )

    # If payload specified contacts, ensure we ONLY alert contacts genuinely saved for this user
    target_contacts: List[EmergencyContactSMS] = []
    if payload.contacts:
        saved_phone_map = {
            re.sub(r"[\s\-\(\)\.]", "", sc.phone.strip()): sc
            for sc in saved_contacts
        }
        for requested in payload.contacts:
            req_clean = re.sub(r"[\s\-\(\)\.]", "", requested.phone.strip())
            if req_clean in saved_phone_map:
                target_contacts.append(saved_phone_map[req_clean])
            else:
                logger.warning(
                    "[SOS-ALERT] Rejecting untrusted phone '%s' — not in saved contacts for user %s",
                    requested.phone,
                    user_id,
                )
    else:
        target_contacts = saved_contacts

    if not target_contacts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid registered emergency contacts to alert.",
        )

    sent_to = []
    for contact in target_contacts:
        phone = contact.phone.strip()
        if not phone or _is_placeholder_phone(phone):
            continue

        loc_text = payload.location_text or f"{sos.gn_division or ''}, {sos.district or 'Sri Lanka'}"
        lat = payload.latitude if payload.latitude is not None else sos.latitude
        lng = payload.longitude if payload.longitude is not None else sos.longitude
        v_name = payload.victim_name or user.full_name or "Victim"

        message = (
            f"[EMERGENCY SOS ALERT] {v_name} has triggered Distress Beacon "
            f"#{sos.id} at {loc_text} "
            f"({lat:.4f}°N, {lng:.4f}°E). "
            f"Urgent medical relief/rescue needed! Priority: {round(sos.priority_score)}/100. "
            f"Emergency services (119/1990) dispatched. - Sri Lanka Disaster Relief System"
        )

        try:
            sms_log = sms_gateway.send_direct_sms(
                recipient=phone,
                message=message,
                message_type="SOS_EMERGENCY_CONTACT_ALERT",
                db=db,
            )
            # sms_log.status is 'simulated' when TEXTLK_ENABLED=false,
            # 'sent' when accepted by provider, or 'failed' on error.
            sent_to.append({
                "phone": phone,
                "name": contact.name,
                "status": sms_log.status,
                "provider": sms_log.gateway_provider or "LOCAL",
            })
        except Exception as exc:
            sent_to.append({
                "phone": phone,
                "name": contact.name,
                "status": f"error: {str(exc)}",
                "provider": "LOCAL",
            })

    successfully_dispatched = [
        c for c in sent_to if c["status"] not in ("failed",) and not c["status"].startswith("error")
    ]
    return {
        "sos_id": payload.sos_id,
        "contacts_alerted": len(successfully_dispatched),
        "total_contacts": len(target_contacts),
        "dispatch_log": sent_to,
        "message": f"SOS alert processed for {len(successfully_dispatched)}/{len(target_contacts)} emergency contacts.",
    }


@router.get("/{sos_id}", response_model=SOSOut)
def get_sos_request(
    sos_id: int,
    token_data: TokenPayload = Depends(require_role(["authority", "admin", "volunteer", "victim"])),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific SOS record.
    Victims can only access their own SOS records (ownership enforced).
    Authority, admin, and volunteer roles can view any SOS record.
    """
    sos = db.query(SOSRequest).filter(SOSRequest.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS request not found.")

    if token_data.role == "victim" and sos.user_id != int(token_data.sub):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot access another user's private SOS record.",
        )

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

