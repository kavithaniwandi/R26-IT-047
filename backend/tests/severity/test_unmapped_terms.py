from __future__ import annotations

import pytest


class _AggregateCursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, _limit):
        return self.rows


class _PatientCollection:
    def __init__(self):
        self.pipeline = None

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        return _AggregateCursor(
            [
                {"_id": "fever", "count": 4},
                {"_id": "wound", "count": 2},
            ]
        )


class _Db:
    def __init__(self):
        self.triage_patients = _PatientCollection()


@pytest.mark.asyncio
async def test_get_unmapped_terms_aggregates_saved_patient_terms(monkeypatch):
    from app.services import mongo_service

    db = _Db()
    monkeypatch.setattr(mongo_service, "_db", db)

    rows = await mongo_service.get_unmapped_terms(limit=10)

    assert rows == [
        {"term": "fever", "count": 4},
        {"term": "wound", "count": 2},
    ]
    assert db.triage_patients.pipeline is not None


def test_unmapped_terms_endpoint_returns_aggregation(client, monkeypatch):
    async def fake_get_unmapped_terms(limit=50):
        assert limit == 3
        return [{"term": "fever", "count": 4}]

    monkeypatch.setattr("app.services.mongo_service.get_unmapped_terms", fake_get_unmapped_terms)

    response = client.get("/api/severity/unmapped-terms?limit=3")

    assert response.status_code == 200
    assert response.json() == {"terms": [{"term": "fever", "count": 4}]}
