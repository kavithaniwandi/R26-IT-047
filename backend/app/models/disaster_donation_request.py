from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RequestItem(BaseModel):
    itemId: Optional[str] = None
    itemName: str = Field(..., min_length=2)
    requiredCategory: Optional[Literal["Blankets", "Dry Rations", "Medical", "Tarpaulins", "Water"]] = None
    unit: str = Field(..., min_length=1)
    neededQuantity: float = Field(..., gt=0)
    pledgedQuantity: float = Field(default=0.0, ge=0)
    donatedQuantity: float = Field(default=0.0, ge=0)
    remainingQuantity: Optional[float] = None
    status: Literal["remaining", "fulfilled"] = "remaining"

    @field_validator("neededQuantity", mode="before")
    @classmethod
    def round_required_quantity_up(cls, value: float) -> int:
        """Relief requests must reserve enough whole supply units."""
        return ceil(float(value))


class DonationEntry(BaseModel):
    donationId: str
    pledgeBatchId: Optional[str] = None
    donorId: str
    donorName: str
    donorPhone: Optional[str] = None
    itemId: Optional[str] = None
    itemName: str
    quantity: float = Field(..., gt=0)
    unit: Optional[str] = None
    dsArea: str
    status: Literal["pledged", "received", "cancelled"] = "pledged"
    donatedAt: datetime
    expiresAt: Optional[datetime] = None
    acceptedByOfficerId: Optional[str] = None
    acceptedAt: Optional[datetime] = None
    cancelledAt: Optional[datetime] = None
    cancellationReason: Optional[str] = None


class DisasterDonationRequestCreate(BaseModel):
    disasterType: Literal["Flood", "Landslide", "Tsunami", "Drought", "Fire", "Other"] = "Flood"
    severity: Literal["Low", "Moderate", "High", "Critical"] = "High"
    dsArea: str = Field(..., min_length=2)
    gnDivision: str = Field(..., min_length=2)
    reliefCamp: str = Field(..., min_length=2)
    people_count: int = Field(default=1, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    items: List[RequestItem] = Field(..., min_length=1)


class PledgeItem(BaseModel):
    itemName: str
    quantity: float = Field(..., gt=0)
    itemId: Optional[str] = None


class BatchPledgeCreate(BaseModel):
    pledges: List[PledgeItem] = Field(..., min_length=1)


class DisasterDonationRequestResponse(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    reliefCamp: str
    people_count: int
    status: str
    createdBy: Optional[str] = None
    createdAt: Optional[datetime] = None
    items: List[RequestItem]
    donations: List[DonationEntry]
