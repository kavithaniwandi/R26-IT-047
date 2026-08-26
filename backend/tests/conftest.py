"""
tests/conftest.py
------------------
Shared pytest fixtures for the entire test suite.

Key design:
  - Uses an in-memory SQLite DB (separate from the real DB) so tests
    are fully isolated and never touch production data.
  - Overrides the `get_db` FastAPI dependency so route handlers use
    the test DB session automatically.
  - The `client` fixture provides a synchronous TestClient that works
    with FastAPI's lifespan (tables created + roles seeded before tests).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base, get_db
from app.main import app

# ── In-memory test database ───────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Yield a test DB session instead of the real one."""
    db: Session = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Create all tables and seed roles in the in-memory test DB once
    per test session.  Runs before any test in the suite.
    """
    # Import all models so Base.metadata picks them up
    from app.models.role import Role  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.sos import SOSRequest  # noqa: F401
    from app.models.risk import RiskPrediction  # noqa: F401
    from app.models.camp import MedicalCamp  # noqa: F401
    from app.models.donation import DonationItem, Donation  # noqa: F401
    from app.models.notification import Notification  # noqa: F401
    from app.models.victim import Victim  # noqa: F401
    from app.models.sms_log import SMSMessageLog  # noqa: F401

    Base.metadata.create_all(bind=test_engine)

    # Seed roles
    from app.models.role import RoleEnum
    db = TestSessionLocal()
    try:
        for role_name in RoleEnum:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db() -> Session:
    """Fresh DB session for a single test; rolls back after the test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """
    TestClient wired to the in-memory DB.
    Each test gets its own isolated session (rolled back after the test).
    """
    def _override_get_db():
        try:
            yield db
        finally:
            pass  # rollback handled by the `db` fixture above

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
