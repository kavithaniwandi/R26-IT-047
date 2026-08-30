from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class RequestItem(BaseModel):
    itemId: Optional[str] = None
    itemName: str = Field(..., min_length=2)
    unit: str = Field(...)
    neededQuantity: float = Field(..., gt=0)
    pledgedQuantity: float = Field(default=0.0, ge=0)
    donatedQuantity: float = Field(default=0.0, ge=0)
    remainingQuantity: Optional[float] = None
    status: Literal["remaining", "fulfilled"] = "remaining"

class DonationEntry(BaseModel):
    donationId: str
    donorId: str
    donorName: str
    donorPhone: Optional[str] = None
    itemId: Optional[str] = None
    itemName: str
    quantity: float = Field(..., gt=0)
    dsArea: str
    status: Literal["pledged", "received"] = "pledged"
    donatedAt: datetime
    acceptedByOfficerId: Optional[str] = None
    acceptedAt: Optional[datetime] = None

class DisasterDonationRequestCreate(BaseModel):
    disasterType: Literal["Flood", "Landslide", "Tsunami", "Drought", "Fire", "Other"]
    severity: Literal["Low", "Moderate", "High", "Critical"]
    dsArea: str = Field(..., min_length=2)
    gnDivision: str = Field(..., min_length=2)
    reliefCamp: str = Field(..., min_length=2)
    people_count: int = Field(..., ge=0)
    items: List[RequestItem] = Field(..., min_items=1)

class PledgeItem(BaseModel):
    itemName: str
    quantity: float = Field(..., gt=0)
    itemId: Optional[str] = None

class BatchPledgeCreate(BaseModel):
    pledges: List[PledgeItem] = Field(..., min_items=1)

class DisasterDonationRequestResponse(BaseModel):
    id: str
    disasterType: str
    severity: str
    dsArea: str
    gnDivision: str
    reliefCamp: str
    people_count: int
    status: str
    createdBy: str
    createdAt: datetime
    items: List[RequestItem]
    donations: List[DonationEntry]
