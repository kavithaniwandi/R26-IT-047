import secrets

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app import database
from app.models.role import Role, RoleEnum
from app.models.user import User


@pytest.fixture
def seed_database(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed-test.db'}")
    database.Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", sessions)
    monkeypatch.setattr(database, "engine", engine)
    database._seed_roles()
    yield sessions
    engine.dispose()


def officer(db):
    return db.query(User).join(Role).filter(Role.name == RoleEnum.disaster_officer).one()


def test_new_seeded_officer_has_ds_area(seed_database):
    database._seed_demo_users()
    with seed_database() as db:
        assert officer(db).assigned_ds_area == "Kaduwela"


@pytest.mark.parametrize("missing_area", [None, ""])
def test_existing_officer_backfilled_without_password_or_other_account_changes(seed_database, missing_area):
    database._seed_demo_users()
    with seed_database() as db:
        existing_officer = officer(db)
        existing_officer.assigned_ds_area = missing_area
        existing_officer.hashed_password = secrets.token_urlsafe(32)
        existing_officer.full_name = "Existing officer"
        existing_officer.is_active = False
        volunteer_role = db.query(Role).filter(Role.name == RoleEnum.volunteer).one()
        volunteer = db.query(User).filter(User.role_id == volunteer_role.id).one()
        volunteer.assigned_ds_area = "Galle"
        db.commit()
        before = {
            user.id: {column.name: getattr(user, column.name) for column in User.__table__.columns}
            for user in db.query(User).all()
        }
        officer_id = existing_officer.id

    database._seed_demo_users()

    with seed_database() as db:
        after = {
            user.id: {column.name: getattr(user, column.name) for column in User.__table__.columns}
            for user in db.query(User).all()
        }
    assert set(after) == set(before)
    for user_id, previous in before.items():
        if user_id == officer_id:
            # SQLAlchemy also maintains updated_at when the area changes.
            assert after[user_id]["assigned_ds_area"] == "Kaduwela"
            for name, value in previous.items():
                if name not in {"assigned_ds_area", "updated_at"}:
                    assert after[user_id][name] == value
        else:
            assert after[user_id] == previous


def test_existing_officer_area_is_preserved(seed_database):
    database._seed_demo_users()
    with seed_database() as db:
        officer(db).assigned_ds_area = "Galle"
        db.commit()

    database._seed_demo_users()

    with seed_database() as db:
        assert officer(db).assigned_ds_area == "Galle"


def test_officer_column_migration_is_additive_and_repeatable(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy-test.db'}")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        monkeypatch.setattr(database, "engine", engine)
        database._ensure_user_donor_profile_columns()
        database._ensure_user_donor_profile_columns()
        assert "assigned_ds_area" in {column["name"] for column in inspect(engine).get_columns("users")}
    finally:
        engine.dispose()
