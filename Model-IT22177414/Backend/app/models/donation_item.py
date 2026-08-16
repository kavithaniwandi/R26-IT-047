from pydantic import BaseModel, Field
from typing import Optional

class DonationItemCreate(BaseModel):
    item: str = Field(..., min_length=2, json_schema_extra={"example": "Rice"})
    quantityPerPerson: float = Field(..., gt=0, json_schema_extra={"example": 5.0})
    unit: str = Field(..., min_length=1, json_schema_extra={"example": "kg"})

class DonationItemResponse(BaseModel):
    itemId: str
    item: str
    quantityPerPerson: float
    unit: str