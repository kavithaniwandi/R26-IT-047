"""MongoDB donation-item catalog used by the disaster request workflow."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import TokenPayload, require_role
from app.database import donation_items_collection


router = APIRouter(prefix="/donation-items", tags=["Disaster Donation Catalog (MongoDB)"])


class DonationItemCreate(BaseModel):
    item: str = Field(..., min_length=2)
    unit: str = Field(default="units", min_length=1)
    quantityPerPerson: float = Field(default=1.0, gt=0)


def _format(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "itemId": str(document["_id"]),
        "item": document.get("item", "Relief Item"),
        "unit": document.get("unit", "units"),
        "quantityPerPerson": float(document.get("quantityPerPerson", 1.0)),
    }


@router.get("")
async def list_donation_items(
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "donor", "authority", "disaster_officer"])
    ),
):
    documents = await donation_items_collection.find().sort("item", 1).to_list(length=300)
    return [_format(document) for document in documents]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_donation_item(
    payload: DonationItemCreate,
    _current_user: TokenPayload = Depends(require_role(["admin"])),
):
    document = payload.model_dump()
    result = await donation_items_collection.insert_one(document)
    document["_id"] = result.inserted_id
    return _format(document)


@router.delete("/{item_id}")
async def delete_donation_item(
    item_id: str,
    _current_user: TokenPayload = Depends(require_role(["admin"])),
):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid donation item ID")
    result = await donation_items_collection.delete_one({"_id": ObjectId(item_id)})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Donation item not found")
    return {"message": "Donation item deleted"}
