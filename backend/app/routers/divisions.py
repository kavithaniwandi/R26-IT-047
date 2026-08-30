from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List

from app.models.division import DSDivisionCreate, DSDivisionResponse, AddGNDivision
from app.my_database import division_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/divisions", tags=["Administrative Divisions"])

def format_division(doc) -> DSDivisionResponse:
    return DSDivisionResponse(
        id=str(doc["_id"]),
        dsArea=doc["dsArea"],
        gnDivisions=doc.get("gnDivisions", [])
    )

# 1. CREATE or Replace a DS Area with its GN Divisions (Admin Only)
@router.post("", response_model=DSDivisionResponse, status_code=status.HTTP_201_CREATED)
async def create_ds_division(
    data: DSDivisionCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage divisions")

    existing = await division_collection.find_one({"dsArea": data.dsArea})
    if existing:
        raise HTTPException(status_code=400, detail=f"DS Area '{data.dsArea}' already exists")

    doc = data.model_dump()
    result = await division_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return format_division(doc)

# 2. BULK CREATE DS Areas (Admin Only)
@router.post("/bulk", response_model=List[DSDivisionResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_ds_divisions(
    data: List[DSDivisionCreate],
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage divisions")

    inserted = []
    for item in data:
        doc = item.model_dump()
        await division_collection.update_one(
            {"dsArea": item.dsArea},
            {"$set": doc},
            upsert=True
        )
        updated = await division_collection.find_one({"dsArea": item.dsArea})
        inserted.append(format_division(updated))
    return inserted

# 3. GET All DS Areas (Returns list of all DS names)
@router.get("/ds-areas", response_model=List[str])
async def get_all_ds_areas():
    cursor = division_collection.find({}, {"dsArea": 1, "_id": 0})
    docs = await cursor.to_list(length=100)
    return [doc["dsArea"] for doc in docs]

# 4. GET GN Divisions for a Specific DS Area
@router.get("/{ds_area}/gn-divisions", response_model=List[str])
async def get_gn_divisions_by_ds_area(ds_area: str):
    doc = await division_collection.find_one({"dsArea": ds_area})
    if not doc:
        raise HTTPException(status_code=404, detail=f"DS Area '{ds_area}' not found")
    return doc.get("gnDivisions", [])

# 5. GET All Divisions with Full Details
@router.get("", response_model=List[DSDivisionResponse])
async def get_all_divisions():
    cursor = division_collection.find()
    docs = await cursor.to_list(length=100)
    return [format_division(doc) for doc in docs]

# 6. APPEND a GN Division to an Existing DS Area (Admin Only)
@router.post("/{ds_area}/gn-divisions", response_model=DSDivisionResponse)
async def add_gn_division_to_ds_area(
    ds_area: str,
    payload: AddGNDivision,
    current_user: dict = Depends(get_current_user)
):
    if current_user["userType"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage divisions")

    result = await division_collection.find_one_and_update(
        {"dsArea": ds_area},
        {"$addToSet": {"gnDivisions": payload.gnDivision}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"DS Area '{ds_area}' not found")
    return format_division(result)
