from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.my_database import disaster_donation_request_collection
from app.utils.security import get_current_user

router = APIRouter(prefix="/donation-history", tags=["Donation History"])


@router.get("", response_model=List[dict])
async def get_donor_donation_history(current_user: dict = Depends(get_current_user)):
    # Admins can view all donations; donors view only their own
    query = {}
    if current_user["userType"] == "donor":
        query = {"donations.donorId": current_user["userId"]}

    cursor = disaster_donation_request_collection.find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)

    history_records = []
    for doc in docs:
        for don in doc.get("donations", []):
            if (
                current_user["userType"] == "admin"
                or don.get("donorId") == current_user["userId"]
            ):
                history_records.append(
                    {
                        "donationId": don.get("donationId"),
                        "requestId": str(doc["_id"]),
                        "disasterType": doc.get("disasterType"),
                        "dsArea": doc.get("dsArea"),
                        "gnDivision": doc.get("gnDivision"),
                        "reliefCamp": doc.get("reliefCamp"),
                        "donorId": don.get("donorId"),
                        "donorName": don.get("donorName"),
                        "itemName": don.get("itemName"),
                        "quantity": don.get("quantity"),
                        "status": don.get("status"),
                        "donatedAt": don.get("donatedAt"),
                        "acceptedAt": don.get("acceptedAt"),
                    }
                )

    return history_records
