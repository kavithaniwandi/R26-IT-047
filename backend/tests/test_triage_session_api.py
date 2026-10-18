from __future__ import annotations

import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.models.main import app

    test_client = TestClient(app)
    yield test_client
    test_client.close()


class _InsertResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class _AsyncCursor:
    def __init__(self, docs: list[dict]):
        self.docs = docs

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self.docs):
            raise StopAsyncIteration
        item = dict(self.docs[self._index])
        self._index += 1
        return item


class _ArchiveCollection:
    def __init__(self):
        self.docs = [
            {
                "_id": "archive-doc-1",
                "session_id": "session-1",
                "camp": {"id": "camp-1", "name": "Camp One"},
                "mos": [],
                "summary": {"total": 1},
                "patients": [{"id": "patient-1"}],
            }
        ]

    def find(self, *args, **kwargs):
        projected = [{key: value for key, value in doc.items() if key != "patients"} for doc in self.docs]
        return _AsyncCursor(projected)

    async def find_one(self, query):
        for doc in self.docs:
            if doc["session_id"] == query.get("session_id"):
                return dict(doc)
        return None

    async def count_documents(self, query):
        return len(self.docs)


class _FakeDb:
    def __getitem__(self, name):
        return getattr(self, name)

    def __init__(self):
        self.triage_archives = _ArchiveCollection()


def test_start_session_and_save_patient_use_document_store(client, monkeypatch):
    async def fake_save_session(payload):
        assert payload["session_id"] == "session-1"
        return "session-doc-1"

    async def fake_save_patient(payload):
        assert payload["id"] == "patient-1"
        assert payload["session_id"] == "session-1"
        return "patient-doc-1"

    monkeypatch.setattr("app.services.mongo_service.save_triage_session", fake_save_session)
    monkeypatch.setattr("app.services.mongo_service.save_triage_patient", fake_save_patient)

    session_response = client.post(
        "/api/v1/triage/session/start",
        json={"session_id": "session-1", "camp": {"id": "camp-1"}, "mos": []},
    )
    patient_response = client.post(
        "/api/v1/triage/patient/save",
        json={"id": "patient-1", "session_id": "session-1", "severity": "LOW"},
    )

    assert session_response.status_code == 200
    assert session_response.json() == {
        "status": "saved",
        "doc_id": "session-doc-1",
        "session_id": "session-1",
    }
    assert patient_response.status_code == 200
    assert patient_response.json() == {
        "status": "saved",
        "doc_id": "patient-doc-1",
        "patient_id": "patient-1",
    }


def test_archive_list_and_archive_by_id_use_distinct_routes(client, monkeypatch):
    from app.services import mongo_service

    monkeypatch.setattr(mongo_service, "_db", _FakeDb())

    list_response = client.get("/api/v1/triage/archives")
    detail_response = client.get("/api/v1/triage/archives/session-1")

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["archives"][0]["session_id"] == "session-1"
    assert "patients" not in list_response.json()["archives"][0]

    assert detail_response.status_code == 200
    assert detail_response.json()["session_id"] == "session-1"
    assert detail_response.json()["patients"] == [{"id": "patient-1"}]


def test_end_session_archives_payload(client, monkeypatch):
    async def fake_archive_triage_session(session_id, session_data, patients, summary):
        assert session_id == "session-1"
        assert session_data["camp"]["id"] == "camp-1"
        assert patients == [{"id": "patient-1"}]
        assert summary == {"total": 1}
        return "archive-doc-1"

    monkeypatch.setattr("app.services.mongo_service.archive_triage_session", fake_archive_triage_session)

    response = client.post(
        "/api/v1/triage/session/end",
        json={
            "session_id": "session-1",
            "session": {"camp": {"id": "camp-1"}},
            "patients": [{"id": "patient-1"}],
            "summary": {"total": 1},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "archived",
        "doc_id": "archive-doc-1",
        "session_id": "session-1",
    }



def test_session_start_reports_failed_when_helper_returns_none(client, monkeypatch):
    async def no_document(payload):
        return None
    monkeypatch.setattr('app.services.mongo_service.save_triage_session', no_document)
    response = client.post('/api/v1/triage/session/start', json={'session_id': 'not-saved'})
    assert response.status_code == 503
    assert response.json() == {
        'status': 'failed', 'detail': 'Triage session could not be persisted.',
        'session_id': 'not-saved',
    }


def test_session_start_still_validates_session_id(client):
    assert client.post('/api/v1/triage/session/start', json={}).status_code == 422
