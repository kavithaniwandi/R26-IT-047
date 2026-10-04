from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import TokenPayload, require_role
from app.database import division_collection
from app.models.division import AddGNDivision, DSDivisionCreate, DSDivisionResponse


router = APIRouter(prefix="/divisions", tags=["Administrative Divisions (MongoDB)"])
READ_ROLES = ["admin", "volunteer", "donor", "authority", "disaster_officer"]


def _format(document: dict) -> DSDivisionResponse:
    return DSDivisionResponse(
        id=str(document["_id"]),
        dsArea=document["dsArea"],
        gnDivisions=document.get("gnDivisions", []),
    )


@router.post("", response_model=DSDivisionResponse, status_code=status.HTTP_201_CREATED)
async def create_division(
    payload: DSDivisionCreate,
    _user: TokenPayload = Depends(require_role(["admin"])),
):
    if await division_collection.find_one({"dsArea": payload.dsArea}):
        raise HTTPException(status_code=400, detail=f"DS Area '{payload.dsArea}' already exists")
    document = payload.model_dump()
    result = await division_collection.insert_one(document)
    document["_id"] = result.inserted_id
    return _format(document)


@router.post("/bulk", response_model=List[DSDivisionResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_divisions(
    payload: List[DSDivisionCreate],
    _user: TokenPayload = Depends(require_role(["admin"])),
):
    output = []
    for item in payload:
        await division_collection.update_one(
            {"dsArea": item.dsArea}, {"$set": item.model_dump()}, upsert=True
        )
        output.append(_format(await division_collection.find_one({"dsArea": item.dsArea})))
    return output


@router.get("/ds-areas", response_model=List[str])
async def list_ds_areas(
    _user: TokenPayload = Depends(require_role(READ_ROLES)),
):
    documents = await division_collection.find({}, {"dsArea": 1, "_id": 0}).to_list(length=200)
    return sorted(document["dsArea"] for document in documents)


@router.get("/{ds_area}/gn-divisions", response_model=List[str])
async def list_gn_divisions(
    ds_area: str,
    _user: TokenPayload = Depends(require_role(READ_ROLES)),
):
    document = await division_collection.find_one({"dsArea": ds_area})
    if not document:
        raise HTTPException(status_code=404, detail=f"DS Area '{ds_area}' not found")
    return document.get("gnDivisions", [])


@router.get("", response_model=List[DSDivisionResponse])
async def list_divisions(
    _user: TokenPayload = Depends(require_role(READ_ROLES)),
):
    documents = await division_collection.find().sort("dsArea", 1).to_list(length=200)
    return [_format(document) for document in documents]


@router.post("/{ds_area}/gn-divisions", response_model=DSDivisionResponse)
async def append_gn_division(
    ds_area: str,
    payload: AddGNDivision,
    _user: TokenPayload = Depends(require_role(["admin"])),
):
    document = await division_collection.find_one_and_update(
        {"dsArea": ds_area},
        {"$addToSet": {"gnDivisions": payload.gnDivision}},
        return_document=True,
    )
    if not document:
        raise HTTPException(status_code=404, detail=f"DS Area '{ds_area}' not found")
    return _format(document)
