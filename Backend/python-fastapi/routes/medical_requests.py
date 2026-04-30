from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from database import get_collection
from models.medical_request import MedicalRequestIn, MedicalRequestUpdate

router = APIRouter()


def serialize(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-serializable dict."""
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


def valid_object_id(id: str):
    """Validate and return ObjectId, raise 422 if invalid."""
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=422, detail=f"Invalid ID format: {id}")


# ── POST /api/medical-requests ────────────────────────────────────────────────
# Called by frontend syncService.js whenever connection is restored
@router.post("/", status_code=201)
async def create_request(payload: MedicalRequestIn):
    col = get_collection("medical_requests")

    # Duplicate guard — if same localId + timestamp already exists, skip insert
    if payload.localId is not None and payload.timestamp:
        existing = await col.find_one({
            "localId":   payload.localId,
            "timestamp": payload.timestamp,
        })
        if existing:
            return {
                "message":   "Already synced",
                "data":      serialize(existing),
                "duplicate": True,
            }

    record = payload.model_dump()
    record["receivedAt"] = datetime.utcnow()

    result = await col.insert_one(record)
    saved  = await col.find_one({"_id": result.inserted_id})

    return {"message": "Request saved", "data": serialize(saved)}


# ── POST /api/medical-requests/bulk ──────────────────────────────────────────
# Sync multiple offline requests in one call (batch sync from frontend)
@router.post("/bulk", status_code=201)
async def bulk_create_requests(payload: list[MedicalRequestIn]):
    col = get_collection("medical_requests")

    results   = []
    skipped   = 0
    inserted  = 0

    for item in payload:
        # Duplicate check per item
        if item.localId is not None and item.timestamp:
            existing = await col.find_one({
                "localId":   item.localId,
                "timestamp": item.timestamp,
            })
            if existing:
                skipped += 1
                continue

        record = item.model_dump()
        record["receivedAt"] = datetime.utcnow()
        result = await col.insert_one(record)
        saved  = await col.find_one({"_id": result.inserted_id})
        results.append(serialize(saved))
        inserted += 1

    return {
        "message":  f"{inserted} saved, {skipped} skipped (duplicates)",
        "inserted": inserted,
        "skipped":  skipped,
        "data":     results,
    }


# ── GET /api/medical-requests ─────────────────────────────────────────────────
# List all requests — supports filtering by syncStatus and pagination
@router.get("/")
async def get_requests(
    status: str = Query(None,  description="Filter by syncStatus: pending | synced | failed"),
    limit:  int = Query(50,    ge=1, le=200),
    page:   int = Query(1,     ge=1),
):
    col    = get_collection("medical_requests")
    filter = {"syncStatus": status} if status else {}
    skip   = (page - 1) * limit

    cursor   = col.find(filter).sort("receivedAt", -1).skip(skip).limit(limit)
    requests = [serialize(doc) async for doc in cursor]
    total    = await col.count_documents(filter)

    return {
        "data":  requests,
        "total": total,
        "page":  page,
        "limit": limit,
        "pages": -(-total // limit),   # ceiling division
    }


# ── GET /api/medical-requests/{id} ───────────────────────────────────────────
@router.get("/{id}")
async def get_request(id: str):
    col = get_collection("medical_requests")
    doc = await col.find_one({"_id": valid_object_id(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"data": serialize(doc)}


# ── PATCH /api/medical-requests/{id} ─────────────────────────────────────────
@router.patch("/{id}")
async def update_request(id: str, payload: MedicalRequestUpdate):
    col = get_collection("medical_requests")

    # Only update fields that were actually provided
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    result = await col.find_one_and_update(
        {"_id": valid_object_id(id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")

    return {"message": "Updated", "data": serialize(result)}


# ── DELETE /api/medical-requests/{id} ────────────────────────────────────────
@router.delete("/{id}", status_code=200)
async def delete_request(id: str):
    col    = get_collection("medical_requests")
    result = await col.delete_one({"_id": valid_object_id(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Deleted successfully"}