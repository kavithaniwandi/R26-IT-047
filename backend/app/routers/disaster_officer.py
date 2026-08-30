"""
app/routers/disaster_officer.py
--------------------------------
Disaster Officer endpoints powered directly by MongoDB Atlas collections.
"""
from __future__ import annotations
from typing import List, Optional, Literal
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_role, get_current_user_payload, TokenPayload
from app.database import disaster_requests_collection, users_collection

router = APIRouter(prefix="/disaster-donation-requests", tags=["Disaster Officer (MongoDB)"])


# ── Input / Request Schemas ──────────────────────────────────────────────────

class RequestItemIn(BaseModel):
    itemName: str = Field(..., min_length=2)
    unit: str = Field(...)
    neededQuantity: float = Field(..., gt=0)


class DisasterDonationRequestCreate(BaseModel):
    disasterType: Literal["Flood", "Landslide", "Tsunami", "Drought", "Fire", "Other"] = "Flood"
    severity: Literal["Low", "Moderate", "High", "Critical"] = "High"
    dsArea: str = Field(..., min_length=2)
    gnDivision: str = Field(..., min_length=2)
    reliefCamp: str = Field(..., min_length=2)
    people_count: int = Field(default=1, ge=0)
    items: List[RequestItemIn] = Field(..., min_items=1)


class PledgeItem(BaseModel):
    itemName: str
    quantity: float = Field(..., gt=0)
    itemId: Optional[str] = None


class BatchPledgeCreate(BaseModel):
    pledges: List[PledgeItem] = Field(..., min_items=1)


# ── Output / Response Schemas ────────────────────────────────────────────────

class RequestItemOut(BaseModel):
    itemId: Optional[str] = None
    itemName: str
    unit: str
    neededQuantity: float
    pledgedQuantity: float = 0.0
    donatedQuantity: float = 0.0
    remainingQuantity: float = 0.0
    status: str = "remaining"


class DonationEntryOut(BaseModel):
    donationId: str
    donorId: str
    donorName: str
    donorPhone: Optional[str] = None
    itemId: Optional[str] = None
    itemName: str
    quantity: float
    dsArea: str
    reliefCamp: Optional[str] = None
    status: str = "pledged"
    donatedAt: datetime
    acceptedAt: Optional[datetime] = None


class DisasterRequestGroupOut(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    reliefCamp: str
    people_count: int
    items: List[RequestItemOut]
    donations: List[DonationEntryOut]


class OfficerPledgeItemOut(BaseModel):
    donationId: str
    requestId: str
    donorName: str
    donorPhone: Optional[str] = None
    itemName: str
    quantity: float
    reliefCamp: str
    dsArea: str
    gnDivision: str
    status: str
    donatedAt: datetime


# ── Helper Formatter ─────────────────────────────────────────────────────────

def format_mongo_doc(doc: dict) -> DisasterRequestGroupOut:
    req_id = str(doc.get("_id"))
    items_out = []
    for item in doc.get("items", []):
        needed = float(item.get("neededQuantity", 0))
        pledged = float(item.get("pledgedQuantity", 0))
        donated = float(item.get("donatedQuantity", 0))
        rem = max(0.0, needed - (pledged + donated))
        items_out.append(
            RequestItemOut(
                itemId=item.get("itemId") or str(item.get("_id", "")),
                itemName=item.get("itemName", "Relief Item"),
                unit=item.get("unit", "units"),
                neededQuantity=needed,
                pledgedQuantity=pledged,
                donatedQuantity=donated,
                remainingQuantity=rem,
                status=item.get("status", "remaining"),
            )
        )

    donations_out = []
    for don in doc.get("donations", []):
        don_id = don.get("donationId") or str(don.get("_id", ObjectId()))
        donations_out.append(
            DonationEntryOut(
                donationId=don_id,
                donorId=str(don.get("donorId", "")),
                donorName=don.get("donorName", "Verified Donor"),
                donorPhone=don.get("donorPhone"),
                itemId=don.get("itemId"),
                itemName=don.get("itemName", "Relief Supply"),
                quantity=float(don.get("quantity", 0)),
                dsArea=don.get("dsArea") or doc.get("dsArea", "Western Sector"),
                reliefCamp=doc.get("reliefCamp", "Relief Camp"),
                status=don.get("status", "pledged"),
                donatedAt=don.get("donatedAt") or datetime.now(timezone.utc),
                acceptedAt=don.get("acceptedAt"),
            )
        )

    return DisasterRequestGroupOut(
        id=req_id,
        disasterType=doc.get("disasterType", "Flood"),
        severity=doc.get("severity", "High"),
        dsArea=doc.get("dsArea", "Western Province"),
        gnDivision=doc.get("gnDivision", "Ranala"),
        reliefCamp=doc.get("reliefCamp", "Community Shelter"),
        people_count=int(doc.get("people_count", 1)),
        items=items_out,
        donations=donations_out,
    )


# ── Route Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=List[DisasterRequestGroupOut])
async def get_all_disaster_requests():
    cursor = disaster_requests_collection.find()
    docs = await cursor.to_list(length=200)
    return [format_mongo_doc(d) for d in docs]


@router.get("/officer/pledges", response_model=List[OfficerPledgeItemOut])
async def get_officer_pending_pledges():
    cursor = disaster_requests_collection.find({"donations.status": "pledged"})
    docs = await cursor.to_list(length=200)

    pledges_out = []
    for doc in docs:
        req_id = str(doc["_id"])
        relief_camp = doc.get("reliefCamp", "Relief Center")
        ds_area = doc.get("dsArea", "Sector")
        gn_division = doc.get("gnDivision", "GN Area")

        for don in doc.get("donations", []):
            if don.get("status") == "pledged":
                don_id = don.get("donationId") or str(don.get("_id", ObjectId()))
                pledges_out.append(
                    OfficerPledgeItemOut(
                        donationId=don_id,
                        requestId=req_id,
                        donorName=don.get("donorName", "Verified Donor"),
                        donorPhone=don.get("donorPhone") or "+94 77 123 4567",
                        itemName=don.get("itemName", "Relief Item"),
                        quantity=float(don.get("quantity", 0)),
                        reliefCamp=relief_camp,
                        dsArea=ds_area,
                        gnDivision=gn_division,
                        status=don.get("status", "pledged"),
                        donatedAt=don.get("donatedAt") or datetime.now(timezone.utc),
                    )
                )
    return pledges_out


@router.patch("/{req_id}/donations/{donation_id}/accept")
async def accept_donation_at_ds_office(
    req_id: str,
    donation_id: str,
    token_payload: TokenPayload = Depends(get_current_user_payload),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")

    doc = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Disaster request not found")

    now = datetime.now(timezone.utc)
    updated = False

    items = doc.get("items", [])
    donations = doc.get("donations", [])

    for don in donations:
        current_don_id = don.get("donationId") or str(don.get("_id", ""))
        if current_don_id == donation_id:
            don["status"] = "received"
            don["acceptedAt"] = now
            don["acceptedByOfficerId"] = str(token_payload.sub)
            updated = True

            for itm in items:
                if itm.get("itemName") == don.get("itemName"):
                    itm["donatedQuantity"] = float(itm.get("donatedQuantity", 0)) + float(don.get("quantity", 0))
                    if itm["donatedQuantity"] >= float(itm.get("neededQuantity", 0)):
                        itm["status"] = "fulfilled"
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Donation record not found in request")

    await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"donations": donations, "items": items}}
    )

    return {"message": "Donation verified and accepted at DS Office.", "donationId": donation_id}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_disaster_request(payload: DisasterDonationRequestCreate):
    doc = payload.model_dump()
    doc["createdAt"] = datetime.now(timezone.utc)
    doc["status"] = "active"
    doc["donations"] = []

    for itm in doc.get("items", []):
        itm["pledgedQuantity"] = 0.0
        itm["donatedQuantity"] = 0.0
        itm["remainingQuantity"] = float(itm["neededQuantity"])
        itm["status"] = "remaining"

    result = await disaster_requests_collection.insert_one(doc)
    return {"message": "Request created successfully", "id": str(result.inserted_id)}


@router.post("/{req_id}/pledge", status_code=status.HTTP_201_CREATED)
async def add_pledge_to_request(req_id: str, payload: BatchPledgeCreate):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")

    now = datetime.now(timezone.utc)
    new_donations = []
    items = doc.get("items", [])

    for p in payload.pledges:
        donation_entry = {
            "donationId": str(ObjectId()),
            "donorId": "donor_01",
            "donorName": "Sri Lanka Red Cross",
            "donorPhone": "+94 77 123 4567",
            "itemName": p.itemName,
            "quantity": float(p.quantity),
            "dsArea": doc.get("dsArea", "Western Sector"),
            "status": "pledged",
            "donatedAt": now,
        }
        new_donations.append(donation_entry)

        for itm in items:
            if itm.get("itemName") == p.itemName:
                itm["pledgedQuantity"] = float(itm.get("pledgedQuantity", 0)) + float(p.quantity)

    await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {"$push": {"donations": {"$each": new_donations}}, "$set": {"items": items}}
    )

    return {"message": "Pledges recorded successfully", "count": len(new_donations)}