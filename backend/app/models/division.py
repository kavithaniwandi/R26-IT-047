from pydantic import BaseModel, Field
from typing import List

class DSDivisionCreate(BaseModel):
    dsArea: str = Field(..., min_length=2, json_schema_extra={"example": "Kaduwela"})
    gnDivisions: List[str] = Field(..., min_items=1, json_schema_extra={"example": ["469 Ranala", "470 Nawagamuwa"]})

class DSDivisionResponse(BaseModel):
    id: str
    dsArea: str
    gnDivisions: List[str]

class AddGNDivision(BaseModel):
    gnDivision: str = Field(..., min_length=2, json_schema_extra={"example": "471 Ihala Bomiriya"})
