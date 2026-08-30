from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.models.disaster_donation_request import (
    DisasterDonationRequestCreate,
    DisasterDonationRequestResponse,
    BatchPledgeCreate,
    RequestItem,
    DonationEntry,
)
from app.my_database import disaster_donation_request_collection, user_collection
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/disaster-donation-requests", tags=["Disaster Donation Requests"]
)


def format_request_doc(doc: dict) -> DisasterDonationRequestResponse:
    items = []
    for item in doc.get("items", []):
        needed = float(item.get("neededQuantity", 0.0))
        donated = float(item.get("donatedQuantity", 0.0))
        pledged = float(item.get("pledgedQuantity", 0.0))
        remaining = max(0.0, needed - donated)
        item_status = "fulfilled" if remaining <= 0 else "remaining"

        items.append(
            RequestItem(
                itemId=item.get("itemId"),
                itemName=item.get("itemName"),
                unit=item.get("unit"),
                neededQuantity=needed,
                pledgedQuantity=pledged,
                donatedQuantity=donated,
                remainingQuantity=remaining,
                status=item_status,
            )
        )

    donations = []
    for don in doc.get("donations", []):
        donations.append(
            DonationEntry(
                donationId=don.get("donationId"),
                donorId=don.get("donorId"),
                donorName=don.get("donorName", "Anonymous"),
                donorPhone=don.get("donorPhone"),
                itemId=don.get("itemId"),
                itemName=don.get("itemName"),
                quantity=float(don.get("quantity", 0.0)),
                dsArea=don.get("dsArea"),
                status=don.get("status", "pledged"),
                donatedAt=don.get("donatedAt"),
                acceptedByOfficerId=don.get("acceptedByOfficerId"),
                acceptedAt=don.get("acceptedAt"),
            )
        )

    # Calculate overall status
    all_fulfilled = len(items) > 0 and all(i.remainingQuantity <= 0 for i in items)
    req_status = "fulfilled" if all_fulfilled else "remaining"

    return DisasterDonationRequestResponse(
        id=str(doc["_id"]),
        disasterType=doc.get("disasterType"),
        severity=doc.get("severity"),
        dsArea=doc.get("dsArea"),
        gnDivision=doc.get("gnDivision"),
        reliefCamp=doc.get("reliefCamp"),
        people_count=doc.get("people_count", 0),
        status=req_status,
        createdBy=doc.get("createdBy"),
        createdAt=doc.get("createdAt"),
        items=items,
        donations=donations,
    )


# 1. CREATE Disaster Donation Request (Volunteer or Admin)
@router.post(
    "",
    response_model=DisasterDonationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_disaster_donation_request(
    request_data: DisasterDonationRequestCreate,
    current_user: dict = Depends(get_current_user),
):
    if current_user["userType"] not in ["volunteer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only volunteers and admins can create disaster donation requests",
        )

    items_list = []
    for item in request_data.items:
        needed = float(item.neededQuantity)
        items_list.append(
            {
                "itemId": item.itemId,
                "itemName": item.itemName,
                "unit": item.unit,
                "neededQuantity": needed,
                "pledgedQuantity": 0.0,
                "donatedQuantity": 0.0,
                "remainingQuantity": needed,
                "status": "remaining",
            }
        )

    new_doc = {
        "disasterType": request_data.disasterType,
        "severity": request_data.severity,
        "dsArea": request_data.dsArea,
        "gnDivision": request_data.gnDivision,
        "reliefCamp": request_data.reliefCamp,
        "people_count": request_data.people_count,
        "status": "remaining",
        "createdBy": current_user["userId"],
        "createdAt": datetime.now(timezone.utc),
        "items": items_list,
        "donations": [],
    }

    result = await disaster_donation_request_collection.insert_one(new_doc)
    new_doc["_id"] = result.inserted_id
    return format_request_doc(new_doc)


# 2. GET ALL Requests (Filterable by dsArea and status)
@router.get("", response_model=List[DisasterDonationRequestResponse])
async def get_all_disaster_requests(
    dsArea: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query = {}
    if dsArea:
        query["dsArea"] = dsArea
    if status_filter:
        query["status"] = status_filter

    cursor = disaster_donation_request_collection.find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)
    return [format_request_doc(doc) for doc in docs]


# 3. GET Specific Request by ID
@router.get("/{request_id}", response_model=DisasterDonationRequestResponse)
async def get_disaster_request_by_id(
    request_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid Request ID format")

    doc = await disaster_donation_request_collection.find_one(
        {"_id": ObjectId(request_id)}
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail="Disaster donation request not found"
        )

    return format_request_doc(doc)


# 4. PLEDGE Multiple Items to a Request (Donor Only)
@router.post("/{request_id}/pledge", response_model=DisasterDonationRequestResponse)
async def pledge_donation_items(
    request_id: str,
    payload: BatchPledgeCreate,
    current_user: dict = Depends(get_current_user),
):
    if current_user["userType"] not in ["donor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only donors can pledge items"
        )

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid Request ID format")

    doc = await disaster_donation_request_collection.find_one(
        {"_id": ObjectId(request_id)}
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail="Disaster donation request not found"
        )

    # Fetch donor information
    donor_doc = await user_collection.find_one(
        {"_id": ObjectId(current_user["userId"])}
    )
    donor_name = (
        f"{donor_doc.get('firstName', '')} {donor_doc.get('lastName', '')}".strip()
        if donor_doc
        else "Anonymous"
    )
    donor_phone = donor_doc.get("phone", "") if donor_doc else ""

    items_list = doc.get("items", [])
    new_donations = []
    update_set = {}

    for pledge in payload.pledges:
        target_item = None
        target_index = -1
        for idx, itm in enumerate(items_list):
            if (pledge.itemId and itm.get("itemId") == pledge.itemId) or (
                itm.get("itemName").lower() == pledge.itemName.lower()
            ):
                target_item = itm
                target_index = idx
                break

        if not target_item:
            raise HTTPException(
                status_code=404,
                detail=f"Item '{pledge.itemName}' is not requested in this appeal",
            )

        needed = float(target_item.get("neededQuantity", 0.0))
        donated = float(target_item.get("donatedQuantity", 0.0))
        pledged = float(target_item.get("pledgedQuantity", 0.0))

        available_to_pledge = needed - (pledged + donated)
        if pledge.quantity > available_to_pledge:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot pledge {pledge.quantity} of {pledge.itemName}. Maximum available to pledge is {available_to_pledge} {target_item.get('unit')}",
            )

        new_pledged = pledged + float(pledge.quantity)
        items_list[target_index]["pledgedQuantity"] = new_pledged
        update_set[f"items.{target_index}.pledgedQuantity"] = new_pledged

        new_donations.append(
            {
                "donationId": str(uuid.uuid4()),
                "donorId": current_user["userId"],
                "donorName": donor_name,
                "donorPhone": donor_phone,
                "itemId": target_item.get("itemId"),
                "itemName": target_item.get("itemName"),
                "quantity": float(pledge.quantity),
                "dsArea": doc.get("dsArea"),
                "status": "pledged",
                "donatedAt": datetime.now(timezone.utc),
                "acceptedByOfficerId": None,
                "acceptedAt": None,
            }
        )

    updated_doc = await disaster_donation_request_collection.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": update_set, "$push": {"donations": {"$each": new_donations}}},
        return_document=True,
    )

    return format_request_doc(updated_doc)


# 5. ACCEPT PLEDGED DONATION (Disaster Officer marks items received)
@router.patch(
    "/{request_id}/donations/{donation_id}/accept",
    response_model=DisasterDonationRequestResponse,
)
async def accept_pledged_donation(
    request_id: str, donation_id: str, current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] not in ["disaster_officer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only disaster officers and admins can mark pledges as received",
        )

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid Request ID format")

    doc = await disaster_donation_request_collection.find_one(
        {"_id": ObjectId(request_id)}
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail="Disaster donation request not found"
        )

    donations = doc.get("donations", [])
    target_donation = None
    donation_idx = -1
    for idx, d in enumerate(donations):
        if d.get("donationId") == donation_id:
            target_donation = d
            donation_idx = idx
            break

    if not target_donation:
        raise HTTPException(status_code=404, detail="Donation pledge record not found")

    if target_donation.get("status") == "received":
        raise HTTPException(
            status_code=400, detail="This donation has already been marked as received"
        )

    # Match the corresponding item in the items array
    item_idx = -1
    for idx, itm in enumerate(doc.get("items", [])):
        if itm.get("itemName").lower() == target_donation.get("itemName").lower():
            item_idx = idx
            break

    if item_idx == -1:
        raise HTTPException(
            status_code=500,
            detail="Corrupted data: referenced item not found in request items",
        )

    target_item = doc["items"][item_idx]
    pledged_qty = float(target_item.get("pledgedQuantity", 0.0))
    donated_qty = float(target_item.get("donatedQuantity", 0.0))
    needed_qty = float(target_item.get("neededQuantity", 0.0))
    transfer_qty = float(target_donation.get("quantity", 0.0))

    new_pledged = max(0.0, pledged_qty - transfer_qty)
    new_donated = donated_qty + transfer_qty
    new_remaining = max(0.0, needed_qty - new_donated)
    item_status = "fulfilled" if new_remaining <= 0 else "remaining"

    # Update item in memory to test overall fulfillment
    doc["items"][item_idx]["pledgedQuantity"] = new_pledged
    doc["items"][item_idx]["donatedQuantity"] = new_donated
    doc["items"][item_idx]["remainingQuantity"] = new_remaining
    doc["items"][item_idx]["status"] = item_status

    all_items_fulfilled = all(
        float(i.get("neededQuantity", 0)) - float(i.get("donatedQuantity", 0)) <= 0
        for i in doc["items"]
    )
    new_request_status = "fulfilled" if all_items_fulfilled else "remaining"

    updated_doc = await disaster_donation_request_collection.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                f"donations.{donation_idx}.status": "received",
                f"donations.{donation_idx}.acceptedByOfficerId": current_user["userId"],
                f"donations.{donation_idx}.acceptedAt": datetime.now(timezone.utc),
                f"items.{item_idx}.pledgedQuantity": new_pledged,
                f"items.{item_idx}.donatedQuantity": new_donated,
                f"items.{item_idx}.remainingQuantity": new_remaining,
                f"items.{item_idx}.status": item_status,
                "status": new_request_status,
            }
        },
        return_document=True,
    )

    return format_request_doc(updated_doc)


# 6. GET Officer Pending Pledges (Filtered by DS Area)
@router.get("/officer/pledges", response_model=List[dict])
async def get_officer_pending_pledges(
    dsArea: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] not in ["disaster_officer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to disaster officers and admins",
        )

    query = {"donations.status": "pledged"}
    if dsArea:
        query["dsArea"] = dsArea

    cursor = disaster_donation_request_collection.find(query)
    requests = await cursor.to_list(length=200)

    pending_list = []
    for req in requests:
        for don in req.get("donations", []):
            if don.get("status") == "pledged":
                pending_list.append(
                    {
                        "requestId": str(req["_id"]),
                        "disasterType": req.get("disasterType"),
                        "severity": req.get("severity"),
                        "dsArea": req.get("dsArea"),
                        "gnDivision": req.get("gnDivision"),
                        "reliefCamp": req.get("reliefCamp"),
                        "donationId": don.get("donationId"),
                        "donorId": don.get("donorId"),
                        "donorName": don.get("donorName"),
                        "donorPhone": don.get("donorPhone"),
                        "itemName": don.get("itemName"),
                        "quantity": don.get("quantity"),
                        "donatedAt": don.get("donatedAt"),
                    }
                )

    return pending_list
