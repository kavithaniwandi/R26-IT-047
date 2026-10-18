"""Exercise triage persistence without connecting to, or writing to, a real database."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.triage import router
from app.services import mongo_service as mongo


class Collection:
    def __init__(self):
        self.docs = {}
        self.acknowledged = True
        self.fail = False

    async def update_one(self, query, update, upsert=False):
        if self.fail:
            raise RuntimeError("simulated storage outage")
        existing = await self.find_one(query)
        if existing is None and upsert:
            existing = {**query, **deepcopy(update.get("$setOnInsert", {}))}
            self.docs[existing["_id"]] = existing
        if existing is not None:
            self.docs[existing["_id"]].update(deepcopy(update.get("$set", {})))
        return SimpleNamespace(acknowledged=self.acknowledged)

    async def find_one(self, query):
        return next((deepcopy(d) for d in self.docs.values() if all(d.get(k) == v for k, v in query.items())), None)


@pytest.fixture
def store(monkeypatch):
    collections = {name: Collection() for name in ("triage_sessions", "triage_patients", "triage_archives")}
    monkeypatch.setattr(mongo, "get_mongo_collection", collections.__getitem__)
    return collections


@pytest.fixture
def triage_client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("endpoint,helper,payload", [
    ("session/start", "save_triage_session", {"session_id": "s"}),
    ("patient/save", "save_triage_patient", {"id": "p", "session_id": "s", "severity": "LOW"}),
    ("session/end", "archive_triage_session", {"session_id": "s"}),
])
@pytest.mark.parametrize("raises", [False, True])
def test_unconfirmed_writes_never_return_success(triage_client, monkeypatch, endpoint, helper, payload, raises):
    async def failure(*args, **kwargs):
        if raises:
            raise RuntimeError("simulated outage")
        return None
    monkeypatch.setattr(mongo, helper, failure)
    response = triage_client.post(f"/api/v1/triage/{endpoint}", json=payload)
    assert response.status_code == 503
    assert response.json().get("status") != "saved"


@pytest.mark.parametrize("endpoint", ["patients", "archives"])
def test_failed_reads_do_not_look_like_empty_lists(triage_client, monkeypatch, endpoint):
    def failure(name):
        raise RuntimeError("simulated unavailable database")
    monkeypatch.setattr(mongo, "get_mongo_collection", failure)
    assert triage_client.get(f"/api/v1/triage/{endpoint}").status_code == 503


def test_cold_start_uses_lazy_connection(monkeypatch):
    db = {"triage_patients": object()}
    calls = []
    def client(*args, **kwargs):
        calls.append(1)
        return {mongo.settings.MONGODB_DB_NAME: db}
    monkeypatch.setattr(mongo.settings, "MONGODB_URI", "mongodb://unused-test-host")
    monkeypatch.setattr(mongo, "motor", SimpleNamespace(AsyncIOMotorClient=client))
    monkeypatch.setattr(mongo, "_client", None)
    monkeypatch.setattr(mongo, "_db", None)
    assert mongo.get_mongo_collection("triage_patients") is db["triage_patients"]
    assert mongo.get_mongo_collection("triage_patients") is db["triage_patients"]
    assert len(calls) == 1


def test_patient_retry_preserves_all_fields_and_does_not_duplicate(triage_client, store):
    assert triage_client.post("/api/v1/triage/session/start", json={"session_id": "s"}).status_code == 200
    payload = {
        "id": "p", "session_id": "s", "severity": "LOW", "should_queue": False,
        "symptoms": "Synthetic mild headache", "clinical_note": "Synthetic test note, not a real patient.",
        "vitals": {"vital_spo2": 99, "pain_score": 0}, "scores": {"LOW": 0.9},
    }
    first = triage_client.post("/api/v1/triage/patient/save", json=payload)
    second = triage_client.post("/api/v1/triage/patient/save", json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json()["doc_id"] == second.json()["doc_id"]
    assert len(store["triage_patients"].docs) == 1
    saved = next(iter(store["triage_patients"].docs.values()))
    for key in ("clinical_note", "vitals", "scores"):
        assert saved[key] == payload[key]
    assert saved["should_queue"] is True  # Includes older clients sending False.


def test_unacknowledged_patient_write_is_failure(triage_client, store):
    triage_client.post("/api/v1/triage/session/start", json={"session_id": "s"})
    store["triage_patients"].acknowledged = False
    response = triage_client.post("/api/v1/triage/patient/save", json={"id": "p", "session_id": "s", "severity": "HIGH"})
    assert response.status_code == 503


def test_archive_retry_after_partial_failure_is_idempotent(triage_client, store):
    triage_client.post("/api/v1/triage/session/start", json={"session_id": "s"})
    store["triage_sessions"].fail = True
    assert triage_client.post("/api/v1/triage/session/end", json={"session_id": "s"}).status_code == 503
    store["triage_sessions"].fail = False
    assert triage_client.post("/api/v1/triage/session/end", json={"session_id": "s"}).status_code == 200
    assert len(store["triage_archives"].docs) == 1
    assert next(iter(store["triage_sessions"].docs.values()))["status"] == "ended"


def test_missing_or_closed_session_rejects_new_patients(triage_client, store):
    payload = {"id": "p", "session_id": "s", "severity": "HIGH"}
    assert triage_client.post("/api/v1/triage/patient/save", json=payload).status_code == 409
    triage_client.post("/api/v1/triage/session/start", json={"session_id": "s"})
    triage_client.post("/api/v1/triage/session/end", json={"session_id": "s"})
    assert triage_client.post("/api/v1/triage/patient/save", json=payload).status_code == 409
    assert triage_client.post("/api/v1/triage/session/start", json={"session_id": "s"}).status_code == 409


def test_invalid_patient_payload_returns_validation_error(triage_client):
    for payload in ({"id": {}, "session_id": "s"}, {"id": "p", "session_id": ["s"]}, {"id": "p", "session_id": "s", "severity": "INVALID"}):
        assert triage_client.post("/api/v1/triage/patient/save", json=payload).status_code == 422
