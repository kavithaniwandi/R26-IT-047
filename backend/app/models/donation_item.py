from __future__ import annotations

from pydantic import BaseModel, Field


class DonationItemCreate(BaseModel):
    item: str = Field(..., min_length=2)
    quantityPerPerson: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)


class DonationItemResponse(BaseModel):
    itemId: str
    item: str
    quantityPerPerson: float
    unit: str
