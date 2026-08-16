from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class DonatedItem(BaseModel):
    itemName: str = Field(..., min_length=2)
    unit: str = Field(...)
    quantity: float = Field(..., gt=0, example=10.0)

class DonationHistoryCreate(BaseModel):
    donationRequestId: str = Field(...)
    donatedItems: List[DonatedItem] = Field(..., min_items=1)

class DonationHistoryResponse(BaseModel):
    donationId: str
    donationRequestId: str
    donorId: str
    donatedItems: List[DonatedItem]
    createdAt: datetime