"""
app/routers/donations.py
------------------------
Donation needs discovery, pledging, and relief tracking endpoints.
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_role, get_current_user_payload, TokenPayload
from app.database import get_db
from app.models.donation import DonationItem, Donation
from app.models.sos import SOSRequest
from app.models.user import User

router = APIRouter(prefix="/donations", tags=["Donations & Relief Matching"])

class DonationPledgeRequest(BaseModel):
    donation_item_id: int
    quantity_pledged: int = Field(..., gt=0)

class DonationItemCreateRequest(BaseModel):
    sos_request_id: int
    category: str # 'Medicine', 'Consumables', 'Equipment', 'Water', 'Nutrition'
    item_name: str
    quantity_required: int = Field(..., gt=0)
    unit: str = "units"

class DonationNeedOut(BaseModel):
    id: int
    sos_request_id: int
    category: str
    item_name: str
    quantity_required: int
    quantity_fulfilled: int
    remaining_needed: int
    unit: str
    status: str
    priority_score: float
    district: Optional[str]
    created_at: str

class DonationPledgeOut(BaseModel):
    id: int
    donor_name: str
    item_name: str
    category: str
    quantity_pledged: int
    unit: str
    delivery_status: str
    tracking_code: str
    pledged_at: str

@router.get("/needs", response_model=List[DonationNeedOut])
def list_donation_needs(
    category_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List itemized donation needs sorted by parent SOS priority score."""
    query = (
        db.query(DonationItem, SOSRequest.priority_score, SOSRequest.district)
        .join(SOSRequest, DonationItem.sos_request_id == SOSRequest.id)
    )
    if category_filter:
        query = query.filter(DonationItem.category == category_filter)
    if status_filter:
        query = query.filter(DonationItem.status == status_filter)
    else:
        # Default: show unmet or partially met needs first
        query = query.filter(DonationItem.status != "fulfilled")

    records = query.order_by(SOSRequest.priority_score.desc(), DonationItem.created_at.desc()).all()
    out = []
    for item, priority, district in records:
        out.append(
            DonationNeedOut(
                id=item.id,
                sos_request_id=item.sos_request_id,
                category=item.category,
                item_name=item.item_name,
                quantity_required=item.quantity_required,
                quantity_fulfilled=item.quantity_fulfilled,
                remaining_needed=max(0, item.quantity_required - item.quantity_fulfilled),
                unit=item.unit,
                status=item.status,
                priority_score=round(priority, 1) if priority else 50.0,
                district=district,
                created_at=item.created_at.isoformat(),
            )
        )
    return out

@router.post("/items", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["authority", "admin", "volunteer"]))])
def create_donation_item(payload: DonationItemCreateRequest, db: Session = Depends(get_db)):
    """Add a specific item need to an existing SOS request."""
    sos = db.query(SOSRequest).filter(SOSRequest.id == payload.sos_request_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found.")
        
    item = DonationItem(
        sos_request_id=payload.sos_request_id,
        category=payload.category,
        item_name=payload.item_name,
        quantity_required=payload.quantity_required,
        quantity_fulfilled=0,
        unit=payload.unit,
        status="unmet",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Donation item created successfully", "id": item.id}

@router.post("", response_model=DonationPledgeOut, status_code=status.HTTP_201_CREATED)
def pledge_donation(
    payload: DonationPledgeRequest,
    token_data: TokenPayload = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Pledge items against an active requirement (Donor / Admin)."""
    item = db.query(DonationItem).filter(DonationItem.id == payload.donation_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Donation item not found.")

    donor_id = int(token_data.sub)
    donor = db.query(User).filter(User.id == donor_id).first()

    # Create pledge
    tracking = f"TRK-{uuid.uuid4().hex[:8].upper()}"
    pledge = Donation(
        donor_user_id=donor_id,
        donation_item_id=item.id,
        quantity_pledged=payload.quantity_pledged,
        delivery_status="pledged",
        tracking_code=tracking,
    )
    db.add(pledge)

    # Atomic fulfillment update
    item.quantity_fulfilled += payload.quantity_pledged
    if item.quantity_fulfilled >= item.quantity_required:
        item.status = "fulfilled"
    else:
        item.status = "partially_met"

    db.commit()
    db.refresh(pledge)

    return DonationPledgeOut(
        id=pledge.id,
        donor_name=donor.full_name if donor else "Anonymous Donor",
        item_name=item.item_name,
        category=item.category,
        quantity_pledged=pledge.quantity_pledged,
        unit=item.unit,
        delivery_status=pledge.delivery_status,
        tracking_code=pledge.tracking_code,
        pledged_at=pledge.pledged_at.isoformat(),
    )

@router.get("", response_model=List[DonationPledgeOut], dependencies=[Depends(require_role(["authority", "admin", "donor"]))])
def list_all_pledges(db: Session = Depends(get_db)):
    """List all donation pledges made across the system."""
    pledges = db.query(Donation).order_by(Donation.pledged_at.desc()).all()
    out = []
    for p in pledges:
        donor = db.query(User).filter(User.id == p.donor_user_id).first()
        item = db.query(DonationItem).filter(DonationItem.id == p.donation_item_id).first()
        out.append(
            DonationPledgeOut(
                id=p.id,
                donor_name=donor.full_name if donor else "Donor",
                item_name=item.item_name if item else "Relief Item",
                category=item.category if item else "General",
                quantity_pledged=p.quantity_pledged,
                unit=item.unit if item else "units",
                delivery_status=p.delivery_status,
                tracking_code=p.tracking_code,
                pledged_at=p.pledged_at.isoformat(),
            )
        )
    return out
