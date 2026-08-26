"""
app/routers/victims.py
----------------------
API router for disaster victim self-registration, demographic intake,
vulnerability ranking, and emergency medical camp assignments.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_role, get_current_user_payload, TokenPayload
from app.database import get_db
from app.schemas.victim import (
    VictimCreateRequest,
    VictimUpdateRequest,
    VictimAssignCampRequest,
    VictimOut,
    VictimStatsOut,
)
from app.services import victim_service

router = APIRouter(prefix="/victims", tags=["Victim Registry & Intake"])


@router.post(
    "/register",
    response_model=VictimOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a disaster victim / household",
    description="Public or authenticated self-registration for disaster victims with automatic vulnerability calculation.",
)
def register_victim_endpoint(
    payload: VictimCreateRequest,
    db: Session = Depends(get_db),
):
    victim = victim_service.register_victim(payload, db)
    return VictimOut(
        id=victim.id,
        user_id=victim.user_id,
        nic=victim.nic,
        full_name=victim.full_name,
        phone=victim.phone,
        alternate_phone=victim.alternate_phone,
        gender=victim.gender,
        age=victim.age,
        district=victim.district,
        ds_division=victim.ds_division,
        gn_division=victim.gn_division,
        current_address=victim.current_address,
        latitude=victim.latitude,
        longitude=victim.longitude,
        family_members_count=victim.family_members_count,
        children_count=victim.children_count,
        elderly_count=victim.elderly_count,
        disabled_count=victim.disabled_count,
        pregnant_lactating_count=victim.pregnant_lactating_count,
        evacuation_status=victim.evacuation_status,
        assigned_camp_id=victim.assigned_camp_id,
        assigned_camp_name=victim.assigned_camp.name if victim.assigned_camp else None,
        chronic_diseases=victim.chronic_diseases,
        immediate_medical_needs=victim.immediate_medical_needs,
        dietary_and_relief_needs=victim.dietary_and_relief_needs,
        vulnerability_score=victim.vulnerability_score,
        registered_via=victim.registered_via,
        is_verified=victim.is_verified,
        notes=victim.notes,
        created_at=victim.created_at.isoformat(),
        updated_at=victim.updated_at.isoformat(),
    )


@router.get(
    "",
    response_model=List[VictimOut],
    dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))],
    summary="List registered victims with multi-criteria filtering",
)
def list_victims_endpoint(
    district: Optional[str] = None,
    evacuation_status: Optional[str] = None,
    min_vulnerability: Optional[float] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    victims, _ = victim_service.list_victims(
        db=db,
        district=district,
        evacuation_status=evacuation_status,
        min_vulnerability=min_vulnerability,
        is_verified=is_verified,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [
        VictimOut(
            id=v.id,
            user_id=v.user_id,
            nic=v.nic,
            full_name=v.full_name,
            phone=v.phone,
            alternate_phone=v.alternate_phone,
            gender=v.gender,
            age=v.age,
            district=v.district,
            ds_division=v.ds_division,
            gn_division=v.gn_division,
            current_address=v.current_address,
            latitude=v.latitude,
            longitude=v.longitude,
            family_members_count=v.family_members_count,
            children_count=v.children_count,
            elderly_count=v.elderly_count,
            disabled_count=v.disabled_count,
            pregnant_lactating_count=v.pregnant_lactating_count,
            evacuation_status=v.evacuation_status,
            assigned_camp_id=v.assigned_camp_id,
            assigned_camp_name=v.assigned_camp.name if v.assigned_camp else None,
            chronic_diseases=v.chronic_diseases,
            immediate_medical_needs=v.immediate_medical_needs,
            dietary_and_relief_needs=v.dietary_and_relief_needs,
            vulnerability_score=v.vulnerability_score,
            registered_via=v.registered_via,
            is_verified=v.is_verified,
            notes=v.notes,
            created_at=v.created_at.isoformat(),
            updated_at=v.updated_at.isoformat(),
        )
        for v in victims
    ]


@router.get(
    "/stats/summary",
    response_model=VictimStatsOut,
    dependencies=[Depends(require_role(["authority", "admin"]))],
    summary="Get aggregated victim demographics and vulnerability summary",
)
def get_victim_stats_endpoint(db: Session = Depends(get_db)):
    stats = victim_service.get_victim_stats(db)
    return VictimStatsOut(**stats)


@router.get(
    "/{victim_id}",
    response_model=VictimOut,
    dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))],
    summary="Get specific victim details by ID",
)
def get_victim_by_id_endpoint(victim_id: int, db: Session = Depends(get_db)):
    from app.models.victim import Victim
    victim = db.query(Victim).filter(Victim.id == victim_id).first()
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found.")
    return VictimOut(
        id=victim.id,
        user_id=victim.user_id,
        nic=victim.nic,
        full_name=victim.full_name,
        phone=victim.phone,
        alternate_phone=victim.alternate_phone,
        gender=victim.gender,
        age=victim.age,
        district=victim.district,
        ds_division=victim.ds_division,
        gn_division=victim.gn_division,
        current_address=victim.current_address,
        latitude=victim.latitude,
        longitude=victim.longitude,
        family_members_count=victim.family_members_count,
        children_count=victim.children_count,
        elderly_count=victim.elderly_count,
        disabled_count=victim.disabled_count,
        pregnant_lactating_count=victim.pregnant_lactating_count,
        evacuation_status=victim.evacuation_status,
        assigned_camp_id=victim.assigned_camp_id,
        assigned_camp_name=victim.assigned_camp.name if victim.assigned_camp else None,
        chronic_diseases=victim.chronic_diseases,
        immediate_medical_needs=victim.immediate_medical_needs,
        dietary_and_relief_needs=victim.dietary_and_relief_needs,
        vulnerability_score=victim.vulnerability_score,
        registered_via=victim.registered_via,
        is_verified=victim.is_verified,
        notes=victim.notes,
        created_at=victim.created_at.isoformat(),
        updated_at=victim.updated_at.isoformat(),
    )


@router.patch(
    "/{victim_id}",
    response_model=VictimOut,
    dependencies=[Depends(require_role(["authority", "admin"]))],
    summary="Update victim profile details",
)
def update_victim_endpoint(
    victim_id: int,
    payload: VictimUpdateRequest,
    db: Session = Depends(get_db),
):
    victim = victim_service.update_victim(victim_id, payload, db)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found.")
    return VictimOut(
        id=victim.id,
        user_id=victim.user_id,
        nic=victim.nic,
        full_name=victim.full_name,
        phone=victim.phone,
        alternate_phone=victim.alternate_phone,
        gender=victim.gender,
        age=victim.age,
        district=victim.district,
        ds_division=victim.ds_division,
        gn_division=victim.gn_division,
        current_address=victim.current_address,
        latitude=victim.latitude,
        longitude=victim.longitude,
        family_members_count=victim.family_members_count,
        children_count=victim.children_count,
        elderly_count=victim.elderly_count,
        disabled_count=victim.disabled_count,
        pregnant_lactating_count=victim.pregnant_lactating_count,
        evacuation_status=victim.evacuation_status,
        assigned_camp_id=victim.assigned_camp_id,
        assigned_camp_name=victim.assigned_camp.name if victim.assigned_camp else None,
        chronic_diseases=victim.chronic_diseases,
        immediate_medical_needs=victim.immediate_medical_needs,
        dietary_and_relief_needs=victim.dietary_and_relief_needs,
        vulnerability_score=victim.vulnerability_score,
        registered_via=victim.registered_via,
        is_verified=victim.is_verified,
        notes=victim.notes,
        created_at=victim.created_at.isoformat(),
        updated_at=victim.updated_at.isoformat(),
    )


@router.post(
    "/{victim_id}/assign-camp",
    response_model=VictimOut,
    dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))],
    summary="Assign victim household to a medical camp",
)
def assign_victim_camp_endpoint(
    victim_id: int,
    payload: VictimAssignCampRequest,
    db: Session = Depends(get_db),
):
    victim = victim_service.assign_victim_to_camp(victim_id, payload.camp_id, db)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim or Medical Camp not found.")
    return VictimOut(
        id=victim.id,
        user_id=victim.user_id,
        nic=victim.nic,
        full_name=victim.full_name,
        phone=victim.phone,
        alternate_phone=victim.alternate_phone,
        gender=victim.gender,
        age=victim.age,
        district=victim.district,
        ds_division=victim.ds_division,
        gn_division=victim.gn_division,
        current_address=victim.current_address,
        latitude=victim.latitude,
        longitude=victim.longitude,
        family_members_count=victim.family_members_count,
        children_count=victim.children_count,
        elderly_count=victim.elderly_count,
        disabled_count=victim.disabled_count,
        pregnant_lactating_count=victim.pregnant_lactating_count,
        evacuation_status=victim.evacuation_status,
        assigned_camp_id=victim.assigned_camp_id,
        assigned_camp_name=victim.assigned_camp.name if victim.assigned_camp else None,
        chronic_diseases=victim.chronic_diseases,
        immediate_medical_needs=victim.immediate_medical_needs,
        dietary_and_relief_needs=victim.dietary_and_relief_needs,
        vulnerability_score=victim.vulnerability_score,
        registered_via=victim.registered_via,
        is_verified=victim.is_verified,
        notes=victim.notes,
        created_at=victim.created_at.isoformat(),
        updated_at=victim.updated_at.isoformat(),
    )
