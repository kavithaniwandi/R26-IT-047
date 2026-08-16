from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from app.models.donation_request import (
    DonationRequestCreate,
    DonationRequestResponse
)
from app.database import donation_request_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/disaster-donation-requests", tags=["Disaster Donation Requests"])

def format_donation_request(doc) -> DonationRequestResponse:
    return DonationRequestResponse(
        id=str(doc["_id"]),
        items=doc["items"],
        createdBy=doc["createdBy"],
        createdAt=doc["createdAt"]
    )

# 1. CREATE Donation Request
@router.post("", response_model=DonationRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_request(
    request_data: DonationRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    new_request = {
        "items": [item.model_dump() for item in request_data.items],
        "createdBy": current_user["userId"],
        "createdAt": datetime.now(timezone.utc)
    }

    result = await donation_request_collection.insert_one(new_request)

    return DonationRequestResponse(
        id=str(result.inserted_id),
        items=request_data.items,
        createdBy=new_request["createdBy"],
        createdAt=new_request["createdAt"]
    )

# 2. VIEW ALL Donation Requests
@router.get("", response_model=List[DonationRequestResponse])
async def get_all_donation_requests(
    current_user: dict = Depends(get_current_user)
):
    cursor = donation_request_collection.find()
    requests = await cursor.to_list(length=100)
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