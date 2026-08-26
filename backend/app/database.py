"""
app/database.py
---------------
SQLAlchemy engine, session factory, declarative Base, and comprehensive seeder.
"""
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
_pool_kwargs = {} if _is_sqlite else {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    echo=False,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _sqlite_schema_is_stale() -> bool:
    """
    For SQLite only: inspect the live 'users' table columns and compare
    against the ORM-declared columns. Returns True if any column is missing,
    meaning the DB file predates the current model definition.
    """
    if not _is_sqlite:
        return False
    try:
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        if "users" not in inspector.get_table_names():
            return False  # fresh DB, create_all will handle it
        live_cols = {col["name"] for col in inspector.get_columns("users")}
        expected_cols = {"id", "full_name", "email", "hashed_password",
                         "phone", "address", "role_id", "is_active",
                         "created_at", "updated_at"}
        return not expected_cols.issubset(live_cols)
    except Exception:
        return False


def init_db() -> None:
    """
    Create all tables and seed canonical roles and master admin account.

    For SQLite (local dev): automatically detects a stale schema (columns
    added to models after the DB file was first created) and drops/recreates
    the file so 'no such column' errors never crash startup.
    MySQL (Docker/production): uses the DB as-is — run Alembic migrations there.
    """
    from app.models.role import Role  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.sos import SOSRequest  # noqa: F401
    from app.models.risk import RiskPrediction  # noqa: F401
    from app.models.camp import MedicalCamp  # noqa: F401
    from app.models.donation import DonationItem, Donation  # noqa: F401
    from app.models.notification import Notification  # noqa: F401
    from app.models.victim import Victim  # noqa: F401
    from app.models.sms_log import SMSMessageLog  # noqa: F401

    # ── SQLite dev-mode schema guard ─────────────────────────────────────────
    if _is_sqlite and _sqlite_schema_is_stale():
        import os
        import urllib.parse
        # Extract the file path from the sqlite URL (e.g. sqlite:///./foo.db)
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
            import logging
            logging.getLogger(__name__).warning(
                "⚠️  Stale SQLite schema detected — deleted '%s' and "
                "will recreate all tables fresh. All previous data is cleared.",
                db_path,
            )
    # ── Create tables (no-op if already current) ─────────────────────────────
    Base.metadata.create_all(bind=engine)
    _seed_roles_and_master_data()

def _seed_roles_and_master_data() -> None:
    """Insert canonical roles, demo admin/authority accounts, and initial seed items."""
    from app.models.role import Role, RoleEnum
    from app.models.user import User
    from app.models.sos import SOSRequest
    from app.models.camp import MedicalCamp
    from app.models.donation import DonationItem, Donation
    from app.models.notification import Notification
    from app.models.victim import Victim
    from app.models.sms_log import SMSMessageLog

    db: Session = SessionLocal()
    try:
        # 1. Seed Roles
        for role_name in RoleEnum:
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                db.add(Role(name=role_name))
        db.commit()

        # 2. Seed Default Admin User
        admin_role = db.query(Role).filter(Role.name == RoleEnum.admin).first()
        existing_admin = db.query(User).filter(User.email == "admin@disaster.relief.lk").first()
        if not existing_admin and admin_role:
            admin_user = User(
                full_name="System Administrator",
                email="admin@disaster.relief.lk",
                hashed_password=pwd_context.hash("Admin@2026!"),
                phone="+94112345678",
                address="National Disaster Management Centre, Colombo 07",
                role_id=admin_role.id,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()

        # 3. Seed Default Authority User
        auth_role = db.query(Role).filter(Role.name == RoleEnum.authority).first()
        existing_auth = db.query(User).filter(User.email == "authority@moh.gov.lk").first()
        if not existing_auth and auth_role:
            auth_user = User(
                full_name="Dr. Nihal Jayasinghe (MOH Officer)",
                email="authority@moh.gov.lk",
                hashed_password=pwd_context.hash("Authority@2026!"),
                phone="+94779876543",
                address="Ministry of Health, Colombo",
                role_id=auth_role.id,
                is_active=True,
            )
            db.add(auth_user)
            db.commit()

        # 4. Seed Default Donor User
        donor_role = db.query(Role).filter(Role.name == RoleEnum.donor).first()
        existing_donor = db.query(User).filter(User.email == "donor@redcross.lk").first()
        if not existing_donor and donor_role:
            donor_user = User(
                full_name="Sri Lanka Red Cross Society",
                email="donor@redcross.lk",
                hashed_password=pwd_context.hash("Donor@2026!"),
                phone="+94115678901",
                address="Dharmapala Mawatha, Colombo 03",
                role_id=donor_role.id,
                is_active=True,
            )
            db.add(donor_user)
            db.commit()

        # 5. Seed Default Victim User
        victim_role = db.query(Role).filter(Role.name == RoleEnum.victim).first()
        existing_victim = db.query(User).filter(User.email == "victim@kaduwela.lk").first()
        if not existing_victim and victim_role:
            victim_user = User(
                full_name="Sunil Perera",
                email="victim@kaduwela.lk",
                hashed_password=pwd_context.hash("Victim@2026!"),
                phone="+94712345678",
                address="45 Low Level Road, Ranala, Kaduwela",
                role_id=victim_role.id,
                is_active=True,
            )
            db.add(victim_user)
            db.commit()

        # 6. Seed Sample SOS Alerts if empty
        if db.query(SOSRequest).count() == 0:
            vic = db.query(User).filter(User.email == "victim@kaduwela.lk").first()
            uid = vic.id if vic else 1

            sos1 = SOSRequest(
                user_id=uid,
                latitude=6.936419,
                longitude=79.957216,
                district="Colombo",
                ds_division="Kaduwela",
                gn_division="Ranala",
                address_text="45 River View Lane, Ranala",
                urgency_level=5,
                affected_people=18,
                affected_families=4,
                has_elderly=True,
                has_children=True,
                has_disabled=True,
                medical_needs_summary="Insulin, Asthma Inhalers, First Aid Bandages, Clean Water",
                priority_score=94.5,
                status="active",
            )
            sos2 = SOSRequest(
                user_id=uid,
                latitude=6.923639,
                longitude=80.002176,
                district="Colombo",
                ds_division="Kaduwela",
                gn_division="Kaduwela Central",
                address_text="12 Old Bridge Road, Kaduwela",
                urgency_level=4,
                affected_people=9,
                affected_families=2,
                has_elderly=True,
                has_children=False,
                has_disabled=False,
                medical_needs_summary="Paracetamol, Amoxicillin, Antiseptic lotion",
                priority_score=78.2,
                status="active",
            )
            sos3 = SOSRequest(
                user_id=uid,
                latitude=6.905000,
                longitude=80.498000,
                district="Nuwara Eliya",
                ds_division="Ambagamuwa Korale",
                gn_division="317 A Lakshapana",
                address_text="Kanamadilihena, Lakshapana",
                urgency_level=5,
                affected_people=25,
                affected_families=6,
                has_elderly=True,
                has_children=True,
                has_disabled=False,
                medical_needs_summary="Trauma Kits, Sutures, Oral Rehydration Salts, IV Saline",
                priority_score=96.0,
                status="active",
            )
            db.add_all([sos1, sos2, sos3])
            db.commit()

            # Seed Donation Items for SOS 1 & 3
            di1 = DonationItem(
                sos_request_id=sos1.id,
                category="Medicine",
                item_name="Human Insulin 100 IU/ml Vials",
                quantity_required=30,
                quantity_fulfilled=10,
                unit="vials",
                status="partially_met",
            )
            di2 = DonationItem(
                sos_request_id=sos1.id,
                category="Consumables",
                item_name="Sterile Gauze Bandages 4-inch",
                quantity_required=100,
                quantity_fulfilled=100,
                unit="packs",
                status="fulfilled",
            )
            di3 = DonationItem(
                sos_request_id=sos3.id,
                category="Equipment",
                item_name="Emergency Trauma Stretchers",
                quantity_required=5,
                quantity_fulfilled=0,
                unit="units",
                status="unmet",
            )
            di4 = DonationItem(
                sos_request_id=sos3.id,
                category="Medicine",
                item_name="IV Normal Saline 0.9% 500ml",
                quantity_required=80,
                quantity_fulfilled=20,
                unit="bottles",
                status="partially_met",
            )
            db.add_all([di1, di2, di3, di4])
            db.commit()

        # 7. Seed Medical Camps if empty
        if db.query(MedicalCamp).count() == 0:
            c1 = MedicalCamp(
                name="Kaduwela Mahawatta Relief Camp",
                latitude=6.931000,
                longitude=79.980000,
                district="Colombo",
                ds_division="Kaduwela",
                gn_division="Nawagamuwa South",
                suitability_score=91.5,
                estimated_capacity=250,
                current_occupancy=65,
                status="approved",
            )
            c2 = MedicalCamp(
                name="Ranala Community Health Centre",
                latitude=6.938000,
                longitude=79.960000,
                district="Colombo",
                ds_division="Kaduwela",
                gn_division="Ranala",
                suitability_score=88.0,
                estimated_capacity=150,
                current_occupancy=30,
                status="operational",
            )
            c3 = MedicalCamp(
                name="Lakshapana Primary School Medical Post",
                latitude=6.908000,
                longitude=80.492000,
                district="Nuwara Eliya",
                ds_division="Ambagamuwa Korale",
                gn_division="317 A Lakshapana",
                suitability_score=85.0,
                estimated_capacity=100,
                current_occupancy=0,
                status="proposed",
            )
            db.add_all([c1, c2, c3])
            db.commit()

        # 8. Seed Victims if empty
        if db.query(Victim).count() == 0:
            vic_user = db.query(User).filter(User.email == "victim@kaduwela.lk").first()
            c1_rec = db.query(MedicalCamp).first()
            
            v1 = Victim(
                user_id=vic_user.id if vic_user else None,
                nic="198421401234",
                full_name="Sunil Perera",
                phone="+94712345678",
                alternate_phone="+94112349999",
                gender="male",
                age=48,
                district="Colombo",
                ds_division="Kaduwela",
                gn_division="Ranala",
                current_address="45 Low Level Road, Ranala, Kaduwela",
                latitude=6.936419,
                longitude=79.957216,
                family_members_count=4,
                children_count=1,
                elderly_count=2,
                disabled_count=1,
                pregnant_lactating_count=0,
                evacuation_status="trapped_in_house",
                assigned_camp_id=c1_rec.id if c1_rec else None,
                chronic_diseases="Type 2 Diabetes, Severe Hypertension",
                immediate_medical_needs="Human Insulin vials, Sterile bandages",
                dietary_and_relief_needs="Clean drinking water (20L), Dry Rations",
                vulnerability_score=92.5,
                registered_via="web_portal",
                is_verified=True,
                notes="House flooded up to ground floor ceiling; 2 elderly members on upper floor.",
            )
            v2 = Victim(
                user_id=None,
                nic="199278901234",
                full_name="Kumari Jayawardena",
                phone="+94775551234",
                alternate_phone=None,
                gender="female",
                age=32,
                district="Colombo",
                ds_division="Kolonnawa",
                gn_division="Wellampitiya",
                current_address="12 Canal Bank Road, Wellampitiya",
                latitude=6.941200,
                longitude=79.894200,
                family_members_count=5,
                children_count=2,
                elderly_count=1,
                disabled_count=0,
                pregnant_lactating_count=1,
                evacuation_status="isolated_roof_level",
                assigned_camp_id=None,
                chronic_diseases="Asthma",
                immediate_medical_needs="Asthma Salbutamol Inhaler, Pediatric Amoxicillin",
                dietary_and_relief_needs="Baby milk formula, Diapers, Ready-to-eat meals",
                vulnerability_score=88.0,
                registered_via="sms_gateway",
                is_verified=True,
                notes="Registered via SMS; water level rising rapidly near Kelani river bank.",
            )
            v3 = Victim(
                user_id=None,
                nic="197612345678",
                full_name="Ramesh Chandrasekara",
                phone="+94789998877",
                alternate_phone=None,
                gender="male",
                age=51,
                district="Nuwara Eliya",
                ds_division="Ambagamuwa",
                gn_division="317 A Lakshapana",
                current_address="Kanamadilihena Tea Estate, Lakshapana",
                latitude=6.905000,
                longitude=80.498000,
                family_members_count=6,
                children_count=2,
                elderly_count=2,
                disabled_count=0,
                pregnant_lactating_count=0,
                evacuation_status="evacuated_to_camp",
                assigned_camp_id=c1_rec.id if c1_rec else None,
                chronic_diseases="Arthritis",
                immediate_medical_needs="Pain relief tablets, Antiseptic lotion",
                dietary_and_relief_needs="Warm blankets, Drinking water",
                vulnerability_score=68.5,
                registered_via="camp_intake",
                is_verified=True,
                notes="Evacuated following minor slope failure; shelter secured at camp.",
            )
            db.add_all([v1, v2, v3])
            db.commit()

        # 9. Seed SMS Gateway Logs if empty
        if db.query(SMSMessageLog).count() == 0:
            sms1 = SMSMessageLog(
                direction="inbound",
                sender="+94775551234",
                recipient="1919",
                message_text="SOS 5 Wellampitiya 5 Need asthma inhaler and baby milk formula urgently water rising",
                message_type="EMERGENCY_SOS",
                parsed_intent="SOS_TRIGGER",
                status="processed",
                gateway_provider="DIALOG_SMSC",
            )
            sms2 = SMSMessageLog(
                direction="outbound",
                sender="DISASTER-RELIEF-1919",
                recipient="+94775551234",
                message_text="[RELIEF-911] SOS #1 RECEIVED! Priority: 92.5/100 (Urgency 5/5). Responders alerted. Stay in safe spot.",
                message_type="SYSTEM_CONFIRMATION",
                parsed_intent="SOS_TRIGGER",
                status="delivered",
                gateway_provider="DIALOG_SMSC",
            )
            db.add_all([sms1, sms2])
            db.commit()

    finally:
        db.close()

