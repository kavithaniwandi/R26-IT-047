from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

from app.core.security import TokenPayload
from app.models.relief_camp import PopulationPredictionRequest, ReliefCampUpdate
from app.routers import relief_camps
from app.services.camp_population_service import (
    MODEL_FEATURE_NAMES,
    load_population_rf_package,
    predict_camp_population_rf,
    SRI_LANKA_TZ,
)


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

    async def update_one(self, _query, update):
        self.update = update
        self.document.update(update.get("$set", {}))
        return True


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


def test_random_forest_package_features_and_metadata():
    pkg = load_population_rf_package()
    assert "model" in pkg
    assert "features" in pkg
    assert pkg.get("model_name") == "Random Forest Regressor"
    assert pkg.get("target") == "next_hour_population"
    assert pkg.get("version") == "1.0"
    assert pkg["features"] == MODEL_FEATURE_NAMES
    assert len(pkg["features"]) == 15


def test_random_forest_uncapped_predicted_demand_and_overflow():
    """Predicted demand above maxCapacity is preserved for emergency response."""
    result = predict_camp_population_rf(
        max_capacity=100,
        hourly_observations=[76, 100, 112, 130, 145],
        rainfall_mm=2.5,
        rainfall_3h_avg_mm=3.0,
        temperature_c=28.0,
        humidity_pct=85.0,
        river_level_m=5.5,
        river_level_change_m=0.2,
        hour_of_day=13,
    )

    assert result["predictedPopulation"] > 100
    assert result["maxCapacity"] == 100
    assert result["expectedSheltered"] == 100
    assert result["overflow"] == result["predictedPopulation"] - 100
    assert result["status"] == "OVERFLOW_RISK"
    assert result["observationsUsed"] == [76, 100, 112, 130, 145]


def test_random_forest_within_capacity():
    result = predict_camp_population_rf(
        max_capacity=500,
        hourly_observations=[20, 25, 28, 30, 35],
        rainfall_mm=0.0,
        rainfall_3h_avg_mm=0.0,
        temperature_c=27.0,
        humidity_pct=70.0,
        river_level_m=3.5,
        river_level_change_m=-0.05,
        hour_of_day=10,
    )

    assert result["maxCapacity"] == 500
    assert result["predictedPopulation"] <= 500
    assert result["expectedSheltered"] == result["predictedPopulation"]
    assert result["overflow"] == 0
    assert result["status"] == "WITHIN_CAPACITY"


@pytest.mark.asyncio
async def test_hourly_observation_deduplication_in_same_hour(monkeypatch):
    camp_id = ObjectId()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    document = {
        "_id": camp_id,
        "name": "Deduplication Test Camp",
        "maxCapacityPersons": 100,
        "currentPopulation": 50,
        "predictedPopulation": 50,
        "assignedVolunteerIds": ["7"],
        "hourlyHistory": [
            {"timestamp": one_hour_ago, "population": 45, "predictedPopulation": 50, "source": "manual"},
            {"timestamp": now, "population": 50, "predictedPopulation": 50, "source": "manual"},
        ],
        "lastUpdated": now,
    }
    collection = _CampCollection(document)
    monkeypatch.setattr(relief_camps, "relief_camp_collection", collection)

    # Correcting population in the current hour should replace/update the existing entry rather than append
    await relief_camps.update_camp_population(
        str(camp_id),
        ReliefCampUpdate(currentPopulation=55, observationSource="manual"),
        current_user=_token("volunteer"),
        db=None,
    )

    history = collection.document.get("hourlyHistory", [])
    assert len(history) == 2
    assert history[-1]["population"] == 55
    assert collection.document["currentPopulation"] == 55


@pytest.mark.asyncio
async def test_invalid_input_validation():
    # Negative population in request raises 422
    with pytest.raises(relief_camps.HTTPException) as err1:
        await relief_camps.predict_population_progression(
            PopulationPredictionRequest(
                maxCapacity=100,
                popHistory=[20, 18, 16, 15, -5],
            ),
            _current_user=_token(),
        )
    assert err1.value.status_code == 422

    # Zero or negative capacity is rejected by schema validation
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PopulationPredictionRequest(
            maxCapacity=0,
            popHistory=[20, 18, 16, 15, 14],
        )

    # ML service rejects non-positive capacity
    with pytest.raises(ValueError) as err3:
        predict_camp_population_rf(
            max_capacity=0,
            hourly_observations=[10, 20, 30, 40, 50],
            rainfall_mm=0.0,
            rainfall_3h_avg_mm=0.0,
            temperature_c=27.0,
            humidity_pct=80.0,
            river_level_m=5.0,
            river_level_change_m=0.0,
            hour_of_day=12,
        )
    assert "Maximum capacity must be positive" in str(err3.value)
