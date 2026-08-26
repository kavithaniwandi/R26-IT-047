"""
app/schemas/victim.py
---------------------
Pydantic v2 validation schemas for disaster victim registration, demographic triage,
and medical camp assignments.
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class VictimCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, examples=["Nimal Karunaratne"])
    phone: str = Field(..., min_length=7, max_length=25, examples=["+94771234567"])
    alternate_phone: str | None = Field(None, max_length=25)
    nic: str | None = Field(None, max_length=30, examples=["198812345678"])
    gender: str | None = Field(None, examples=["male", "female", "other"])
    age: int | None = Field(None, ge=0, le=130, examples=[42])
    
    district: str = Field("Colombo", max_length=100, examples=["Colombo"])
    ds_division: str | None = Field("Kaduwela", max_length=100)
    gn_division: str | None = Field("Ranala", max_length=100)
    current_address: str | None = Field(None, max_length=500, examples=["45 River View Lane, Ranala, Kaduwela"])
    latitude: float = Field(6.9271, ge=-90.0, le=90.0)
    longitude: float = Field(79.8612, ge=-180.0, le=180.0)

    family_members_count: int = Field(1, ge=1, le=100)
    children_count: int = Field(0, ge=0, le=50)
    elderly_count: int = Field(0, ge=0, le=50)
    disabled_count: int = Field(0, ge=0, le=50)
    pregnant_lactating_count: int = Field(0, ge=0, le=20)

    evacuation_status: str = Field(
        "trapped_in_house",
        description="trapped_in_house | safe_at_home | isolated_roof_level | evacuated_to_camp | displaced_with_relatives"
    )
    assigned_camp_id: int | None = None
    chronic_diseases: str | None = Field(None, examples=["Type 2 Diabetes, Hypertension"])
    immediate_medical_needs: str | None = Field(None, examples=["Insulin vials, Asthma inhaler, sterile bandages"])
    dietary_and_relief_needs: str | None = Field(None, examples=["Clean drinking water, baby milk formula, dry rations"])
    registered_via: str = Field("web_portal", description="web_portal | sms_gateway | volunteer_app | camp_intake")
    notes: str | None = None


class VictimUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    nic: str | None = None
    gender: str | None = None
    age: int | None = None
    district: str | None = None
    ds_division: str | None = None
    gn_division: str | None = None
    current_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    family_members_count: int | None = None
    children_count: int | None = None
    elderly_count: int | None = None
    disabled_count: int | None = None
    pregnant_lactating_count: int | None = None
    evacuation_status: str | None = None
    assigned_camp_id: int | None = None
    chronic_diseases: str | None = None
    immediate_medical_needs: str | None = None
    dietary_and_relief_needs: str | None = None
    is_verified: bool | None = None
    notes: str | None = None


class VictimAssignCampRequest(BaseModel):
    camp_id: int = Field(..., description="Target Medical Camp ID")


class VictimOut(BaseModel):
    id: int
    user_id: int | None
    nic: str | None
    full_name: str
    phone: str
    alternate_phone: str | None
    gender: str | None
    age: int | None
    district: str
    ds_division: str | None
    gn_division: str | None
    current_address: str | None
    latitude: float
    longitude: float
    family_members_count: int
    children_count: int
    elderly_count: int
    disabled_count: int
    pregnant_lactating_count: int
    evacuation_status: str
    assigned_camp_id: int | None
    assigned_camp_name: str | None = None
    chronic_diseases: str | None
    immediate_medical_needs: str | None
    dietary_and_relief_needs: str | None
    vulnerability_score: float
    registered_via: str
    is_verified: bool
    notes: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class VictimStatsOut(BaseModel):
    total_victims: int
    total_family_members_affected: int
    total_children: int
    total_elderly: int
    total_disabled: int
    total_pregnant_lactating: int
    high_vulnerability_count: int
    evacuated_to_camp_count: int
    trapped_count: int
    by_district: dict[str, int]
    by_evacuation_status: dict[str, int]
