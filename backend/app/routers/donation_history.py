from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import TokenPayload, require_role
from app.database import disaster_requests_collection
from app.services.pledge_expiry import expire_stale_pledges


router = APIRouter(prefix="/donation-history", tags=["Donation History (MongoDB)"])


@router.get("")
async def get_donation_history(
    user: TokenPayload = Depends(
        require_role(["admin", "donor", "authority", "disaster_officer"])
    ),
):
    await expire_stale_pledges()
    query = {"donations.donorId": user.sub} if user.role == "donor" else {}
    documents = await disaster_requests_collection.find(query).sort("createdAt", -1).to_list(length=200)
    records = []
    for document in documents:
        for donation in document.get("donations", []):
            if user.role == "donor" and str(donation.get("donorId")) != user.sub:
                continue
            records.append({
                "donationId": donation.get("donationId"),
                "pledgeBatchId": donation.get("pledgeBatchId"),
                "requestId": str(document["_id"]),
                "disasterType": document.get("disasterType"),
                "dsArea": document.get("dsArea"),
                "gnDivision": document.get("gnDivision"),
                "reliefCamp": document.get("reliefCamp"),
                "donorId": donation.get("donorId"),
                "donorName": donation.get("donorName"),
                "itemName": donation.get("itemName"),
                "quantity": donation.get("quantity"),
                "unit": donation.get("unit", "units"),
                "status": donation.get("status"),
                "donatedAt": donation.get("donatedAt"),
                "expiresAt": donation.get("expiresAt"),
                "acceptedAt": donation.get("acceptedAt"),
                "cancelledAt": donation.get("cancelledAt"),
                "cancellationReason": donation.get("cancellationReason"),
            })
    return records
