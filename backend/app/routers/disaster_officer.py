"""
app/routers/disaster_officer.py
--------------------------------
Disaster Officer endpoints powered directly by MongoDB Atlas collections.
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_role, TokenPayload
from app.database import disaster_requests_collection, get_db, users_collection
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.disaster_donation_request import (
    BatchPledgeCreate,
    DisasterDonationRequestCreate,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/disaster-donation-requests", tags=["Disaster Officer (MongoDB)"])


# ── Input / Request Schemas ──────────────────────────────────────────────────

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
    acceptedByOfficerId: Optional[str] = None


class DisasterRequestGroupOut(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    reliefCamp: str
    people_count: int
    status: str = "remaining"
    createdBy: Optional[str] = None
    createdAt: Optional[datetime] = None
    items: List[RequestItemOut]
    donations: List[DonationEntryOut]
    targetedDonorCount: int = 0
    lastOutreachAt: Optional[datetime] = None


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


class DonorMatchOut(BaseModel):
    donorId: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    source: str
    score: int
    proximityTier: str
    historyCount: int
    receivedDonationCount: int
    relevantDonationCount: int
    reasons: List[str]
    alreadyTargeted: bool = False


class DonorOutreachCreate(BaseModel):
    donorIds: List[str]


class DonorOutreachResult(BaseModel):
    requestId: str
    targetedDonorCount: int
    sentAt: datetime
    message: str


# ── Helper Formatter ─────────────────────────────────────────────────────────

def format_mongo_doc(doc: dict) -> DisasterRequestGroupOut:
    req_id = str(doc.get("_id"))
    items_out = []
    for item in doc.get("items", []):
        needed = float(item.get("neededQuantity", 0))
        pledged = float(item.get("pledgedQuantity", 0))
        donated = float(item.get("donatedQuantity", 0))
        rem = max(0.0, needed - donated)
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
                acceptedByOfficerId=don.get("acceptedByOfficerId"),
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
        status=doc.get("status", "remaining"),
        createdBy=str(doc.get("createdBy")) if doc.get("createdBy") is not None else None,
        createdAt=doc.get("createdAt"),
        items=items_out,
        donations=donations_out,
        targetedDonorCount=len(doc.get("targetedDonorIds", [])),
        lastOutreachAt=doc.get("lastOutreachAt"),
    )


def _normalise(value: Optional[str]) -> str:
    return " ".join((value or "").strip().casefold().split())


def _sql_donor_alias_ids(db: Session, donor_id: str) -> List[str]:
    """Resolve duplicate development accounts with the same email as one identity."""
    if not donor_id.isdigit():
        return [donor_id]
    donor = db.query(User).filter(User.id == int(donor_id)).first()
    if not donor or not donor.email:
        return [donor_id]
    return [
        str(user_id)
        for (user_id,) in db.query(User.id).filter(User.email == donor.email).all()
    ] or [donor_id]


def _proximity(address: Optional[str], gn_division: str, ds_area: str) -> tuple[str, int, str]:
    address_key = _normalise(address)
    gn_key = _normalise(gn_division)
    ds_key = _normalise(ds_area)
    if gn_key and gn_key in address_key:
        return "Same GN division", 45, f"Address matches {gn_division} GN division"
    if ds_key and ds_key in address_key:
        return "Same DS area", 30, f"Address matches {ds_area} DS area"
    if address_key:
        return "Broader area", 12, "Registered outside the request's GN/DS area"
    return "Location unavailable", 5, "No donor address is available for proximity matching"


# ── Route Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=List[DisasterRequestGroupOut])
async def get_all_disaster_requests(
    dsArea: Optional[str] = None,
    status_filter: Optional[str] = None,
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "donor", "authority", "disaster_officer"])
    ),
    db: Session = Depends(get_db),
):
    query = {}
    if _current_user.role == "donor":
        query["targetedDonorIds"] = {"$in": _sql_donor_alias_ids(db, _current_user.sub)}
    if dsArea:
        query["dsArea"] = dsArea
    if status_filter:
        query["status"] = status_filter
    cursor = disaster_requests_collection.find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)
    return [format_mongo_doc(d) for d in docs]


@router.get("/{req_id}/donor-matches", response_model=List[DonorMatchOut])
async def get_ranked_donor_matches(
    req_id: str,
    _current_user: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    request_doc = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Disaster request not found")

    role = db.query(Role).filter(Role.name == RoleEnum.donor).first()
    sql_users = (
        db.query(User)
        .filter(User.role_id == role.id, User.is_active.is_(True))
        .order_by(User.id.desc())
        .all()
        if role else []
    )

    donors: List[dict] = []
    seen_emails = set()
    for user in sql_users:
        email_key = _normalise(user.email)
        if email_key and email_key in seen_emails:
            continue
        if email_key:
            seen_emails.add(email_key)
        donors.append({
            "donorId": str(user.id), "name": user.full_name, "email": user.email,
            "phone": user.phone, "address": user.address, "source": "SQL account",
        })

    mongo_users = await users_collection.find({"userType": "donor"}).to_list(length=500)
    for user in mongo_users:
        email_key = _normalise(user.get("email"))
        if email_key and email_key in seen_emails:
            continue
        if email_key:
            seen_emails.add(email_key)
        name = " ".join(
            part for part in [user.get("firstName"), user.get("lastName")] if part
        ) or user.get("full_name") or "Registered Donor"
        donors.append({
            "donorId": str(user["_id"]), "name": name, "email": user.get("email"),
            "phone": user.get("phone"), "address": user.get("address"),
            "source": "MongoDB account",
        })

    history_docs = await disaster_requests_collection.find(
        {"donations.0": {"$exists": True}}, {"donations": 1}
    ).to_list(length=1000)
    target_items = {
        _normalise(item.get("itemName")) for item in request_doc.get("items", [])
        if item.get("itemName")
    }
    targeted_ids = {str(value) for value in request_doc.get("targetedDonorIds", [])}
    severity_points = {
        "critical": 10, "high": 8, "moderate": 5, "medium": 5, "low": 2,
    }.get(_normalise(request_doc.get("severity")), 5)

    matches = []
    for donor in donors:
        donor_id = donor["donorId"]
        donor_email = _normalise(donor.get("email"))
        donor_history = []
        for history_doc in history_docs:
            for donation in history_doc.get("donations", []):
                same_id = str(donation.get("donorId", "")) == donor_id
                same_email = donor_email and _normalise(donation.get("donorEmail")) == donor_email
                if same_id or same_email:
                    donor_history.append(donation)

        received_count = sum(1 for donation in donor_history if donation.get("status") == "received")
        relevant_count = sum(
            1 for donation in donor_history
            if _normalise(donation.get("itemName")) in target_items
        )
        proximity_tier, proximity_points, proximity_reason = _proximity(
            donor.get("address"), request_doc.get("gnDivision", ""), request_doc.get("dsArea", "")
        )
        history_points = min(15, len(donor_history) * 3) + min(10, received_count * 2)
        relevance_points = min(20, relevant_count * 5)
        score = min(100, proximity_points + history_points + relevance_points + severity_points)
        reasons = [proximity_reason]
        if donor_history:
            reasons.append(f"{len(donor_history)} previous pledge(s), {received_count} received")
        else:
            reasons.append("No previous donation history yet")
        if relevant_count:
            reasons.append(f"{relevant_count} previous donation(s) match requested items")
        reasons.append(f"{request_doc.get('severity', 'Moderate')} request urgency")

        matches.append(DonorMatchOut(
            **donor, score=score, proximityTier=proximity_tier,
            historyCount=len(donor_history), receivedDonationCount=received_count,
            relevantDonationCount=relevant_count, reasons=reasons,
            alreadyTargeted=donor_id in targeted_ids,
        ))

    return sorted(matches, key=lambda match: (-match.score, match.name.casefold()))


@router.post("/{req_id}/outreach", response_model=DonorOutreachResult)
async def send_personalized_donor_outreach(
    req_id: str,
    payload: DonorOutreachCreate,
    token_payload: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    donor_ids = list(dict.fromkeys(str(value).strip() for value in payload.donorIds if str(value).strip()))
    if not donor_ids:
        raise HTTPException(status_code=400, detail="Select at least one donor")

    now = datetime.now(timezone.utc)
    result = await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {
            "$addToSet": {"targetedDonorIds": {"$each": donor_ids}},
            "$set": {"lastOutreachAt": now},
            "$push": {"outreachHistory": {
                "officerId": token_payload.sub, "donorIds": donor_ids,
                "sentAt": now, "channel": "in_app",
            }},
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Disaster request not found")
    updated = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    return DonorOutreachResult(
        requestId=req_id, targetedDonorCount=len(updated.get("targetedDonorIds", [])),
        sentAt=now,
        message=f"Personalized in-app request published to {len(donor_ids)} donor(s)",
    )


@router.get("/officer/pledges", response_model=List[OfficerPledgeItemOut])
async def get_officer_pending_pledges(
    _current_user: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer"])
    ),
):
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


@router.get("/{req_id}", response_model=DisasterRequestGroupOut)
async def get_disaster_request(
    req_id: str,
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "donor", "authority", "disaster_officer"])
    ),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    document = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Disaster request not found")
    if _current_user.role == "donor":
        identity_ids = set(_sql_donor_alias_ids(db, _current_user.sub))
        targeted_ids = {str(value) for value in document.get("targetedDonorIds", [])}
        if not identity_ids.intersection(targeted_ids):
            raise HTTPException(status_code=403, detail="This request is not assigned to your donor profile")
    return format_mongo_doc(document)


@router.patch("/{req_id}/donations/{donation_id}/accept")
async def accept_donation_at_ds_office(
    req_id: str,
    donation_id: str,
    token_payload: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer"])
    ),
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
            if don.get("status") == "received":
                raise HTTPException(status_code=400, detail="This donation has already been received")
            don["status"] = "received"
            don["acceptedAt"] = now
            don["acceptedByOfficerId"] = str(token_payload.sub)
            updated = True

            for itm in items:
                same_item_id = don.get("itemId") and itm.get("itemId") == don.get("itemId")
                same_item_name = itm.get("itemName", "").casefold() == don.get("itemName", "").casefold()
                if same_item_id or same_item_name:
                    transfer_quantity = float(don.get("quantity", 0))
                    itm["pledgedQuantity"] = max(
                        0.0,
                        float(itm.get("pledgedQuantity", 0)) - transfer_quantity,
                    )
                    itm["donatedQuantity"] = float(itm.get("donatedQuantity", 0)) + transfer_quantity
                    itm["remainingQuantity"] = max(
                        0.0,
                        float(itm.get("neededQuantity", 0)) - itm["donatedQuantity"],
                    )
                    if itm["donatedQuantity"] >= float(itm.get("neededQuantity", 0)):
                        itm["status"] = "fulfilled"
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Donation record not found in request")

    request_status = (
        "fulfilled"
        if items and all(item.get("status") == "fulfilled" for item in items)
        else "remaining"
    )

    await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"donations": donations, "items": items, "status": request_status}}
    )

    updated_document = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    return format_mongo_doc(updated_document)


@router.post("", response_model=DisasterRequestGroupOut, status_code=status.HTTP_201_CREATED)
async def create_disaster_request(
    payload: DisasterDonationRequestCreate,
    token_payload: TokenPayload = Depends(require_role(["admin", "volunteer"])),
):
    doc = payload.model_dump()
    doc["createdAt"] = datetime.now(timezone.utc)
    doc["status"] = "remaining"
    doc["createdBy"] = token_payload.sub
    doc["donations"] = []

    for itm in doc.get("items", []):
        itm["pledgedQuantity"] = 0.0
        itm["donatedQuantity"] = 0.0
        itm["remainingQuantity"] = float(itm["neededQuantity"])
        itm["status"] = "remaining"

    result = await disaster_requests_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return format_mongo_doc(doc)


@router.post("/{req_id}/pledge", status_code=status.HTTP_201_CREATED)
async def add_pledge_to_request(
    req_id: str,
    payload: BatchPledgeCreate,
    token_payload: TokenPayload = Depends(require_role(["admin", "donor"])),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")

    if token_payload.role == "donor":
        identity_ids = set(_sql_donor_alias_ids(db, token_payload.sub))
        targeted_ids = {str(value) for value in doc.get("targetedDonorIds", [])}
        if not identity_ids.intersection(targeted_ids):
            raise HTTPException(status_code=403, detail="This request is not assigned to your donor profile")

    now = datetime.now(timezone.utc)
    new_donations = []
    items = doc.get("items", [])

    sql_user = None
    mongo_user = None
    if token_payload.sub.isdigit():
        sql_user = db.query(User).filter(User.id == int(token_payload.sub)).first()
    elif ObjectId.is_valid(token_payload.sub):
        mongo_user = await users_collection.find_one({"_id": ObjectId(token_payload.sub)})
    donor_name = (
        sql_user.full_name
        if sql_user
        else " ".join(
            value for value in [
                (mongo_user or {}).get("firstName"),
                (mongo_user or {}).get("lastName"),
            ] if value
        ) or (mongo_user or {}).get("full_name") or "Verified Donor"
    )
    donor_phone = sql_user.phone if sql_user else (mongo_user or {}).get("phone")
    donor_email = sql_user.email if sql_user else (mongo_user or {}).get("email")

    for p in payload.pledges:
        target_item = next(
            (
                item for item in items
                if (p.itemId and item.get("itemId") == p.itemId)
                or item.get("itemName", "").casefold() == p.itemName.casefold()
            ),
            None,
        )
        if target_item is None:
            raise HTTPException(status_code=404, detail=f"Requested item '{p.itemName}' was not found")
        available = max(
            0.0,
            float(target_item.get("neededQuantity", 0))
            - float(target_item.get("pledgedQuantity", 0))
            - float(target_item.get("donatedQuantity", 0)),
        )
        if float(p.quantity) > available:
            raise HTTPException(
                status_code=400,
                detail=f"Only {available:g} {target_item.get('unit', 'units')} remain for {p.itemName}",
            )

        donation_entry = {
            "donationId": str(ObjectId()),
            "donorId": token_payload.sub,
            "donorName": donor_name,
            "donorPhone": donor_phone,
            "donorEmail": donor_email,
            "itemId": target_item.get("itemId"),
            "itemName": p.itemName,
            "quantity": float(p.quantity),
            "dsArea": doc.get("dsArea", "Western Sector"),
            "reliefCamp": doc.get("reliefCamp"),
            "status": "pledged",
            "donatedAt": now,
        }
        new_donations.append(donation_entry)

        target_item["pledgedQuantity"] = float(target_item.get("pledgedQuantity", 0)) + float(p.quantity)

    await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {"$push": {"donations": {"$each": new_donations}}, "$set": {"items": items}}
    )

    updated_document = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    return format_mongo_doc(updated_document)
