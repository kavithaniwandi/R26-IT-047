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
from app.services.camp_population_service import (
    predict_camp_population_rf,
    fetch_live_kelani_environment,
    SRI_LANKA_TZ,
)

router = APIRouter(prefix="/relief-camps", tags=["Relief Camps"])


def volunteer_identity_ids(current_user: TokenPayload, db: Optional[Session]) -> List[str]:
    """Return all legacy SQL IDs sharing the logged-in volunteer's email."""
    if not current_user.sub.isdigit() or db is None:
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
        # Predicted demand is preserved as real ML demand and NOT capped at maxCapacityPersons
        pred_pop = max(0, int(payload.predictedPopulation))
        update_set["predictedPopulation"] = pred_pop

    if payload.maxCapacityPersons is not None and current_user.role == "admin":
        update_set["maxCapacityPersons"] = payload.maxCapacityPersons

    if payload.currentPopulation is not None:
        # Check existing hourly observations to avoid creating duplicate observations for the same hour
        existing_history = [dict(h) for h in camp.get("hourlyHistory", [])]
        current_hour_key = now.astimezone(SRI_LANKA_TZ).strftime("%Y-%m-%d %H")

        matched_index = None
        for idx, entry in enumerate(existing_history):
            e_ts = entry.get("timestamp")
            if e_ts:
                if isinstance(e_ts, str):
                    try:
                        e_ts = datetime.fromisoformat(e_ts.replace("Z", "+00:00"))
                    except Exception:
                        continue
                if e_ts.tzinfo is None:
                    e_ts = e_ts.replace(tzinfo=timezone.utc)
                if e_ts.astimezone(SRI_LANKA_TZ).strftime("%Y-%m-%d %H") == current_hour_key:
                    matched_index = idx
                    break

        new_log_entry = {
            "timestamp": now,
            "population": cur_pop,
            "predictedPopulation": pred_pop,
            "rainfall": 0.0,
            "source": payload.observationSource or "manual",
        }

        if matched_index is not None:
            # Update/replace the existing hourly observation
            existing_history[matched_index] = new_log_entry
        else:
            existing_history.append(new_log_entry)
            if len(existing_history) > 24:
                existing_history = existing_history[-24:]

        update_set["hourlyHistory"] = existing_history

    update_operation = {"$set": update_set}

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


def extract_hourly_observations_from_camp(camp: dict) -> Tuple[List[int], List[datetime]]:
    """
    Extract up to 5 latest distinct hourly observations from camp's hourlyHistory in chronological order.
    Avoids duplicate observations within the same hour bucket.
    """
    history = camp.get("hourlyHistory", [])
    if not history:
        return [], []

    valid_entries = []
    for entry in history:
        pop = entry.get("population")
        ts = entry.get("timestamp")
        if pop is not None and isinstance(pop, (int, float)) and pop >= 0:
            if ts:
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                valid_entries.append({"timestamp": ts, "population": int(pop), "source": entry.get("source")})

    # Group by Sri Lanka local hour bucket
    entries_by_hour = {}
    for entry in sorted(valid_entries, key=lambda x: x["timestamp"], reverse=True):
        ts = entry["timestamp"]
        hour_key = ts.astimezone(SRI_LANKA_TZ).strftime("%Y-%m-%d %H")
        if hour_key not in entries_by_hour:
            entries_by_hour[hour_key] = entry

    # Take latest 5 and sort chronologically (oldest to newest: Hour 1 to Hour 5)
    latest_entries = list(entries_by_hour.values())[:5]
    latest_entries.sort(key=lambda x: x["timestamp"])

    populations = [e["population"] for e in latest_entries]
    timestamps = [e["timestamp"] for e in latest_entries]
    return populations, timestamps


# 7. POPULATION PREDICTION MODEL (Random Forest Regressor)
@router.post("/predict-population", response_model=PopulationPredictionResponse)
async def predict_population_progression(
    req: PopulationPredictionRequest,
    _current_user: TokenPayload = Depends(require_role(["admin", "volunteer", "disaster_officer"])),
):
    camp = None
    if req.campId:
        if not ObjectId.is_valid(req.campId):
            raise HTTPException(status_code=400, detail="Invalid Camp ID format")
        camp = await relief_camp_collection.find_one({"_id": ObjectId(req.campId)})
        if not camp:
            raise HTTPException(status_code=404, detail="Relief camp not found")

    # Determine maximum capacity
    if camp:
        max_capacity = int(camp.get("maxCapacityPersons", 0) or 0)
    else:
        max_capacity = req.maxCapacity or 0

    if max_capacity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Relief camp maximum capacity must be greater than zero; got {max_capacity}",
        )

    # Determine 5 hourly observations
    hourly_obs: List[int] = []
    hourly_timestamps: Optional[List[datetime]] = None

    if camp:
        camp_obs, camp_ts = extract_hourly_observations_from_camp(camp)
        if len(camp_obs) >= 5:
            hourly_obs = camp_obs
            hourly_timestamps = camp_ts

    if len(hourly_obs) < 5 and req.popHistory and len(req.popHistory) >= 5:
        raw_list = [int(v) for v in req.popHistory]
        # If passed in reverse order (newest first, e.g. raw_list[0] == req.currentPopulation and raw_list[-1] != req.currentPopulation)
        if req.currentPopulation is not None and raw_list[0] == req.currentPopulation and raw_list[-1] != req.currentPopulation:
            hourly_obs = list(reversed(raw_list[:5]))
        else:
            hourly_obs = raw_list[-5:]

    if len(hourly_obs) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Five real hourly population observations are required for forecasting",
        )

    for val in hourly_obs:
        if val < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Observed hourly population count cannot be negative; got {val}",
            )

    # Retrieve live environmental data using existing telemetry
    live_env = await fetch_live_kelani_environment()
    live_weather = live_env.get("weather", {})
    live_river = live_env.get("river", {})
    live_rain_hist = live_env.get("rainHistory", [])

    # 1. rainfall_mm
    if req.rainfallMm is not None:
        rainfall_mm = float(req.rainfallMm)
    elif req.rainHistory and len(req.rainHistory) > 0:
        rainfall_mm = float(req.rainHistory[0])
    elif live_weather.get("available") and live_weather.get("precipitationMm") is not None:
        rainfall_mm = float(live_weather["precipitationMm"])
    else:
        rainfall_mm = 0.0

    # 2. rainfall_3h_avg_mm
    if req.rainfall3hAvgMm is not None:
        rainfall_3h_avg_mm = float(req.rainfall3hAvgMm)
    elif req.rainHistory and len(req.rainHistory) >= 1:
        rainfall_3h_avg_mm = float(sum(req.rainHistory[:3]) / len(req.rainHistory[:3]))
    elif live_rain_hist and len(live_rain_hist) >= 1:
        rainfall_3h_avg_mm = float(sum(live_rain_hist[:3]) / len(live_rain_hist[:3]))
    elif live_weather.get("available") and live_weather.get("precipitationMm") is not None:
        rainfall_3h_avg_mm = float(live_weather["precipitationMm"])
    else:
        rainfall_3h_avg_mm = 0.0

    # 3. temperature_c
    if req.temperatureC is not None:
        temperature_c = float(req.temperatureC)
    elif live_weather.get("available") and live_weather.get("temperatureC") is not None:
        temperature_c = float(live_weather["temperatureC"])
    else:
        temperature_c = 27.5

    # 4. humidity_pct
    if req.humidityPercent is not None:
        humidity_pct = float(req.humidityPercent)
    elif live_weather.get("available") and live_weather.get("humidityPercent") is not None:
        humidity_pct = float(live_weather["humidityPercent"])
    else:
        humidity_pct = 80.0

    # 5. river_level_m
    if req.riverLevel is not None:
        river_level_m = float(req.riverLevel)
    elif live_river.get("available") and live_river.get("levelM") is not None:
        river_level_m = float(live_river["levelM"])
    else:
        river_level_m = 5.0

    # 6. river_level_change_m
    if req.riverLevelChangeM is not None:
        river_level_change_m = float(req.riverLevelChangeM)
    elif live_river.get("available") and live_river.get("rateOfRiseMPerHour") is not None:
        river_level_change_m = float(live_river["rateOfRiseMPerHour"])
    else:
        river_level_change_m = 0.0

    # 7. hour_of_day
    if req.hourOfDay is not None:
        hour_of_day = int(req.hourOfDay)
    elif hourly_timestamps and len(hourly_timestamps) >= 5:
        hour_of_day = hourly_timestamps[-1].astimezone(SRI_LANKA_TZ).hour
    else:
        hour_of_day = datetime.now(SRI_LANKA_TZ).hour

    try:
        pred_res = predict_camp_population_rf(
            max_capacity=max_capacity,
            hourly_observations=hourly_obs,
            rainfall_mm=rainfall_mm,
            rainfall_3h_avg_mm=rainfall_3h_avg_mm,
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            river_level_m=river_level_m,
            river_level_change_m=river_level_change_m,
            hour_of_day=hour_of_day,
            observation_timestamps=hourly_timestamps,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference engine failure: {exc}",
        ) from exc

    # Persist prediction metadata to MongoDB camp doc if camp was identified
    if camp:
        pred_meta = {
            "campId": str(camp["_id"]),
            "predictionGeneratedAt": pred_res["predictionGeneratedAt"],
            "forecastFor": pred_res["forecastFor"],
            "predictedPopulation": pred_res["predictedPopulation"],
            "maxCapacity": max_capacity,
            "expectedSheltered": pred_res["expectedSheltered"],
            "overflow": pred_res["overflow"],
            "status": pred_res["status"],
            "modelVersion": pred_res["modelMetadata"]["version"],
            "modelName": pred_res["modelMetadata"]["modelName"],
            "featuresUsed": pred_res["factors"],
        }
        await relief_camp_collection.update_one(
            {"_id": camp["_id"]},
            {
                "$set": {
                    "predictedPopulation": pred_res["predictedPopulation"],
                    "latestPrediction": pred_meta,
                    "lastUpdated": datetime.now(timezone.utc),
                },
                "$push": {
                    "predictionHistory": {"$each": [pred_meta], "$slice": -24}
                }
            }
        )

    return PopulationPredictionResponse(**pred_res)


@router.post("/{camp_id}/predict-population", response_model=PopulationPredictionResponse)
async def predict_camp_population_by_id(
    camp_id: str,
    req: Optional[PopulationPredictionRequest] = None,
    _current_user: TokenPayload = Depends(require_role(["admin", "volunteer", "disaster_officer"])),
):
    if req is None:
        req = PopulationPredictionRequest()
    req.campId = camp_id
    return await predict_population_progression(req, _current_user=_current_user)


@router.get("/environment/kelani")
async def get_kelani_environment(
    _current_user: TokenPayload = Depends(
        require_role(["admin", "volunteer", "disaster_officer"])
    ),
):
    """Return Kaduwela weather and the nearby Hanwella Kelani gauge snapshot."""
    return await fetch_live_kelani_environment()


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
