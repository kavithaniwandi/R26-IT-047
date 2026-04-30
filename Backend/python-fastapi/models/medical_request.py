from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MedicalRequestIn(BaseModel):
    """
    Schema for data coming in from the frontend sync service.
    Mirrors the fields saved in IndexedDB on the frontend.
    """
    patientName: str
    type:        str
    notes:       Optional[str] = ""

    # Offline tracking fields sent from IndexedDB
    localId:    Optional[int]  = None   # IndexedDB autoIncrement id
    timestamp:  Optional[str]  = None   # ISO string — when saved offline
    syncStatus: Optional[str]  = "synced"

class MedicalRequestUpdate(BaseModel):
    """
    Schema for PATCH requests — all fields optional.
    Only provided fields will be updated.
    """
    patientName: Optional[str] = None
    type:        Optional[str] = None
    notes:       Optional[str] = None
    syncStatus:  Optional[str] = None

class MedicalRequestOut(BaseModel):
    """
    Schema for API responses — adds server-generated fields.
    """
    id:          Optional[str]      = None
    patientName: str
    type:        str
    notes:       Optional[str]      = ""
    localId:     Optional[int]      = None
    timestamp:   Optional[str]      = None
    syncStatus:  Optional[str]      = "synced"
    receivedAt:  Optional[datetime] = None