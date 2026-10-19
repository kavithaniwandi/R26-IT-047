from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

from app.core.security import TokenPayload
from app.models.relief_camp import PopulationPredictionRequest, ReliefCampUpdate
from app.routers import relief_camps


def _token(role="volunteer"):
    return TokenPayload(
        sub="7",
        role=role,
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    )


@pytest.mark.asyncio
async def test_rain_and_river_level_increase_next_hour_forecast():
    base = dict(
        currentPopulation=20,
        maxCapacity=200,
        popHistory=[20, 18, 16, 15, 14],
        hourOfDay=12,
        severity="Moderate",
    )
    dry = await relief_camps.predict_population_progression(
        PopulationPredictionRequest(**base, rainHistory=[0, 0, 0], riverLevel=4.5),
        _current_user=_token(),
    )
    wet = await relief_camps.predict_population_progression(
        PopulationPredictionRequest(**base, rainHistory=[20, 18, 16], riverLevel=7.5),
        _current_user=_token(),
    )

    assert wet.predictedPopulation > dry.predictedPopulation
    assert wet.factors["recentRainfallMm"] == 18
    assert wet.factors["riverLevelM"] == 7.5


@pytest.mark.asyncio
async def test_forecast_requires_five_real_hourly_observations():
    request = PopulationPredictionRequest(
        currentPopulation=20,
        maxCapacity=100,
        popHistory=[20, 18, 16, 14],
    )

    with pytest.raises(relief_camps.HTTPException) as error:
        await relief_camps.predict_population_progression(
            request,
            _current_user=_token(),
        )

    assert error.value.status_code == 422
    assert "Five real hourly" in error.value.detail


class _CampCollection:
    def __init__(self, document):
        self.document = document
        self.update = None

    async def find_one(self, _query):
        return self.document

    async def find_one_and_update(self, _query, update, return_document=True):
        self.update = update
        self.document.update(update.get("$set", {}))
        return self.document


@pytest.mark.asyncio
async def test_saving_prediction_does_not_create_observed_headcount(monkeypatch):
    camp_id = ObjectId()
    document = {
        "_id": camp_id,
        "dsArea": "Kaduwela",
        "gnDivision": "Ranala",
        "name": "Community Hall",
        "maxCapacityPersons": 100,
        "maxFamilies": 20,
        "currentPopulation": 30,
        "predictedPopulation": 30,
        "assignedVolunteerIds": [],
        "hourlyHistory": [],
        "lastUpdated": datetime.now(timezone.utc),
    }
    collection = _CampCollection(document)
    monkeypatch.setattr(relief_camps, "relief_camp_collection", collection)

    await relief_camps.update_camp_population(
        str(camp_id),
        ReliefCampUpdate(predictedPopulation=42),
        current_user=_token("admin"),
        db=None,
    )

    assert "$push" not in collection.update
    assert collection.update["$set"]["predictedPopulation"] == 42
