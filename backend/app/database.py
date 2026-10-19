"""SQL and MongoDB boundaries for the integrated research application.

The established research features keep their SQLAlchemy database. The
individual disaster-operations component uses lazy MongoDB collection proxies,
so Atlas availability never prevents the SQL application from starting.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


class _LazyMongoCollection:
    def __init__(self, name: str) -> None:
        self.name = name

    def __getattr__(self, attribute: str):
        from app.services.mongo_service import get_component_mongo_collection

        return getattr(get_component_mongo_collection(self.name), attribute)


# MongoDB collections owned by the individual component. Keep the original
# collection names so the merged application reads the component's existing
# Atlas data instead of creating parallel, empty collections.
disaster_requests_collection = _LazyMongoCollection("disaster_donation_requests")
disaster_donation_request_collection = disaster_requests_collection
donation_items_collection = _LazyMongoCollection("donation_items")
users_collection = _LazyMongoCollection("users")
user_collection = users_collection
relief_camp_collection = _LazyMongoCollection("relief_camps")
division_collection = _LazyMongoCollection("administrative_divisions")
donation_history_collection = _LazyMongoCollection("donation_history")


# SQL database retained for every pre-existing research module.
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=False,
    **({} if _is_sqlite else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }),
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import camp, donation, notification, role, sms_log, sos, user, victim  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_user_donor_profile_columns()
    _ensure_user_emergency_contacts_column()
    _seed_roles()
    _seed_demo_users()


def _ensure_user_donor_profile_columns() -> None:
    """Small additive migration for deployments created before donor profiles."""
    existing = {column["name"] for column in inspect(engine).get_columns("users")}
    columns = {
        "donor_type": "VARCHAR(30)",
        "preferred_donation_category": "VARCHAR(40)",
        "capacity_level": "VARCHAR(20)",
        "latitude": "FLOAT",
        "longitude": "FLOAT",
        "assigned_ds_area": "VARCHAR(120)",
    }
    with engine.begin() as connection:
        for name, sql_type in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))


def _ensure_user_emergency_contacts_column() -> None:
    """Additive migration for users created before emergency contacts."""
    existing = {column["name"] for column in inspect(engine).get_columns("users")}
    if "emergency_contacts" not in existing:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN emergency_contacts TEXT"))


def _seed_roles() -> None:
    from app.models.role import Role, RoleEnum

    db = SessionLocal()
    try:
        existing = {row.name for row in db.query(Role).all()}
        for role_name in RoleEnum:
            if role_name not in existing:
                db.add(Role(name=role_name))
        db.commit()
    finally:
        db.close()


def _seed_demo_users() -> None:
    from passlib.context import CryptContext

    from app.models.role import Role, RoleEnum
    from app.models.user import User

    demo_users = [
        ("System Administrator", "admin@disaster.relief.lk", "Admin@2026!", RoleEnum.admin),
        ("Victim - Kaduwela", "victim@kaduwela.lk", "Victim@2026!", RoleEnum.victim),
        ("Dr. MOH Authority Officer", "authority@moh.gov.lk", "Authority@2026!", RoleEnum.authority),
        ("Red Cross Relief Donor", "donor@redcross.lk", "Donor@2026!", RoleEnum.donor),
        ("Field Volunteer Officer", "volunteer@relief.lk", "Volunteer@2026!", RoleEnum.volunteer),
        ("District Disaster Officer", "officer@disaster.relief.lk", "Officer@2026!", RoleEnum.disaster_officer),
    ]
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        for full_name, email, password, role_name in demo_users:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                if role_name == RoleEnum.disaster_officer and not existing_user.assigned_ds_area:
                    existing_user.assigned_ds_area = "Kaduwela"
                continue
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                db.add(User(
                    full_name=full_name,
                    email=email,
                    hashed_password=password_context.hash(password),
                    role_id=role.id,
                    assigned_ds_area="Kaduwela" if role_name == RoleEnum.disaster_officer else None,
                    is_active=True,
                ))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Demo user seeding failed (non-fatal): {exc}")
    finally:
        db.close()
