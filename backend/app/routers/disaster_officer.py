"""
app/routers/disaster_officer.py
--------------------------------
Disaster Officer endpoints powered directly by MongoDB Atlas collections.
"""
from __future__ import annotations
from typing import List, Literal, Optional
from datetime import datetime, timedelta, timezone
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
    whole_required_quantity,
)
from app.services.pledge_expiry import expire_stale_pledges
from app.services.donor_matching import (
    DonorModelUnavailable,
    model_information,
    predict_compatibility,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/disaster-donation-requests", tags=["Disaster Officer (MongoDB)"])


# ── Input / Request Schemas ──────────────────────────────────────────────────

# ── Output / Response Schemas ────────────────────────────────────────────────

class RequestItemOut(BaseModel):
    itemId: Optional[str] = None
    itemName: str
    requiredCategory: Optional[str] = None
    unit: str
    neededQuantity: float
    pledgedQuantity: float = 0.0
    donatedQuantity: float = 0.0
    remainingQuantity: float = 0.0
    status: str = "remaining"


class DonationEntryOut(BaseModel):
    donationId: str
    pledgeBatchId: Optional[str] = None
    donorId: str
    donorName: str
    donorPhone: Optional[str] = None
    itemId: Optional[str] = None
    itemName: str
    quantity: float
    unit: Optional[str] = None
    dsArea: str
    reliefCamp: Optional[str] = None
    status: str = "pledged"
    donatedAt: datetime
    expiresAt: Optional[datetime] = None
    acceptedAt: Optional[datetime] = None
    acceptedByOfficerId: Optional[str] = None
    cancelledAt: Optional[datetime] = None
    cancellationReason: Optional[str] = None


class DisasterRequestGroupOut(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    reliefCamp: str
    people_count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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
    unit: Optional[str] = None
    reliefCamp: str
    dsArea: str
    gnDivision: str
    status: str
    donatedAt: datetime
    expiresAt: Optional[datetime] = None


class DonorMatchOut(BaseModel):
    donorId: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    source: str
    score: float
    compatibilityScore: float
    priorityScore: float
    modelName: str = "Linear Regression"
    donorType: str
    preferredCategory: str
    capacityLevel: str
    distanceKm: float
    distanceSource: str
    categoryMatchScore: float
    capacityMatchScore: float
    proximityScore: float
    proximityTier: str
    historyCount: int
    receivedDonationCount: int
    relevantDonationCount: int
    reasons: List[str]
    alreadyTargeted: bool = False


class DonorOutreachCreate(BaseModel):
    donorIds: List[str]


class ConsolidatedDonorMatchesCreate(BaseModel):
    requestIds: List[str]


class ConsolidatedDonorMatchesOut(BaseModel):
    matches: List[DonorMatchOut]
    eligibleDonorCount: int
    ineligibleDonorCount: int
    model: dict


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
        # Normalize legacy fractional requirements as well as newly-created
        # records. Supply requirements always represent whole usable units.
        needed = float(whole_required_quantity(item.get("neededQuantity", 0)))
        pledged = float(item.get("pledgedQuantity", 0))
        donated = float(item.get("donatedQuantity", 0))
        rem = max(0.0, needed - donated - pledged)
        items_out.append(
            RequestItemOut(
                itemId=item.get("itemId") or str(item.get("_id", "")),
                itemName=item.get("itemName", "Relief Item"),
                requiredCategory=item.get("requiredCategory") or item.get("category"),
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
                pledgeBatchId=don.get("pledgeBatchId"),
                donorId=str(don.get("donorId", "")),
                donorName=don.get("donorName", "Verified Donor"),
                donorPhone=don.get("donorPhone"),
                itemId=don.get("itemId"),
                itemName=don.get("itemName", "Relief Supply"),
                quantity=float(don.get("quantity", 0)),
                unit=don.get("unit"),
                dsArea=don.get("dsArea") or doc.get("dsArea", "Western Sector"),
                reliefCamp=doc.get("reliefCamp", "Relief Camp"),
                status=don.get("status", "pledged"),
                donatedAt=don.get("donatedAt") or datetime.now(timezone.utc),
                expiresAt=don.get("expiresAt"),
                acceptedAt=don.get("acceptedAt"),
                acceptedByOfficerId=don.get("acceptedByOfficerId"),
                cancelledAt=don.get("cancelledAt"),
                cancellationReason=don.get("cancellationReason"),
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
        latitude=doc.get("latitude") or doc.get("lat"),
        longitude=doc.get("longitude") or doc.get("lng"),
        status=doc.get("status", "remaining"),
        createdBy=str(doc.get("createdBy")) if doc.get("createdBy") is not None else None,
        createdAt=doc.get("createdAt"),
        items=items_out,
        donations=donations_out,
        targetedDonorCount=len(doc.get("targetedDonorIds", [])),
        lastOutreachAt=doc.get("lastOutreachAt"),
    )


async def _persist_whole_required_quantities(document: dict) -> None:
    """Upgrade legacy fractional request quantities when a request is read."""
    items = document.get("items", [])
    changed = False
    for item in items:
        needed = float(whole_required_quantity(item.get("neededQuantity", 0)))
        pledged = float(item.get("pledgedQuantity", 0))
        donated = float(item.get("donatedQuantity", 0))
        remaining = max(0.0, needed - donated - pledged)
        item_status = "fulfilled" if donated >= needed else "remaining"

        if (
            item.get("neededQuantity") != needed
            or item.get("remainingQuantity") != remaining
            or item.get("status") != item_status
        ):
            item["neededQuantity"] = needed
            item["remainingQuantity"] = remaining
            item["status"] = item_status
            changed = True

    request_status = (
        "fulfilled"
        if items and all(item.get("status") == "fulfilled" for item in items)
        else "remaining"
    )
    if document.get("status") != request_status:
        document["status"] = request_status
        changed = True

    if changed:
        await disaster_requests_collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"items": items, "status": request_status}},
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


async def _assigned_officer_ds_area(
    token: TokenPayload,
    db: Session,
) -> Optional[str]:
    """Return the authenticated officer's server-side DS assignment.

    Admin and authority users intentionally return ``None`` because their
    existing cross-area oversight access is unchanged.
    """
    if token.role != "disaster_officer":
        return None

    assigned_area = None
    if token.sub.isdigit():
        officer = db.query(User).filter(User.id == int(token.sub)).first()
        assigned_area = officer.assigned_ds_area if officer else None
    elif ObjectId.is_valid(token.sub):
        officer = await users_collection.find_one({"_id": ObjectId(token.sub)})
        if officer:
            assigned_area = (
                officer.get("assignedDsArea")
                or officer.get("assigned_ds_area")
                or officer.get("dsArea")
            )

    assigned_area = (assigned_area or "").strip()
    if not assigned_area:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This disaster officer account has no assigned DS area.",
        )
    return assigned_area


async def _apply_officer_scope(
    query: dict,
    token: TokenPayload,
    db: Session,
) -> dict:
    assigned_area = await _assigned_officer_ds_area(token, db)
    if assigned_area:
        query["dsArea"] = assigned_area
    return query


# ── Route Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=List[DisasterRequestGroupOut])
async def get_all_disaster_requests(
    dsArea: Optional[str] = None,
    status_filter: Optional[str] = None,
    scope: Literal["personalized", "all"] = "personalized",
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "donor", "authority", "disaster_officer"])
    ),
    db: Session = Depends(get_db),
):
    await expire_stale_pledges()
    query = {}
    donor_aliases = set()
    if _current_user.role == "volunteer":
        # A volunteer owns only the requests created with their authenticated ID.
        # Keep this restriction server-side so it cannot be bypassed by changing
        # frontend query parameters.
        query["createdBy"] = _current_user.sub
    if _current_user.role == "donor" and scope == "personalized":
        donor_aliases = set(_sql_donor_alias_ids(db, _current_user.sub))
        query["targetedDonorIds"] = {"$in": list(donor_aliases)}
    elif _current_user.role == "donor":
        donor_aliases = set(_sql_donor_alias_ids(db, _current_user.sub))
    if dsArea:
        query["dsArea"] = dsArea
    if status_filter:
        query["status"] = status_filter
    await _apply_officer_scope(query, _current_user, db)
    cursor = disaster_requests_collection.find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)
    for document in docs:
        await _persist_whole_required_quantities(document)
    if _current_user.role == "donor":
        docs = [
            {
                **document,
                "donations": [
                    donation for donation in document.get("donations", [])
                    if str(donation.get("donorId")) in donor_aliases
                ],
            }
            for document in docs
        ]
    return [format_mongo_doc(d) for d in docs]


async def _registered_donors(db: Session) -> List[dict]:
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
            "donor_type": user.donor_type,
            "preferred_donation_category": user.preferred_donation_category,
            "capacity_level": user.capacity_level,
            "latitude": user.latitude, "longitude": user.longitude,
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
            "donor_type": user.get("donorType") or user.get("donor_type"),
            "preferred_category": (
                user.get("preferredCategory")
                or user.get("preferredDonationCategory")
                or user.get("preferred_donation_category")
            ),
            "capacity_level": user.get("capacityLevel") or user.get("capacity_level"),
            "latitude": user.get("latitude") or user.get("lat"),
            "longitude": user.get("longitude") or user.get("lng"),
        })
    return donors


async def _rank_registered_donors(db: Session, request_docs: List[dict]) -> tuple[List[DonorMatchOut], int]:
    donors = await _registered_donors(db)

    history_docs = await disaster_requests_collection.find(
        {"donations.0": {"$exists": True}}, {"donations": 1}
    ).to_list(length=1000)
    target_items = {
        _normalise(item.get("itemName")) for request_doc in request_docs for item in request_doc.get("items", [])
        if item.get("itemName")
    }
    targeted_ids = {
        str(value) for request_doc in request_docs for value in request_doc.get("targetedDonorIds", [])
    }

    matches = []
    ineligible_count = 0
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
        _priority_score, prediction = predict_compatibility(donor, request_docs)
        if not prediction.get("eligible"):
            ineligible_count += 1
            continue

        distance_km = float(prediction["distanceKm"])
        distance_source = prediction["distanceSource"]
        proximity_tier = f"{distance_km:g} km ({distance_source})"
        reasons = [
            f"{prediction['preferredCategory']} preference; {prediction['capacityLevel']} capacity",
            f"Distance input: {distance_km:g} km from {distance_source}",
        ]
        if donor_history:
            reasons.append(f"History (not a model feature): {len(donor_history)} pledge(s), {received_count} received")
        else:
            reasons.append("No historical response feature is used by this synthetic compatibility model")
        if relevant_count:
            reasons.append(f"{relevant_count} prior donation item match(es), shown for context only")

        matches.append(DonorMatchOut(
            donorId=donor["donorId"], name=donor["name"], email=donor.get("email"),
            phone=donor.get("phone"), address=donor.get("address"), source=donor["source"],
            score=prediction["compatibilityScore"],
            compatibilityScore=prediction["compatibilityScore"],
            priorityScore=prediction["priorityScore"],
            donorType=prediction["donorType"],
            preferredCategory=prediction["preferredCategory"],
            capacityLevel=prediction["capacityLevel"],
            distanceKm=distance_km, distanceSource=distance_source,
            categoryMatchScore=prediction["categoryMatchScore"],
            capacityMatchScore=prediction["capacityMatchScore"],
            proximityScore=prediction["proximityScore"],
            proximityTier=proximity_tier,
            historyCount=len(donor_history), receivedDonationCount=received_count,
            relevantDonationCount=relevant_count, reasons=reasons,
            alreadyTargeted=donor_id in targeted_ids,
        ))

    return sorted(matches, key=lambda match: (-match.priorityScore, match.name.casefold())), ineligible_count


@router.get("/donor-insights/model-info")
async def get_donor_matching_model_info(
    _current_user: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
):
    try:
        load_info = model_information()
        # Force artifact loading here so the health response reflects runtime compatibility.
        from app.services.donor_matching import load_pipeline
        load_pipeline()
        return load_info
    except DonorModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/donor-insights/donor-matches", response_model=ConsolidatedDonorMatchesOut)
async def get_consolidated_donor_matches(
    payload: ConsolidatedDonorMatchesCreate,
    _current_user: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
    db: Session = Depends(get_db),
):
    ids = list(dict.fromkeys(payload.requestIds))
    if not ids or any(not ObjectId.is_valid(value) for value in ids):
        raise HTTPException(status_code=400, detail="Select valid GN-level request records")
    query = {"_id": {"$in": [ObjectId(value) for value in ids]}}
    await _apply_officer_scope(query, _current_user, db)
    documents = await disaster_requests_collection.find(query).to_list(length=200)
    if len(documents) != len(ids):
        raise HTTPException(status_code=404, detail="One or more donation request records were not found")
    group_keys = {
        (_normalise(doc.get("dsArea")), _normalise(doc.get("gnDivision")), _normalise(doc.get("disasterType")))
        for doc in documents
    }
    if len(group_keys) != 1:
        raise HTTPException(status_code=400, detail="Requests must belong to one GN division and disaster type")
    try:
        matches, ineligible_count = await _rank_registered_donors(db, documents)
        return ConsolidatedDonorMatchesOut(
            matches=matches,
            eligibleDonorCount=len(matches),
            ineligibleDonorCount=ineligible_count,
            model=model_information(),
        )
    except DonorModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{req_id}/donor-matches", response_model=List[DonorMatchOut])
async def get_ranked_donor_matches(
    req_id: str,
    _current_user: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    query = {"_id": ObjectId(req_id)}
    await _apply_officer_scope(query, _current_user, db)
    request_doc = await disaster_requests_collection.find_one(query)
    if not request_doc:
        raise HTTPException(status_code=404, detail="Disaster request not found")
    try:
        matches, _ineligible_count = await _rank_registered_donors(db, [request_doc])
        return matches
    except DonorModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{req_id}/outreach", response_model=DonorOutreachResult)
async def send_personalized_donor_outreach(
    req_id: str,
    payload: DonorOutreachCreate,
    token_payload: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    donor_ids = list(dict.fromkeys(str(value).strip() for value in payload.donorIds if str(value).strip()))
    if not donor_ids:
        raise HTTPException(status_code=400, detail="Select at least one donor")

    now = datetime.now(timezone.utc)
    query = {"_id": ObjectId(req_id)}
    await _apply_officer_scope(query, token_payload, db)
    result = await disaster_requests_collection.update_one(
        query,
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
        message=f"Personalized request published to {len(donor_ids)} donor portal(s)",
    )


@router.get("/officer/pledges", response_model=List[OfficerPledgeItemOut])
async def get_officer_pending_pledges(
    _current_user: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer"])
    ),
    db: Session = Depends(get_db),
):
    await expire_stale_pledges()
    query = {"donations.status": "pledged"}
    await _apply_officer_scope(query, _current_user, db)
    cursor = disaster_requests_collection.find(query)
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
                        unit=don.get("unit", "units"),
                        reliefCamp=relief_camp,
                        dsArea=ds_area,
                        gnDivision=gn_division,
                        status=don.get("status", "pledged"),
                        donatedAt=don.get("donatedAt") or datetime.now(timezone.utc),
                        expiresAt=don.get("expiresAt"),
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
    await expire_stale_pledges()
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")
    query = {"_id": ObjectId(req_id)}
    if _current_user.role == "volunteer":
        query["createdBy"] = _current_user.sub
    await _apply_officer_scope(query, _current_user, db)
    document = await disaster_requests_collection.find_one(query)
    if not document:
        raise HTTPException(status_code=404, detail="Disaster request not found")
    await _persist_whole_required_quantities(document)
    if _current_user.role == "donor":
        identity_ids = set(_sql_donor_alias_ids(db, _current_user.sub))
        document = {
            **document,
            "donations": [
                donation for donation in document.get("donations", [])
                if str(donation.get("donorId")) in identity_ids
            ],
        }
    return format_mongo_doc(document)


@router.patch("/{req_id}/donations/{donation_id}/accept")
async def accept_donation_at_ds_office(
    req_id: str,
    donation_id: str,
    token_payload: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer"])
    ),
    db: Session = Depends(get_db),
):
    await expire_stale_pledges()
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid Request ObjectId")

    query = {"_id": ObjectId(req_id)}
    await _apply_officer_scope(query, token_payload, db)
    doc = await disaster_requests_collection.find_one(query)
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
            if don.get("status") == "cancelled":
                raise HTTPException(status_code=400, detail="This pledge expired and can no longer be received")
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
                    needed_quantity = float(
                        whole_required_quantity(itm.get("neededQuantity", 0))
                    )
                    itm["remainingQuantity"] = max(
                        0.0,
                        needed_quantity - itm["donatedQuantity"],
                    )
                    if itm["donatedQuantity"] >= needed_quantity:
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
        itm["neededQuantity"] = float(
            whole_required_quantity(itm["neededQuantity"])
        )
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
    await expire_stale_pledges()
    if not ObjectId.is_valid(req_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=12)
    pledge_batch_id = f"PLG-{str(ObjectId())[-8:].upper()}"
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
            float(whole_required_quantity(target_item.get("neededQuantity", 0)))
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
            "pledgeBatchId": pledge_batch_id,
            "donorId": token_payload.sub,
            "donorName": donor_name,
            "donorPhone": donor_phone,
            "donorEmail": donor_email,
            "itemId": target_item.get("itemId"),
            "itemName": p.itemName,
            "quantity": float(p.quantity),
            "unit": target_item.get("unit", "units"),
            "dsArea": doc.get("dsArea", "Western Sector"),
            "reliefCamp": doc.get("reliefCamp"),
            "status": "pledged",
            "donatedAt": now,
            "expiresAt": expires_at,
        }
        new_donations.append(donation_entry)

        target_item["pledgedQuantity"] = float(target_item.get("pledgedQuantity", 0)) + float(p.quantity)

    await disaster_requests_collection.update_one(
        {"_id": ObjectId(req_id)},
        {"$push": {"donations": {"$each": new_donations}}, "$set": {"items": items}}
    )

    updated_document = await disaster_requests_collection.find_one({"_id": ObjectId(req_id)})
    return format_mongo_doc(updated_document)
