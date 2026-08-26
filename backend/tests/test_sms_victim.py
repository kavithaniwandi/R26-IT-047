"""
tests/test_sms_victim.py
------------------------
Unit and integration tests for SMS Gateway and Victim Registration endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.camp import MedicalCamp
from app.models.victim import Victim
from app.models.sms_log import SMSMessageLog
from app.core.security import create_access_token
from app.services.auth import _hash_password


def _create_user_with_role(db: Session, email: str, role_name: RoleEnum) -> tuple[User, str]:
    role = db.query(Role).filter(Role.name == role_name).first()
    user = User(
        full_name=f"Test {role_name.value}",
        email=email,
        hashed_password=_hash_password("Pass1234!"),
        phone="+94770000001",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, role=role_name.value)
    return user, token


def test_victim_registration_and_stats(client: TestClient, db: Session):
    # 1. Public self-registration
    payload = {
        "full_name": "Nimal Shantha",
        "phone": "+94779998811",
        "nic": "198812345678",
        "district": "Colombo",
        "ds_division": "Kaduwela",
        "gn_division": "Ranala",
        "current_address": "88 River Bank Road, Ranala",
        "latitude": 6.9364,
        "longitude": 79.9572,
        "family_members_count": 4,
        "children_count": 1,
        "elderly_count": 1,
        "disabled_count": 1,
        "pregnant_lactating_count": 0,
        "evacuation_status": "trapped_in_house",
        "chronic_diseases": "Type 2 Diabetes",
        "immediate_medical_needs": "Insulin vials",
        "dietary_and_relief_needs": "Clean water",
        "registered_via": "web_portal",
    }
    res = client.post("/api/v1/victims/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["full_name"] == "Nimal Shantha"
    assert data["vulnerability_score"] > 50.0
    assert data["evacuation_status"] == "trapped_in_house"
    victim_id = data["id"]

    # 2. Access victim list with admin token
    _, admin_token = _create_user_with_role(db, "admin_v@test.lk", RoleEnum.admin)
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    list_res = client.get("/api/v1/victims", headers=headers)
    assert list_res.status_code == 200
    victims = list_res.json()
    assert any(v["id"] == victim_id for v in victims)

    # 3. Stats summary
    stats_res = client.get("/api/v1/victims/stats/summary", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_victims"] >= 1
    assert stats["total_disabled"] >= 1


def test_victim_camp_assignment(client: TestClient, db: Session):
    _, auth_token = _create_user_with_role(db, "auth_v@test.lk", RoleEnum.authority)
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Create camp
    camp = MedicalCamp(
        name="Test Relief Base",
        latitude=6.93,
        longitude=79.98,
        district="Colombo",
        ds_division="Kaduwela",
        status="approved",
        estimated_capacity=100,
        current_occupancy=0,
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)

    # Register victim
    victim = Victim(
        full_name="Chathura Silva",
        phone="+94711112233",
        district="Colombo",
        family_members_count=3,
        evacuation_status="trapped_in_house",
        vulnerability_score=60.0,
    )
    db.add(victim)
    db.commit()
    db.refresh(victim)

    # Assign to camp
    assign_res = client.post(
        f"/api/v1/victims/{victim.id}/assign-camp",
        json={"camp_id": camp.id},
        headers=headers,
    )
    assert assign_res.status_code == 200
    updated = assign_res.json()
    assert updated["assigned_camp_id"] == camp.id
    assert updated["evacuation_status"] == "evacuated_to_camp"


def test_sms_gateway_inbound_sos_parsing(client: TestClient, db: Session):
    # Inbound SOS simulation
    payload = {
        "sender": "+94778889900",
        "message": "SOS 5 Ranala, Kaduwela 5 Trapped on 2nd floor, diabetic needs insulin urgently",
        "provider": "SIMULATOR",
    }
    res = client.post("/api/v1/sms/simulate-inbound", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "SOS_TRIGGER"
    assert data["urgency_level"] == 5
    assert data["extracted_district"] == "Colombo"
    assert data["sos_id"] is not None
    assert "SOS #" in data["auto_reply_message"]


def test_sms_gateway_registration_and_status(client: TestClient, db: Session):
    # Inbound REG command
    reg_payload = {
        "sender": "+94773334455",
        "message": "REG Chaminda Perera 198511223344 Colombo 4 Asthma",
        "provider": "DIALOG_SMSC",
    }
    reg_res = client.post("/api/v1/sms/incoming", json=reg_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["intent"] == "VICTIM_REGISTRATION"
    assert reg_data["victim_id"] is not None
    assert "Registered" in reg_data["auto_reply_message"]

    # Inbound STATUS command
    status_payload = {
        "sender": "+94773334455",
        "message": "STATUS",
        "provider": "DIALOG_SMSC",
    }
    status_res = client.post("/api/v1/sms/webhook", json=status_payload)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["intent"] == "STATUS_CHECK"


def test_sms_send_and_broadcast(client: TestClient, db: Session):
    _, admin_token = _create_user_with_role(db, "admin_sms@test.lk", RoleEnum.admin)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Direct send
    send_res = client.post(
        "/api/v1/sms/send",
        json={
            "recipient": "+94771234567",
            "message": "Emergency rescue boat is en route to your location.",
            "message_type": "RESCUE_UPDATE",
        },
        headers=headers,
    )
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "delivered"

    # Broadcast
    bcast_res = client.post(
        "/api/v1/sms/broadcast",
        json={
            "district": "Colombo",
            "message": "Heavy rainfall warning. Evacuate low-lying river areas.",
            "urgency": "CRITICAL",
        },
        headers=headers,
    )
    assert bcast_res.status_code == 200
    assert bcast_res.json()["status"] == "success"

    # Gateway status
    status_res = client.get("/api/v1/sms/gateway-status")
    assert status_res.status_code == 200
    assert "ONLINE" in status_res.json()["gateway_status"]
