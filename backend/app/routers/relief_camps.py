"""
app/routers/relief_camps.py
----------------------------
Relief Camps management (user's own module) backed by MongoDB Atlas.
"""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import math
import httpx
from sqlalchemy.orm import Session

from app.core.security import require_role, TokenPayload
from app.database import get_db, relief_camp_collection
from app.models.user import User
from app.models.relief_camp import (
    ReliefCampCreate,
    ReliefCampUpdate,
    ReliefCampResponse,
    AssignVolunteersPayload,
    PopulationPredictionRequest,
    PopulationPredictionResponse,
    HourlyLogEntry,
)

router = APIRouter(prefix="/relief-camps", tags=["Relief Camps"])


def volunteer_identity_ids(current_user: TokenPayload, db: Session) -> List[str]:
    """Return all legacy SQL IDs sharing the logged-in volunteer's email."""
    if not current_user.sub.isdigit():
        return [current_user.sub]

    user = db.query(User).filter(User.id == int(current_user.sub)).first()
    if not user:
        return [current_user.sub]

    # Scan the small user directory in Python instead of trusting the legacy
    # unique email index, which may hide duplicate rows in older seeded DBs.
    normalized_email = user.email.strip().lower()
    duplicate_accounts = db.query(User).all()
    return [
        str(account.id)
        for account in duplicate_accounts
        if account.email and account.email.strip().lower() == normalized_email
    ]


def can_manage_camp(current_user: TokenPayload, camp: dict, db: Session) -> bool:
    """Allow volunteers to manage camps assigned to any of their legacy account IDs."""
    if current_user.role != "volunteer":
        return True
    assigned_ids = {str(value) for value in camp.get("assignedVolunteerIds", [])}
    permitted_ids = set(volunteer_identity_ids(current_user, db))
    return not assigned_ids.isdisjoint(permitted_ids)


def format_camp(doc) -> ReliefCampResponse:
    history = [
        HourlyLogEntry(
            timestamp=h.get("timestamp", datetime.now(timezone.utc)),
            population=h.get("population", 0),
            predictedPopulation=h.get("predictedPopulation", 0),
            rainfall=h.get("rainfall", 0.0),
            source=h.get("source", "unknown"),
        )
        for h in doc.get("hourlyHistory", [])
    ]

    return ReliefCampResponse(
        id=str(doc["_id"]),
        dsArea=doc.get("dsArea", ""),
        gnDivision=doc.get("gnDivision", ""),
        name=doc.get("name", ""),
        maxCapacityPersons=int(doc.get("maxCapacityPersons", 100)),
        maxFamilies=int(doc.get("maxFamilies", 0)),
        currentPopulation=int(doc.get("currentPopulation", 0)),
        predictedPopulation=int(doc.get("predictedPopulation", doc.get("currentPopulation", 0))),
        assignedVolunteerIds=doc.get("assignedVolunteerIds", []),
        hourlyHistory=history,
        lastUpdated=doc.get("lastUpdated", datetime.now(timezone.utc)),
    )


# 1. CREATE Relief Camp (Admin Only)
@router.post("", response_model=ReliefCampResponse, status_code=status.HTTP_201_CREATED)
async def create_relief_camp(
    camp: ReliefCampCreate,
    current_user: TokenPayload = Depends(require_role(["admin"])),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add relief camps",
        )

    doc = camp.model_dump()
    doc["lastUpdated"] = datetime.now(timezone.utc)
    result = await relief_camp_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return format_camp(doc)


# 2. BULK CREATE Relief Camps (Admin Only)
@router.post(
    "/bulk",
    response_model=List[ReliefCampResponse],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_camps(
    camps: List[ReliefCampCreate],
    current_user: TokenPayload = Depends(require_role(["admin"])),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can bulk import relief camps",
        )

    docs = []
    for c in camps:
        d = c.model_dump()
        d["lastUpdated"] = datetime.now(timezone.utc)
        docs.append(d)

    result = await relief_camp_collection.insert_many(docs)
    for doc_id, doc in zip(result.inserted_ids, docs):
        doc["_id"] = doc_id

    return [format_camp(d) for d in docs]


# 3. GET All Relief Camps (Volunteers see only assigned; Admins/Officers see all)
@router.get("", response_model=List[ReliefCampResponse])
async def get_all_camps(
    dsArea: Optional[str] = None,
    gnDivision: Optional[str] = None,
    current_user: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer", "volunteer"])
    ),
    db: Session = Depends(get_db),
):
    query = {}
    if current_user.role == "volunteer":
        query["assignedVolunteerIds"] = {"$in": volunteer_identity_ids(current_user, db)}

    if dsArea:
        query["dsArea"] = dsArea
    if gnDivision:
        query["gnDivision"] = {"$regex": gnDivision, "$options": "i"}

    cursor = relief_camp_collection.find(query).sort("name", 1)
    docs = await cursor.to_list(length=300)
    return [format_camp(d) for d in docs]


# 4. ASSIGN Volunteers to a Camp (Admin Only)
@router.patch("/{camp_id}/assign-volunteers", response_model=ReliefCampResponse)
async def assign_volunteers_to_camp(
    camp_id: str,
    payload: AssignVolunteersPayload,
    current_user: TokenPayload = Depends(require_role(["admin"])),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign volunteers to relief camps",
        )

    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    updated = await relief_camp_collection.find_one_and_update(
        {"_id": ObjectId(camp_id)},
        {
            "$set": {
                "assignedVolunteerIds": payload.volunteerIds,
                "lastUpdated": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Relief camp not found")

    return format_camp(updated)


# 5. UPDATE Camp Population (Supports manual override and bounded predicted updates)
@router.patch("/{camp_id}/population", response_model=ReliefCampResponse)
async def update_camp_population(
    camp_id: str,
    payload: ReliefCampUpdate,
    current_user: TokenPayload = Depends(
        require_role(["admin", "disaster_officer", "volunteer"])
    ),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    camp = await relief_camp_collection.find_one({"_id": ObjectId(camp_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Relief camp not found")

    if not can_manage_camp(current_user, camp, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this relief camp",
        )

    now = datetime.now(timezone.utc)
    update_set = {"lastUpdated": now}

    cur_pop = camp.get("currentPopulation", 0)
    pred_pop = camp.get("predictedPopulation", cur_pop)

    if payload.currentPopulation is not None:
        cur_pop = payload.currentPopulation
        update_set["currentPopulation"] = cur_pop

    if payload.predictedPopulation is not None:
        max_cap = int(camp.get("maxCapacityPersons", 100))
        # Predicted count is strictly bounded by Max Capacity
        pred_pop = min(payload.predictedPopulation, max_cap)
        update_set["predictedPopulation"] = pred_pop

    if payload.maxCapacityPersons is not None and current_user.role == "admin":
        update_set["maxCapacityPersons"] = payload.maxCapacityPersons

    update_operation = {"$set": update_set}
    if payload.currentPopulation is not None:
        log_entry = {
            "timestamp": now,
            "population": cur_pop,
            "predictedPopulation": pred_pop,
            "rainfall": 0.0,
            "source": payload.observationSource or "manual",
        }
        update_operation["$push"] = {
            "hourlyHistory": {"$each": [log_entry], "$slice": -24}
        }

    updated = await relief_camp_collection.find_one_and_update(
        {"_id": ObjectId(camp_id)},
        update_operation,
        return_document=True,
    )
    return format_camp(updated)


# 6. DELETE Relief Camp (Admin Only)
@router.delete("/{camp_id}", status_code=status.HTTP_200_OK)
async def delete_relief_camp(
    camp_id: str,
    current_user: TokenPayload = Depends(require_role(["admin"])),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete relief camps",
        )

    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    res = await relief_camp_collection.delete_one({"_id": ObjectId(camp_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Relief camp not found")
    return {"message": "Relief camp deleted successfully"}


# 7. POPULATION PREDICTION MODEL
@router.post("/predict-population", response_model=PopulationPredictionResponse)
async def predict_population_progression(
    req: PopulationPredictionRequest,
    _current_user: TokenPayload = Depends(require_role(["admin", "volunteer", "disaster_officer"])),
):
    if len(req.popHistory or []) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Five real hourly population observations are required for forecasting",
        )
    K = req.maxCapacity
    P0 = max(1, req.currentPopulation)

    rates = {"Low": 0.12, "Moderate": 0.22, "High": 0.35, "Critical": 0.50}
    base_rate = rates.get(req.severity, 0.30)

    recent_population = [max(0, int(value)) for value in (req.popHistory or [])[:5]]
    population_deltas = [
        recent_population[index] - recent_population[index + 1]
        for index in range(len(recent_population) - 1)
    ]
    average_hourly_growth = (
        max(0.0, sum(population_deltas) / len(population_deltas))
        if population_deltas else 0.0
    )

    recent_rain = [max(0.0, float(value)) for value in (req.rainHistory or [])[:3]]
    average_recent_rain = sum(recent_rain) / len(recent_rain) if recent_rain else 0.0
    rain_pressure = min(average_recent_rain / 20.0, 1.5)

    river_level = max(0.0, float(req.riverLevel or 0.0))
    # Hanwella's official alert threshold is 7 m. Levels approaching or
    # exceeding it increase the expected shelter influx.
    river_pressure = min(max(0.0, river_level - 5.0) / 5.0, 1.5)
    weather_code = int(req.weatherCode or 0)
    weather_pressure = (
        0.08 if weather_code >= 95
        else 0.06 if weather_code >= 80
        else 0.04 if weather_code >= 51
        else 0.01 if weather_code in {45, 48}
        else 0.0
    )
    if req.humidityPercent is not None and req.humidityPercent >= 90:
        weather_pressure += 0.01
    k = base_rate + (rain_pressure * 0.12) + (river_pressure * 0.18) + weather_pressure

    p_t = K / (1.0 + ((K - P0) / P0) * math.exp(-k * 1))
    trend_adjustment = int(round(average_hourly_growth * 0.5))
    next_pred = min(max(P0, int(round(p_t)) + trend_adjustment), K)
    delta = next_pred - P0
    occ = (next_pred / K) * 100 if K > 0 else 0

    projected_hourly = []
    for h in range(1, 7):
        val = K / (1.0 + ((K - P0) / P0) * math.exp(-k * h))
        val_int = min(max(P0, int(round(val)) + trend_adjustment), K)
        projected_hourly.append({
            "hour": f"+{h}h",
            "estimatedPeople": val_int,
            "occupancyPercent": round((val_int / K) * 100, 1)
        })

    if occ >= 100:
        note = "Predicted population reaches 100% capacity limit. Direct excess arrivals to neighboring relief centers."
    elif occ >= 85:
        note = "Camp will be near full capacity within the next hours. Request additional ration supply units immediately."
    else:
        note = "Projected intake remains within manageable capacity bounds."

    return PopulationPredictionResponse(
        predictedPopulation=next_pred,
        forecastFor=datetime.now(timezone.utc) + timedelta(hours=1),
        delta=delta,
        maxCapacity=K,
        occupancyPercent=round(occ, 1),
        projectedHourly=projected_hourly,
        note=note,
        factors={
            "severity": req.severity,
            "averageHourlyGrowth": round(average_hourly_growth, 1),
            "recentRainfallMm": round(average_recent_rain, 1),
            "riverLevelM": round(river_level, 2),
            "temperatureC": req.temperatureC,
            "humidityPercent": req.humidityPercent,
            "weatherCode": req.weatherCode,
            "adjustedGrowthRate": round(k, 3),
        },
    )


@router.get("/environment/kelani")
async def get_kelani_environment(
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "disaster_officer"])
    ),
):
    """Return Kaduwela weather and the nearby Hanwella Kelani gauge snapshot."""
    weather_url = "https://api.open-meteo.com/v1/forecast"
    river_url = "https://slwaterlevel.mevinu.com/api/gauges/Hanwella"
    weather_params = {
        "latitude": 6.9344,
        "longitude": 79.9830,
        "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation,rain",
        "hourly": "precipitation",
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "Asia/Colombo",
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        weather_result, river_result = await asyncio.gather(
            client.get(weather_url, params=weather_params),
            client.get(river_url),
            return_exceptions=True,
        )

    weather = {"available": False}
    rain_history: List[float] = []
    if not isinstance(weather_result, Exception) and weather_result.is_success:
        payload = weather_result.json()
        current = payload.get("current", {})
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])
        current_time = current.get("time", "")
        current_hour = f"{current_time[:13]}:00" if current_time else ""
        current_index = max(
            (index for index, value in enumerate(times) if value <= current_hour),
            default=len(precipitation) - 1,
        )
        rain_history = [
            round(float(precipitation[index] or 0.0), 1)
            for index in range(current_index, max(-1, current_index - 7), -1)
        ]
        weather = {
            "available": True,
            "temperatureC": current.get("temperature_2m"),
            "humidityPercent": current.get("relative_humidity_2m"),
            "precipitationMm": current.get("precipitation", current.get("rain", 0.0)),
            "weatherCode": current.get("weather_code"),
            "observedAt": current_time,
            "source": "Open-Meteo",
        }

    river = {
        "available": False,
        "station": "Hanwella",
        "basin": "Kelani Ganga",
        "source": "Sri Lanka Flood Monitor / Irrigation telemetry",
    }
    if not isinstance(river_result, Exception) and river_result.is_success:
        payload = river_result.json()
        river.update({
            "available": True,
            "levelM": payload.get("water_level"),
            "status": payload.get("status"),
            "rateOfRiseMPerHour": payload.get("rate_of_rise"),
            "isRising": payload.get("is_rising"),
            "alertLevelM": payload.get("alertpull"),
            "observedAt": payload.get("last_updated_time"),
        })

    return {
        "location": "Kaduwela / Kelani River basin",
        "weather": weather,
        "rainHistory": rain_history,
        "river": river,
        "fetchedAt": datetime.now(timezone.utc),
    }


# 8. GET Relief Camp by ID
@router.get("/{camp_id}", response_model=ReliefCampResponse)
async def get_relief_camp_by_id(
    camp_id: str,
    current_user: TokenPayload = Depends(
        require_role(["admin", "authority", "disaster_officer", "volunteer"])
    ),
    db: Session = Depends(get_db),
):
    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    camp = await relief_camp_collection.find_one({"_id": ObjectId(camp_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Relief camp not found")

    if not can_manage_camp(current_user, camp, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this relief camp"
        )

    return format_camp(camp)
