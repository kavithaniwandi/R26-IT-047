"""
app/routers/donors.py
---------------------
Donor registry & donation-history endpoints powered by MongoDB Atlas.
Aggregates verified donation records across all disaster requests.
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import disaster_requests_collection

router = APIRouter(prefix="/donors", tags=["Donors (MongoDB)"])


class DonorHistoryEntry(BaseModel):
    requestId: str
    disasterType: Optional[str] = None
    reliefCamp: Optional[str] = None
    dsArea: Optional[str] = None
    gnDivision: Optional[str] = None
    donationId: str
    itemId: Optional[str] = None
    itemName: str
    quantity: float
    status: str
    donatedAt: Optional[datetime] = None
    acceptedAt: Optional[datetime] = None


class DonorSummary(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    total_donated: float
    requests_supported: int
    fulfilled_count: int
    status: str


class DonorDetail(DonorSummary):
    history: List[DonorHistoryEntry]


async def _aggregate_donors() -> list[dict]:
    """Iterate disaster requests and collapse embedded donations by donor."""
    donors: dict[str, dict] = {}
    cursor = disaster_requests_collection.find()
    docs = await cursor.to_list(length=200)

    for doc in docs:
        req_id = str(doc["_id"])
        for don in doc.get("donations", []):
            donor_id = don.get("donorId") or "unknown"
            if donor_id not in donors:
                donors[donor_id] = {
                    "id": str(donor_id),
                    "name": don.get("donorName", "Verified Donor"),
                    "email": don.get("donorEmail"),
                    "phone": don.get("donorPhone"),
                    "total_donated": 0.0,
                    "requests_supported": 0,
                    "fulfilled_count": 0,
                    "history": [],
                }
            entry = DonorHistoryEntry(
                requestId=req_id,
                disasterType=doc.get("disasterType"),
                reliefCamp=doc.get("reliefCamp"),
                dsArea=don.get("dsArea") or doc.get("dsArea"),
                gnDivision=doc.get("gnDivision"),
                donationId=don.get("donationId") or don.get("_id", ""),
                itemId=don.get("itemId"),
                itemName=don.get("itemName", "Relief Supply"),
                quantity=float(don.get("quantity", 0)),
                status=don.get("status", "pledged"),
                donatedAt=don.get("donatedAt"),
                acceptedAt=don.get("acceptedAt"),
            )
            d = donors[donor_id]
            d["history"].append(entry)
            d["total_donated"] += entry.quantity
            d["requests_supported"] += 1
            if entry.status == "received":
                d["fulfilled_count"] += 1

    return list(donors.values())


@router.get("", response_model=List[DonorSummary])
async def list_donors():
    donor_list = await _aggregate_donors()
    donor_list.sort(key=lambda d: d["total_donated"], reverse=True)
    return [
        DonorSummary(
            id=d["id"],
            name=d["name"],
            email=d["email"],
            phone=d["phone"],
            total_donated=round(d["total_donated"], 2),
            requests_supported=d["requests_supported"],
            fulfilled_count=d["fulfilled_count"],
            status="active",
        )
        for d in donor_list
    ]


@router.get("/{donor_id}", response_model=DonorDetail)
async def get_donor_detail(donor_id: str):
    donor_list = await _aggregate_donors()
    for d in donor_list:
        if d["id"] == donor_id:
            d["history"].sort(key=lambda e: (e.donatedAt or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
            return DonorDetail(
                id=d["id"],
                name=d["name"],
                email=d["email"],
                phone=d["phone"],
                total_donated=round(d["total_donated"], 2),
                requests_supported=d["requests_supported"],
                fulfilled_count=d["fulfilled_count"],
                status="active",
                history=d["history"],
            )
    raise HTTPException(status_code=404, detail="Donor not found")
