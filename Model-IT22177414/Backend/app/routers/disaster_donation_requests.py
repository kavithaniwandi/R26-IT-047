from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from app.models.donation_request import (
    DonationRequestCreate,
    DonationRequestResponse,
    DonationRequestUpdateStatus
)
from app.database import donation_request_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/disaster-donation-requests", tags=["Disaster Donation Requests"])

def format_donation_request(doc) -> DonationRequestResponse:
    # Ensure items carry remaining and donated calculations
    formatted_items = []
    for item in doc.get("items", []):
        quantity = item.get("quantity", 0.0)
        donated = item.get("donated", 0.0)
        remaining = item.get("remaining", max(quantity - donated, 0.0))
        item_status = item.get("status", "fulfilled" if remaining <= 0 else "remaining")
        formatted_items.append({
            "itemName": item.get("itemName"),
            "unit": item.get("unit"),
            "quantity": quantity,
            "donated": donated,
            "remaining": remaining,
            "status": item_status
        })

    return DonationRequestResponse(
        id=str(doc["_id"]),
        disasterType=doc.get("disasterType", "Flood"),
        severity=doc.get("severity", "High"),
        dsArea=doc.get("dsArea", "Kaduwela"),
        gnDivision=doc.get("gnDivision", "Unknown"),
        population=doc.get("population", 0),
        status=doc.get("status", "remaining"),
        items=formatted_items,
        createdBy=doc.get("createdBy", ""),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc))
    )

# 1. CREATE Donation Request
@router.post("", response_model=DonationRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_request(
    request_data: DonationRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    items_dump = []
    for item in request_data.items:
        i_dict = item.model_dump()
        if i_dict["remaining"] is None:
            i_dict["remaining"] = max(i_dict["quantity"] - i_dict["donated"], 0.0)
        items_dump.append(i_dict)

    new_request = {
        "disasterType": request_data.disasterType,
        "severity": request_data.severity,
        "dsArea": request_data.dsArea,
        "gnDivision": request_data.gnDivision,
        "population": request_data.population,
        "status": request_data.status,
        "items": items_dump,
        "createdBy": current_user["userId"],
        "createdAt": datetime.now(timezone.utc)
    }

    result = await donation_request_collection.insert_one(new_request)
    new_request["_id"] = result.inserted_id

    return format_donation_request(new_request)

# 2. VIEW ALL Donation Requests (Sorted newest first)
@router.get("", response_model=List[DonationRequestResponse])
async def get_all_donation_requests(
    current_user: dict = Depends(get_current_user)
):
    cursor = donation_request_collection.find().sort("createdAt", -1)
    requests = await cursor.to_list(length=200)
    return [format_donation_request(doc) for doc in requests]

# 3. VIEW Donation Request BY ID
@router.get("/{request_id}", response_model=DonationRequestResponse)
async def get_donation_request_by_id(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format"
        )

    doc = await donation_request_collection.find_one({"_id": ObjectId(request_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found"
        )

    return format_donation_request(doc)

# 4. UPDATE Status / Items
@router.patch("/{request_id}", response_model=DonationRequestResponse)
async def update_donation_request(
    request_id: str,
    update_data: DonationRequestUpdateStatus,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format"
        )

    update_fields = {}
    if update_data.status is not None:
        update_fields["status"] = update_data.status
    if update_data.items is not None:
        update_fields["items"] = [item.model_dump() for item in update_data.items]

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided"
        )

    result = await donation_request_collection.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": update_fields},
        return_document=True
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found"
        )

    return format_donation_request(result)