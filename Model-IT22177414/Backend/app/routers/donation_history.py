from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from app.models.donation_history import (
    DonationHistoryCreate,
    DonationHistoryResponse
)
from app.database import donation_history_collection, donation_request_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/donation-history", tags=["Donation History"])

def format_donation_history(doc) -> DonationHistoryResponse:
    return DonationHistoryResponse(
        donationId=str(doc["_id"]),
        donationRequestId=doc["donationRequestId"],
        donorId=doc["donorId"],
        donatedItems=doc["donatedItems"],
        createdAt=doc["createdAt"]
    )

# 1. CREATE Donation Record (Donor creates a donation)
@router.post("", response_model=DonationHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_history(
    donation_data: DonationHistoryCreate,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(donation_data.donationRequestId):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Donation Request ID format"
        )

    # Check if target donation request exists
    request_doc = await donation_request_collection.find_one(
        {"_id": ObjectId(donation_data.donationRequestId)}
    )
    if not request_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced Donation Request not found"
        )

    new_donation = {
        "donationRequestId": donation_data.donationRequestId,
        "donorId": current_user["userId"],
        "donatedItems": [item.model_dump() for item in donation_data.donatedItems],
        "createdAt": datetime.now(timezone.utc)
    }

    result = await donation_history_collection.insert_one(new_donation)

    return DonationHistoryResponse(
        donationId=str(result.inserted_id),
        donationRequestId=donation_data.donationRequestId,
        donorId=current_user["userId"],
        donatedItems=donation_data.donatedItems,
        createdAt=new_donation["createdAt"]
    )

# 2. GET ALL Donation Histories (Admins view all; Donors view only their own)
@router.get("", response_model=List[DonationHistoryResponse])
async def get_all_donation_history(
    current_user: dict = Depends(get_current_user)
):
    # Filter for donors to only see their records; admins see everything
    query = {} if current_user["userType"] == "admin" else {"donorId": current_user["userId"]}
    
    cursor = donation_history_collection.find(query)
    donations = await cursor.to_list(length=100)
    return [format_donation_history(doc) for doc in donations]

# 3. GET Donation History BY ID
@router.get("/{donation_id}", response_model=DonationHistoryResponse)
async def get_donation_history_by_id(
    donation_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(donation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Donation ID format"
        )

    doc = await donation_history_collection.find_one({"_id": ObjectId(donation_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation record not found"
        )

    # Restrict donors to only view their own donation record
    if current_user["userType"] != "admin" and doc["donorId"] != current_user["userId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this donation record"
        )

    return format_donation_history(doc)

# 4. GET ALL Donations by a Specific Donor ID (Convenience endpoint for Admins/Donors)
@router.get("/donor/{donor_id}", response_model=List[DonationHistoryResponse])
async def get_donations_by_donor_id(
    donor_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin" and current_user["userId"] != donor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these donations"
        )

    cursor = donation_history_collection.find({"donorId": donor_id})
    donations = await cursor.to_list(length=100)
    return [format_donation_history(doc) for doc in donations]


# 5. GET ALL Donation History Records for a Specific Donation Request ID
@router.get("/request/{donation_request_id}", response_model=List[DonationHistoryResponse])
async def get_donations_by_request_id(
    donation_request_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(donation_request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Donation Request ID format"
        )

    # Verify if the donation request actually exists
    request_exists = await donation_request_collection.find_one(
        {"_id": ObjectId(donation_request_id)}
    )
    if not request_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation Request not found"
        )

    # Fetch all history items tied to this request ID
    cursor = donation_history_collection.find({"donationRequestId": donation_request_id})
    donations = await cursor.to_list(length=100)
    
    return [format_donation_history(doc) for doc in donations]