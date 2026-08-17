from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class DonationItem(BaseModel):
    itemName: str = Field(..., min_length=2)
    unit: str = Field(...)
    quantity: float = Field(..., gt=0)
    donated: float = Field(default=0.0, ge=0)
    remaining: Optional[float] = None
    status: Literal["remaining", "fulfilled"] = "remaining"

class DonationRequestCreate(BaseModel):
    disasterType: Literal["Flood", "Landslide"]
    severity: Literal["Low", "Moderate", "High", "Critical"]
    dsArea: str = Field(..., min_length=2)
    gnDivision: str = Field(..., min_length=2)
    population: int = Field(..., ge=0)
    status: Literal["remaining", "fulfilled"] = "remaining"
    items: List[DonationItem] = Field(..., min_items=1)

class DonationRequestUpdateStatus(BaseModel):
    status: Optional[Literal["remaining", "fulfilled"]] = None
    items: Optional[List[DonationItem]] = None

class DonationRequestResponse(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    population: int
    status: str
    items: List[DonationItem]
    createdBy: str
    createdAt: datetime