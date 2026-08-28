"""
app/services/victim_service.py
------------------------------
Core business logic for disaster victim registration, vulnerability calculation,
camp intake management, and demographic aggregation.
"""
from __future__ import annotations

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.victim import Victim
from app.models.camp import MedicalCamp
from app.models.user import User
from app.schemas.victim import VictimCreateRequest, VictimUpdateRequest


def calculate_vulnerability_score(
    family_members_count: int = 1,
    children_count: int = 0,
    elderly_count: int = 0,
    disabled_count: int = 0,
    pregnant_lactating_count: int = 0,
    evacuation_status: str = "trapped_in_house",
    chronic_diseases: Optional[str] = None,
    immediate_medical_needs: Optional[str] = None,
) -> float:
    """
    Computes a composite vulnerability index (0.0 - 100.0) based on household
    demographics, trapped/evacuation severity, and urgent medical needs.
    """
    score = 25.0  # Baseline for any disaster-affected household

    # Demographic multipliers
    score += min(children_count * 7.5, 20.0)
    score += min(elderly_count * 9.0, 25.0)
    score += min(disabled_count * 15.0, 30.0)
    score += min(pregnant_lactating_count * 12.0, 24.0)

    # Large family penalty
    if family_members_count > 5:
        score += min((family_members_count - 5) * 2.0, 10.0)

    # Evacuation status severity
    status_weights = {
        "isolated_roof_level": 30.0,
        "trapped_in_house": 22.0,
        "displaced_with_relatives": 10.0,
        "evacuated_to_camp": 5.0,
        "safe_at_home": 0.0,
    }
    score += status_weights.get(evacuation_status, 15.0)

    # Medical vulnerability
    if chronic_diseases and len(chronic_diseases.strip()) > 0:
        score += 12.0
    if immediate_medical_needs and len(immediate_medical_needs.strip()) > 0:
        score += 15.0

    return round(min(max(score, 5.0), 100.0), 1)


def register_victim(payload: VictimCreateRequest, db: Session, user_id: Optional[int] = None) -> Victim:
    """Create a new registered victim record with computed vulnerability."""
    # Compute vulnerability
    vulnerability = calculate_vulnerability_score(
        family_members_count=payload.family_members_count,
        children_count=payload.children_count,
        elderly_count=payload.elderly_count,
        disabled_count=payload.disabled_count,
        pregnant_lactating_count=payload.pregnant_lactating_count,
        evacuation_status=payload.evacuation_status,
        chronic_diseases=payload.chronic_diseases,
        immediate_medical_needs=payload.immediate_medical_needs,
    )

    # If user_id not explicitly provided, check if a user with this phone exists
    if user_id is None:
        matched_user = db.query(User).filter(User.phone == payload.phone).first()
        if matched_user:
            user_id = matched_user.id

    victim = Victim(
        user_id=user_id,
        nic=payload.nic.strip() if payload.nic else None,
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        alternate_phone=payload.alternate_phone.strip() if payload.alternate_phone else None,
        gender=payload.gender,
        age=payload.age,
        district=payload.district or "Colombo",
        ds_division=payload.ds_division,
        gn_division=payload.gn_division,
        current_address=payload.current_address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        family_members_count=payload.family_members_count,
        children_count=payload.children_count,
        elderly_count=payload.elderly_count,
        disabled_count=payload.disabled_count,
        pregnant_lactating_count=payload.pregnant_lactating_count,
        evacuation_status=payload.evacuation_status,
        assigned_camp_id=payload.assigned_camp_id,
        chronic_diseases=payload.chronic_diseases,
        immediate_medical_needs=payload.immediate_medical_needs,
        dietary_and_relief_needs=payload.dietary_and_relief_needs,
        vulnerability_score=vulnerability,
        registered_via=payload.registered_via,
        is_verified=False,
        notes=payload.notes,
    )
    db.add(victim)
    db.commit()
    db.refresh(victim)
    return victim


def list_victims(
    db: Session,
    district: Optional[str] = None,
    evacuation_status: Optional[str] = None,
    min_vulnerability: Optional[float] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Victim], int]:
    """Retrieve filtered list of disaster victims."""
    query = db.query(Victim)

    if district:
        query = query.filter(Victim.district.ilike(f"%{district}%"))
    if evacuation_status:
        query = query.filter(Victim.evacuation_status == evacuation_status)
    if min_vulnerability is not None:
        query = query.filter(Victim.vulnerability_score >= min_vulnerability)
    if is_verified is not None:
        query = query.filter(Victim.is_verified == is_verified)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Victim.full_name.ilike(search_fmt)) |
            (Victim.phone.ilike(search_fmt)) |
            (Victim.nic.ilike(search_fmt)) |
            (Victim.current_address.ilike(search_fmt))
        )

    total = query.count()
    results = query.order_by(Victim.vulnerability_score.desc(), Victim.created_at.desc()).offset(skip).limit(limit).all()
    return results, total


def update_victim(victim_id: int, payload: VictimUpdateRequest, db: Session) -> Optional[Victim]:
    """Update fields of an existing victim profile."""
    victim = db.query(Victim).filter(Victim.id == victim_id).first()
    if not victim:
        return None

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(victim, k, v)

    # Recalculate vulnerability if demographic/status changed
    victim.vulnerability_score = calculate_vulnerability_score(
        family_members_count=victim.family_members_count,
        children_count=victim.children_count,
        elderly_count=victim.elderly_count,
        disabled_count=victim.disabled_count,
        pregnant_lactating_count=victim.pregnant_lactating_count,
        evacuation_status=victim.evacuation_status,
        chronic_diseases=victim.chronic_diseases,
        immediate_medical_needs=victim.immediate_medical_needs,
    )

    db.commit()
    db.refresh(victim)
    return victim


def assign_victim_to_camp(victim_id: int, camp_id: int, db: Session) -> Optional[Victim]:
    """Assign victim and family to an approved medical camp and increment occupancy."""
    victim = db.query(Victim).filter(Victim.id == victim_id).first()
    camp = db.query(MedicalCamp).filter(MedicalCamp.id == camp_id).first()
    if not victim or not camp:
        return None

    victim.assigned_camp_id = camp.id
    victim.evacuation_status = "evacuated_to_camp"
    
    # Increment camp occupancy by household size
    camp.current_occupancy = (camp.current_occupancy or 0) + victim.family_members_count
    
    db.commit()
    db.refresh(victim)
    db.refresh(camp)
    return victim


def get_victim_stats(db: Session) -> dict:
    """Generate demographic and vulnerability summary statistics."""
    total_victims = db.query(Victim).count()
    if total_victims == 0:
        return {
            "total_victims": 0,
            "total_family_members_affected": 0,
            "total_children": 0,
            "total_elderly": 0,
            "total_disabled": 0,
            "total_pregnant_lactating": 0,
            "high_vulnerability_count": 0,
            "evacuated_to_camp_count": 0,
            "trapped_count": 0,
            "by_district": {},
            "by_evacuation_status": {},
        }

    sum_members = db.query(func.sum(Victim.family_members_count)).scalar() or 0
    sum_children = db.query(func.sum(Victim.children_count)).scalar() or 0
    sum_elderly = db.query(func.sum(Victim.elderly_count)).scalar() or 0
    sum_disabled = db.query(func.sum(Victim.disabled_count)).scalar() or 0
    sum_pregnant = db.query(func.sum(Victim.pregnant_lactating_count)).scalar() or 0
    
    high_vuln = db.query(Victim).filter(Victim.vulnerability_score >= 75.0).count()
    evacuated = db.query(Victim).filter(Victim.evacuation_status == "evacuated_to_camp").count()
    trapped = db.query(Victim).filter(
        Victim.evacuation_status.in_(["trapped_in_house", "isolated_roof_level"])
    ).count()

    # District grouping
    dist_counts = db.query(Victim.district, func.count(Victim.id)).group_by(Victim.district).all()
    by_district = {d: c for d, c in dist_counts if d}

    # Evacuation status grouping
    status_counts = db.query(Victim.evacuation_status, func.count(Victim.id)).group_by(Victim.evacuation_status).all()
    by_status = {s: c for s, c in status_counts if s}

    return {
        "total_victims": total_victims,
        "total_family_members_affected": int(sum_members),
        "total_children": int(sum_children),
        "total_elderly": int(sum_elderly),
        "total_disabled": int(sum_disabled),
        "total_pregnant_lactating": int(sum_pregnant),
        "high_vulnerability_count": high_vuln,
        "evacuated_to_camp_count": evacuated,
        "trapped_count": trapped,
        "by_district": by_district,
        "by_evacuation_status": by_status,
    }
