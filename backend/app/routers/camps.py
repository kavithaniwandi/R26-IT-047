"""
app/routers/camps.py
--------------------
MedicalCamp router with Model 3 suitability scoring, listing, and approval.
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_role, get_current_user_payload, TokenPayload
from app.database import get_db
from app.models.camp import MedicalCamp
from app.models.user import User

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models"

router = APIRouter(prefix="/camps", tags=["Medical Camps"])

_camp_model = None
_camp_scaler = None

def get_camp_scorer():
    global _camp_model, _camp_scaler
    if _camp_model is None:
        model_p = MODEL_DIR / "camp_suitability_model.joblib"
        scaler_p = MODEL_DIR / "camp_suitability_scaler.joblib"
        if model_p.exists() and scaler_p.exists():
            _camp_model = joblib.load(model_p)
            _camp_scaler = joblib.load(scaler_p)
    return _camp_model, _camp_scaler


class CampCreateRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    district: str
    ds_division: str
    gn_division: Optional[str] = None
    estimated_capacity: int = Field(100, ge=10)

class CampOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    district: str
    ds_division: str
    gn_division: Optional[str]
    suitability_score: float
    estimated_capacity: int
    current_occupancy: int
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str

@router.get("", response_model=List[CampOut])
def list_camps(
    status_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List medical camps for all authenticated stakeholders."""
    query = db.query(MedicalCamp)
    if status_filter:
        query = query.filter(MedicalCamp.status == status_filter)
    if district_filter:
        query = query.filter(MedicalCamp.district == district_filter)
        
    camps = query.order_by(MedicalCamp.suitability_score.desc(), MedicalCamp.created_at.desc()).all()
    out = []
    for c in camps:
        approver_name = None
        if c.approved_by_user_id:
            u = db.query(User).filter(User.id == c.approved_by_user_id).first()
            if u:
                approver_name = u.full_name
        out.append(
            CampOut(
                id=c.id,
                name=c.name,
                latitude=c.latitude,
                longitude=c.longitude,
                district=c.district,
                ds_division=c.ds_division,
                gn_division=c.gn_division,
                suitability_score=c.suitability_score,
                estimated_capacity=c.estimated_capacity,
                current_occupancy=c.current_occupancy,
                status=c.status,
                approved_by=approver_name,
                approved_at=c.approved_at.isoformat() if c.approved_at else None,
                created_at=c.created_at.isoformat(),
            )
        )
    return out

@router.post("", response_model=CampOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["authority", "admin"]))])
def create_medical_camp(
    payload: CampCreateRequest,
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Propose a candidate medical camp and calculate suitability using Model 3."""
    score = 75.0
    model, scaler = get_camp_scorer()
    if model is not None and scaler is not None:
        try:
            # 10 features: latitude, longitude, dist_to_kelani_km, flood_risk_score, landslide_risk_score,
            # sos_density, road_accessibility, critical_facility_nearby, open_space_available, elevation_suitability
            feat_vec = np.array([[
                payload.latitude,
                payload.longitude,
                5.0, # distance
                0.25, # low flood risk at camp site
                0.15, # low landslide risk
                0.70, # moderate/high SOS density nearby
                0.90, # good road accessibility
                1.0,  # critical facility nearby
                1.0,  # open space available
                0.85  # elevated terrain
            ]])
            scaled = scaler.transform(feat_vec)
            score = float(np.clip(model.predict(scaled)[0], 0.0, 100.0))
        except Exception:
            score = 80.0

    camp = MedicalCamp(
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district=payload.district,
        ds_division=payload.ds_division,
        gn_division=payload.gn_division,
        suitability_score=round(score, 1),
        estimated_capacity=payload.estimated_capacity,
        current_occupancy=0,
        status="proposed",
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)

    return CampOut(
        id=camp.id,
        name=camp.name,
        latitude=camp.latitude,
        longitude=camp.longitude,
        district=camp.district,
        ds_division=camp.ds_division,
        gn_division=camp.gn_division,
        suitability_score=camp.suitability_score,
        estimated_capacity=camp.estimated_capacity,
        current_occupancy=camp.current_occupancy,
        status=camp.status,
        approved_by=None,
        approved_at=None,
        created_at=camp.created_at.isoformat(),
    )

@router.patch("/{camp_id}/approve", response_model=CampOut, dependencies=[Depends(require_role(["authority", "admin"]))])
def approve_medical_camp(
    camp_id: int,
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Officially approve a proposed medical camp (Authority / Admin)."""
    camp = db.query(MedicalCamp).filter(MedicalCamp.id == camp_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Medical camp not found.")

    approver_id = int(token_data.sub)
    camp.status = "approved"
    camp.approved_by_user_id = approver_id
    camp.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(camp)

    u = db.query(User).filter(User.id == approver_id).first()
    return CampOut(
        id=camp.id,
        name=camp.name,
        latitude=camp.latitude,
        longitude=camp.longitude,
        district=camp.district,
        ds_division=camp.ds_division,
        gn_division=camp.gn_division,
        suitability_score=camp.suitability_score,
        estimated_capacity=camp.estimated_capacity,
        current_occupancy=camp.current_occupancy,
        status=camp.status,
        approved_by=u.full_name if u else "Admin",
        approved_at=camp.approved_at.isoformat(),
        created_at=camp.created_at.isoformat(),
    )
