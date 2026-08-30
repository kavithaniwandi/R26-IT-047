from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from app.models.my_user import UserResponse
from app.my_database import user_collection
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
        createdAt=user_doc["createdAt"],
    )


@router.get("", response_model=List[UserResponse])
async def get_users(
    userType: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    # Allow admins and disaster officers to query users
    if current_user["userType"] not in ["admin", "disaster_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin and disaster officer users",
        )

    query = {}
    if userType:
        query["userType"] = userType

    cursor = user_collection.find(query)
    users = await cursor.to_list(length=200)
    return [format_user(doc) for doc in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, current_user: dict = Depends(get_current_user)):
    if (
        current_user["userType"] not in ["admin", "disaster_officer"]
        and current_user["userId"] != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile",
        )

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return format_user(user)
