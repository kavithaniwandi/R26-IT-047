"""
app/routers/users.py
--------------------
User management endpoints for Administrator.
"""
from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.security import require_role, TokenPayload
from app.database import get_db
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.schemas.auth import UserOut

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/users", tags=["User Administration"])

class RoleChangeRequest(BaseModel):
    role: RoleEnum
    assigned_ds_area: Optional[str] = Field(None, min_length=2, max_length=120)

    @model_validator(mode="after")
    def validate_officer_area(self):
        if self.role == RoleEnum.disaster_officer and not self.assigned_ds_area:
            raise ValueError("A disaster officer must be assigned to a DS area")
        return self

class StatusChangeRequest(BaseModel):
    is_active: bool

class AdminCreateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    address: Optional[str] = None
    assigned_ds_area: Optional[str] = Field(None, min_length=2, max_length=120)
    role: RoleEnum = RoleEnum.victim
    donor_type: Optional[Literal["Business", "Hospital", "Individual", "NGO", "Organization", "Pharmacy"]] = None
    preferred_donation_category: Optional[Literal["Blankets", "Dry Rations", "Medical", "Multiple", "Tarpaulins", "Water"]] = None
    capacity_level: Optional[Literal["Low", "Medium", "High"]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    @model_validator(mode="after")
    def validate_donor_profile(self):
        if self.role == RoleEnum.donor:
            missing = [
                label for label, value in {
                    "donor type": self.donor_type,
                    "preferred donation category": self.preferred_donation_category,
                    "capacity level": self.capacity_level,
                }.items() if value is None
            ]
            if not self.address and (self.latitude is None or self.longitude is None):
                missing.append("address or latitude/longitude")
            if missing:
                raise ValueError(f"Donor profile requires: {', '.join(missing)}")
        if self.role == RoleEnum.disaster_officer and not self.assigned_ds_area:
            raise ValueError("A disaster officer must be assigned to a DS area")
        return self


class DonorProfileUpdate(BaseModel):
    donor_type: Literal["Business", "Hospital", "Individual", "NGO", "Organization", "Pharmacy"]
    preferred_donation_category: Literal["Blankets", "Dry Rations", "Medical", "Multiple", "Tarpaulins", "Water"]
    capacity_level: Literal["Low", "Medium", "High"]
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


def _to_user_out(user: User, role_name: str) -> UserOut:
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        assigned_ds_area=user.assigned_ds_area,
        donor_type=user.donor_type,
        preferred_donation_category=user.preferred_donation_category,
        capacity_level=user.capacity_level,
        latitude=user.latitude,
        longitude=user.longitude,
        role=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )

@router.get("", response_model=List[UserOut], dependencies=[Depends(require_role(["admin"]))])
def list_users(
    role_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all registered stakeholders with optional search and role filtering."""
    query = db.query(User)
    
    if role_filter:
        role_obj = db.query(Role).filter(Role.name == role_filter).first()
        if role_obj:
            query = query.filter(User.role_id == role_obj.id)
            
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_fmt)) | (User.email.ilike(search_fmt))
        )
        
    users = query.order_by(User.created_at.desc()).all()
    out = []
    for u in users:
        r = db.query(Role).filter(Role.id == u.role_id).first()
        out.append(_to_user_out(u, r.name.value if r else "victim"))
    return out

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin"]))])
def admin_create_user(payload: AdminCreateUserRequest, db: Session = Depends(get_db)):
    """Admin creates a new user account directly with any assigned role."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists.",
        )
    
    role_obj = db.query(Role).filter(Role.name == payload.role).first()
    if not role_obj:
        raise HTTPException(status_code=400, detail="Invalid role specified.")
        
    hashed = pwd_context.hash(payload.password)
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hashed,
        phone=payload.phone,
        address=payload.address,
        assigned_ds_area=payload.assigned_ds_area,
        donor_type=payload.donor_type,
        preferred_donation_category=payload.preferred_donation_category,
        capacity_level=payload.capacity_level,
        latitude=payload.latitude,
        longitude=payload.longitude,
        role_id=role_obj.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return _to_user_out(user, role_obj.name.value)

@router.patch("/{user_id}/role", response_model=UserOut, dependencies=[Depends(require_role(["admin"]))])
def change_user_role(user_id: int, payload: RoleChangeRequest, db: Session = Depends(get_db)):
    """Change a user's role (admin privilege)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    role_obj = db.query(Role).filter(Role.name == payload.role).first()
    if not role_obj:
        raise HTTPException(status_code=400, detail="Invalid role specified.")
        
    user.role_id = role_obj.id
    user.assigned_ds_area = (
        payload.assigned_ds_area
        if payload.role == RoleEnum.disaster_officer
        else None
    )
    db.commit()
    db.refresh(user)
    
    return _to_user_out(user, role_obj.name.value)

@router.patch("/{user_id}/status", response_model=UserOut, dependencies=[Depends(require_role(["admin"]))])
def toggle_user_status(user_id: int, payload: StatusChangeRequest, db: Session = Depends(get_db)):
    """Activate or deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    
    r = db.query(Role).filter(Role.id == user.role_id).first()
    return _to_user_out(user, r.name.value if r else "victim")


@router.patch("/{user_id}/donor-profile", response_model=UserOut, dependencies=[Depends(require_role(["admin"]))])
def update_donor_profile(user_id: int, payload: DonorProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role or role.name != RoleEnum.donor:
        raise HTTPException(status_code=400, detail="A donor profile can only be assigned to a donor account.")
    if not user.address and (payload.latitude is None or payload.longitude is None):
        raise HTTPException(status_code=400, detail="A donor profile requires an address or latitude/longitude.")
    for field, value in payload.model_dump().items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return _to_user_out(user, role.name.value)
