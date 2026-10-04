"""Read-only access to the original MongoDB component user directory."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import TokenPayload, require_role
from app.database import users_collection


router = APIRouter(prefix="/component-users", tags=["Component Users (MongoDB)"])


def _format(document: dict) -> dict:
    return {
        "userId": str(document["_id"]),
        "firstName": document.get("firstName", ""),
        "lastName": document.get("lastName", ""),
        "email": document.get("email"),
        "phone": document.get("phone"),
        "address": document.get("address"),
        "userType": document.get("userType"),
        "createdAt": document.get("createdAt") or datetime.now(timezone.utc),
    }


@router.get("")
async def list_component_users(
    userType: Optional[str] = None,
    _user: TokenPayload = Depends(require_role(["admin", "disaster_officer"])),
):
    query = {"userType": userType} if userType else {}
    documents = await users_collection.find(query).sort("createdAt", -1).to_list(length=200)
    return [_format(document) for document in documents]


@router.get("/{user_id}")
async def get_component_user(
    user_id: str,
    user: TokenPayload = Depends(require_role(["admin", "disaster_officer", "donor", "volunteer"])),
):
    if user.role not in {"admin", "disaster_officer"} and user.sub != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")
    document = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not document:
        raise HTTPException(status_code=404, detail="User not found")
    return _format(document)
