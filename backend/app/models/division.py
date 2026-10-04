from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class DSDivisionCreate(BaseModel):
    dsArea: str = Field(..., min_length=2)
    gnDivisions: List[str] = Field(..., min_length=1)


class DSDivisionResponse(BaseModel):
    id: str
    dsArea: str
    gnDivisions: List[str]


class AddGNDivision(BaseModel):
    gnDivision: str = Field(..., min_length=2)
