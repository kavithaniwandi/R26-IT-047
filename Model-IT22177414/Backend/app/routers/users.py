from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from app.models.user import UserResponse
from app.database import user_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

def format_user(user_doc) -> UserResponse:
    return UserResponse(
        userId=str(user_doc["_id"]),
        firstName=user_doc["firstName"],
        lastName=user_doc["lastName"],
        email=user_doc["email"],
        phone=user_doc["phone"],
        userType=user_doc["userType"],
        createdAt=user_doc["createdAt"]
    )

@router.get("/donors", response_model=List[UserResponse])
async def get_all_donors(current_user: dict = Depends(get_current_user)):
    if current_user["userType"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin users only"
        )

    cursor = user_collection.find({"userType": "donor"})
    donors = await cursor.to_list(length=100)
    return [format_user(doc) for doc in donors]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, current_user: dict = Depends(get_current_user)):
    # Donors can only access their own profile; admins can access any profile
    if current_user["userType"] != "admin" and current_user["userId"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile"
        )

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return format_user(user)