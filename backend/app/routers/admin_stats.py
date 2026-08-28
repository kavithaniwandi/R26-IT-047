"""
app/routers/admin_stats.py
--------------------------
Admin analytics, KPIs, and system health overview.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import require_role, TokenPayload
from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.sos import SOSRequest
from app.models.camp import MedicalCamp
from app.models.donation import DonationItem, Donation
from app.models.notification import Notification

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])

@router.get("/stats", dependencies=[Depends(require_role(["admin", "authority", "donor", "volunteer", "victim"]))])
def get_admin_stats(db: Session = Depends(get_db)):
    """Aggregate high-level system metrics for the Admin Dashboard."""
    total_users = db.query(User).count()
    users_by_role = {}
    for r in db.query(Role).all():
        count = db.query(User).filter(User.role_id == r.id).count()
        users_by_role[r.name.value] = count

    total_sos = db.query(SOSRequest).count()
    active_sos = db.query(SOSRequest).filter(SOSRequest.status == "active").count()
    triaged_sos = db.query(SOSRequest).filter(SOSRequest.status == "triaged").count()
    resolved_sos = db.query(SOSRequest).filter(SOSRequest.status == "resolved").count()

    total_camps = db.query(MedicalCamp).count()
    proposed_camps = db.query(MedicalCamp).filter(MedicalCamp.status == "proposed").count()
    approved_camps = db.query(MedicalCamp).filter(MedicalCamp.status == "approved").count()
    operational_camps = db.query(MedicalCamp).filter(MedicalCamp.status == "operational").count()

    total_needs = db.query(DonationItem).count()
    unmet_needs = db.query(DonationItem).filter(DonationItem.status == "unmet").count()
    partially_met = db.query(DonationItem).filter(DonationItem.status == "partially_met").count()
    fulfilled_needs = db.query(DonationItem).filter(DonationItem.status == "fulfilled").count()

    total_donations = db.query(Donation).count()
    delivered_donations = db.query(Donation).filter(Donation.delivery_status == "delivered").count()
    in_transit_donations = db.query(Donation).filter(Donation.delivery_status == "in_transit").count()

    total_notifications = db.query(Notification).count()

    # Recent active alerts for quick action table
    recent_sos = (
        db.query(SOSRequest)
        .order_by(SOSRequest.priority_score.desc(), SOSRequest.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "users": {
            "total": total_users,
            "by_role": users_by_role,
        },
        "sos": {
            "total": total_sos,
            "active": active_sos,
            "triaged": triaged_sos,
            "resolved": resolved_sos,
        },
        "camps": {
            "total": total_camps,
            "proposed": proposed_camps,
            "approved": approved_camps,
            "operational": operational_camps,
        },
        "donations": {
            "total_items": total_needs,
            "unmet": unmet_needs,
            "partially_met": partially_met,
            "fulfilled": fulfilled_needs,
            "total_pledges": total_donations,
            "delivered": delivered_donations,
            "in_transit": in_transit_donations,
        },
        "notifications_count": total_notifications,
        "recent_critical_sos": [
            {
                "id": s.id,
                "district": s.district,
                "ds_division": s.ds_division,
                "gn_division": s.gn_division,
                "urgency_level": s.urgency_level,
                "affected_people": s.affected_people,
                "priority_score": round(s.priority_score, 1),
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in recent_sos
        ],
    }
