"""
app/routers/users.py
--------------------
User management endpoints for Administrator.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
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

class StatusChangeRequest(BaseModel):
    is_active: bool

class AdminCreateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    address: Optional[str] = None
    role: RoleEnum = RoleEnum.victim

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
        out.append(
            UserOut(
                id=u.id,
                full_name=u.full_name,
                email=u.email,
                phone=u.phone,
                address=u.address,
                role=r.name.value if r else "victim",
                is_active=u.is_active,
                created_at=u.created_at,
            )
        )
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
        role_id=role_obj.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=role_obj.name.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )

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
    db.commit()
    db.refresh(user)
    
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=role_obj.name.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )

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
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        role=r.name.value if r else "victim",
        is_active=user.is_active,
        created_at=user.created_at,
    )
