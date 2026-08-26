"""
app/routers/notifications.py
----------------------------
Notification audit logs endpoint.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.database import get_db
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationOut(BaseModel):
    id: int
    channel: str
    message_type: str
    recipient_target: str
    message_content: str
    dispatch_status: str
    dispatched_at: str

@router.get("", response_model=List[NotificationOut], dependencies=[Depends(require_role(["admin", "authority"]))])
def list_notifications(limit: int = 50, db: Session = Depends(get_db)):
    """List dispatched alert notifications."""
    logs = db.query(Notification).order_by(Notification.dispatched_at.desc()).limit(limit).all()
    return [
        NotificationOut(
            id=n.id,
            channel=n.channel,
            message_type=n.message_type,
            recipient_target=n.recipient_target,
            message_content=n.message_content,
            dispatch_status=n.dispatch_status,
            dispatched_at=n.dispatched_at.isoformat(),
        )
        for n in logs
    ]
