from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List

from app.models.donation_item import (
    DonationItemCreate,
    DonationItemResponse
)
from app.database import donation_items_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/donation-items", tags=["Donation Items"])

def format_donation_item(doc) -> DonationItemResponse:
    return DonationItemResponse(
        itemId=str(doc["_id"]),
        item=doc["item"],
        quantityPerPerson=doc["quantityPerPerson"],
        unit=doc["unit"]
    )

# 1. CREATE Donation Item (Admin only)
@router.post("", response_model=DonationItemResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_item(
    item_data: DonationItemCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create donation catalog items"
        )

    new_item = item_data.model_dump()
    result = await donation_items_collection.insert_one(new_item)

    return DonationItemResponse(
        itemId=str(result.inserted_id),
        item=item_data.item,
        quantityPerPerson=item_data.quantityPerPerson,
        unit=item_data.unit
    )

# 2. VIEW ALL Donation Items (Accessible by authenticated users)
@router.get("", response_model=List[DonationItemResponse])
async def get_all_donation_items(
    current_user: dict = Depends(get_current_user)
):
    cursor = donation_items_collection.find()
    items = await cursor.to_list(length=100)
    return [format_donation_item(doc) for doc in items]

# 3. VIEW Donation Item BY ID
@router.get("/{item_id}", response_model=DonationItemResponse)
async def get_donation_item_by_id(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Item ID format"
        )

    doc = await donation_items_collection.find_one({"_id": ObjectId(item_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation item not found"
        )

# BULK CREATE Donation Items
@router.post("/bulk", response_model=List[DonationItemResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_donation_items(
    items_data: List[DonationItemCreate],
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create donation catalog items"
        )

    new_items = [item.model_dump() for item in items_data]
    result = await donation_items_collection.insert_many(new_items)

    response = []
    for doc_id, item in zip(result.inserted_ids, items_data):
        response.append(
            DonationItemResponse(
                itemId=str(doc_id),
                item=item.item,
                quantityPerPerson=item.quantityPerPerson,
                unit=item.unit
            )
        )
    return response

    return format_donation_item(doc)