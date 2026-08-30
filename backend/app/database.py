"""
app/database.py
---------------
SQLAlchemy engine, session factory, declarative Base, and DB initializer.

All ORM models import Base from here. The session dependency (get_db) is
used by every router via FastAPI's Depends() mechanism.
"""
from __future__ import annotations
import motor.motor_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── 1. MongoDB Atlas Async Connection ───────────────────────────────────────
mongo_uri = settings.MONGODB_URI
if not mongo_uri:
    print("⚠️ WARNING: MONGODB_URI not loaded from .env!")
    
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
mongo_db = mongo_client[settings.MONGODB_DB_NAME]

disaster_requests_collection = mongo_db["disaster_requests"]
donation_items_collection = mongo_db["donation_items"]
users_collection = mongo_db["users"]
relief_camp_collection = mongo_db["relief_camps"]

# ── 2. SQLAlchemy Engine (Preserved for compatibility) ──────────────────────
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

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
_pool_kwargs = {} if _is_sqlite else {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

# Enable WAL mode for SQLite to allow concurrent reads while writing
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Declarative Base (shared by ALL ORM model classes)
# ---------------------------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI Dependency — yields a DB session per request, auto-closes on exit
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# DB Initializer — called once at startup from app lifespan
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables and seed required lookup data.

    Import every ORM model here so SQLAlchemy's metadata registry knows
    about them before calling create_all(). This is the canonical pattern
    for avoiding "table not found" errors on first boot.
    """
    # Import all models to register them with Base.metadata
    from app.models import role, user, sos, camp, donation, notification, victim, sms_log  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Seed the five canonical roles if the table is empty
    _seed_roles()
    # Seed default demo users for each portal if they don't exist
    _seed_demo_users()


def _seed_roles() -> None:
    """Ensure all five RoleEnum values exist as rows in the `roles` table."""
    from app.models.role import Role, RoleEnum

    db = SessionLocal()
    try:
        existing = {r.name for r in db.query(Role).all()}
        for role_enum in RoleEnum:
            if role_enum not in existing:
                db.add(Role(name=role_enum))
        db.commit()
    finally:
        db.close()


def _seed_demo_users() -> None:
    """
    Create one demo account per stakeholder role for dev / demo use.
    Credentials match those stored in portalConfig.js on the frontend.
    These users are only created if they don't already exist.
    """
    from passlib.context import CryptContext
    from app.models.role import Role, RoleEnum
    from app.models.user import User

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    demo_users = [
        {
            "full_name": "System Administrator",
            "email": "admin@disaster.relief.lk",
            "password": "Admin@2026!",
            "role": RoleEnum.admin,
        },
        {
            "full_name": "Victim - Kaduwela",
            "email": "victim@kaduwela.lk",
            "password": "Victim@2026!",
            "role": RoleEnum.victim,
        },
        {
            "full_name": "Dr. MOH Authority Officer",
            "email": "authority@moh.gov.lk",
            "password": "Authority@2026!",
            "role": RoleEnum.authority,
        },
        {
            "full_name": "Red Cross Relief Donor",
            "email": "donor@redcross.lk",
            "password": "Donor@2026!",
            "role": RoleEnum.donor,
        },
        {
            "full_name": "Field Volunteer Officer",
            "email": "volunteer@relief.lk",
            "password": "Volunteer@2026!",
            "role": RoleEnum.volunteer,
        },
    ]

    db = SessionLocal()
    try:
        for demo in demo_users:
            existing_user = db.query(User).filter(User.email == demo["email"]).first()
            if existing_user:
                continue
            role_obj = db.query(Role).filter(Role.name == demo["role"]).first()
            if not role_obj:
                continue
            user = User(
                full_name=demo["full_name"],
                email=demo["email"],
                hashed_password=pwd_context.hash(demo["password"]),
                role_id=role_obj.id,
                is_active=True,
            )
            db.add(user)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Demo user seeding failed (non-fatal): {exc}")
    finally:
        db.close()
