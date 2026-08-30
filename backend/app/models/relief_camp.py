from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class HourlyLogEntry(BaseModel):
    timestamp: datetime
    population: int
    predictedPopulation: int
    rainfall: Optional[float] = 0.0

class ReliefCampCreate(BaseModel):
    dsArea: str = Field(..., min_length=2, json_schema_extra={"example": "Kaduwela"})
    gnDivision: str = Field(..., min_length=2, json_schema_extra={"example": "Boralugoda"})
    name: str = Field(..., min_length=2, json_schema_extra={"example": "Sri Maha Viharaya Pore"})
    maxCapacityPersons: int = Field(..., gt=0, json_schema_extra={"example": 50})
    maxFamilies: Optional[int] = Field(default=0, ge=0)
    currentPopulation: int = Field(default=0, ge=0)
    predictedPopulation: int = Field(default=0, ge=0)
    assignedVolunteerIds: List[str] = Field(default_factory=list)

class ReliefCampUpdate(BaseModel):
    currentPopulation: Optional[int] = Field(default=None, ge=0)
    predictedPopulation: Optional[int] = Field(default=None, ge=0)
    maxCapacityPersons: Optional[int] = Field(default=None, gt=0)
    name: Optional[str] = None
    assignedVolunteerIds: Optional[List[str]] = None

class AssignVolunteersPayload(BaseModel):
    volunteerIds: List[str]

class ReliefCampResponse(BaseModel):
    id: str
    dsArea: str
    gnDivision: str
    name: str
    maxCapacityPersons: int
    maxFamilies: int
    currentPopulation: int
    predictedPopulation: int
    assignedVolunteerIds: List[str] = Field(default_factory=list)
    hourlyHistory: List[HourlyLogEntry] = Field(default_factory=list)
    lastUpdated: datetime

class PopulationPredictionRequest(BaseModel):
    currentPopulation: int = Field(..., ge=0)
    maxCapacity: int = Field(..., gt=0)
    popHistory: Optional[List[int]] = Field(default_factory=list)
    rainHistory: Optional[List[float]] = Field(default_factory=list)
    riverLevel: Optional[float] = 5.0
    hourOfDay: Optional[int] = 12
    severity: Optional[str] = "High"

class PopulationPredictionResponse(BaseModel):
    predictedPopulation: int
    delta: int
    maxCapacity: int
    occupancyPercent: float
    projectedHourly: List[dict]
    note: str
