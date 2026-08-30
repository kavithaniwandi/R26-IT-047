from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, timezone
import math

from app.models.relief_camp import (
    ReliefCampCreate,
    ReliefCampUpdate,
    ReliefCampResponse,
    AssignVolunteersPayload,
    PopulationPredictionRequest,
    PopulationPredictionResponse,
    HourlyLogEntry,
)
from app.my_database import relief_camp_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/relief-camps", tags=["Relief Camps"])


def format_camp(doc) -> ReliefCampResponse:
    history = [
        HourlyLogEntry(
            timestamp=h.get("timestamp", datetime.now(timezone.utc)),
            population=h.get("population", 0),
            predictedPopulation=h.get("predictedPopulation", 0),
            rainfall=h.get("rainfall", 0.0)
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
    camp: ReliefCampCreate, current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
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
    camps: List[ReliefCampCreate], current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
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
    current_user: dict = Depends(get_current_user),
):
    query = {}
    if current_user["userType"] == "volunteer":
        query["assignedVolunteerIds"] = current_user["userId"]

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
    current_user: dict = Depends(get_current_user),
):
    if current_user["userType"] != "admin":
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
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    camp = await relief_camp_collection.find_one({"_id": ObjectId(camp_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Relief camp not found")

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

    if payload.maxCapacityPersons is not None and current_user["userType"] == "admin":
        update_set["maxCapacityPersons"] = payload.maxCapacityPersons

    log_entry = {
        "timestamp": now,
        "population": cur_pop,
        "predictedPopulation": pred_pop,
        "rainfall": 0.0
    }

    updated = await relief_camp_collection.find_one_and_update(
        {"_id": ObjectId(camp_id)},
        {
            "$set": update_set,
            "$push": {"hourlyHistory": {"$each": [log_entry], "$slice": -24}}
        },
        return_document=True,
    )
    return format_camp(updated)


# 6. DELETE Relief Camp (Admin Only)
@router.delete("/{camp_id}", status_code=status.HTTP_200_OK)
async def delete_relief_camp(
    camp_id: str, current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
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
async def predict_population_progression(req: PopulationPredictionRequest):
    K = req.maxCapacity
    P0 = max(1, req.currentPopulation)

    rates = {"Low": 0.12, "Moderate": 0.22, "High": 0.35, "Critical": 0.50}
    k = rates.get(req.severity, 0.30)

    p_t = K / (1.0 + ((K - P0) / P0) * math.exp(-k * 1))
    next_pred = min(int(round(p_t)), K)
    delta = next_pred - P0
    occ = (next_pred / K) * 100 if K > 0 else 0

    projected_hourly = []
    for h in range(1, 7):
        val = K / (1.0 + ((K - P0) / P0) * math.exp(-k * h))
        val_int = min(int(round(val)), K)
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
        delta=delta,
        maxCapacity=K,
        occupancyPercent=round(occ, 1),
        projectedHourly=projected_hourly,
        note=note
    )


# 8. GET Relief Camp by ID
@router.get("/{camp_id}", response_model=ReliefCampResponse)
async def get_relief_camp_by_id(
    camp_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(camp_id):
        raise HTTPException(status_code=400, detail="Invalid Camp ID format")

    camp = await relief_camp_collection.find_one({"_id": ObjectId(camp_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Relief camp not found")

    if current_user["userType"] == "volunteer" and current_user["userId"] not in camp.get("assignedVolunteerIds", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this relief camp"
        )

    return format_camp(camp)
