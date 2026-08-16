from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class DonationItem(BaseModel):
    itemName: str = Field(..., min_length=2, example="Rice")
    unit: str = Field(..., example="kg")
    quantity: float = Field(..., gt=0, example=50.0)

class DonationRequestCreate(BaseModel):
    items: List[DonationItem] = Field(..., min_items=1)

class DonationRequestResponse(BaseModel):
    id: str
    items: List[DonationItem]
    createdBy: str
    createdAt: datetime