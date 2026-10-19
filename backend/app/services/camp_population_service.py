"""
backend/app/services/camp_population_service.py
------------------------------------------------
Machine-learning inference service for next-hour relief camp population forecasting.
Loads and caches the trained Random Forest model (camp_population_rf_model.joblib).
Constructs the exact 15-feature inference DataFrame and calculates predicted demand,
expected sheltered population, overflow risk, and capacity status.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
import logging
import warnings

import joblib
import pandas as pd
import httpx

logger = logging.getLogger(__name__)

# Sri Lanka standard time is UTC+05:30
SRI_LANKA_TZ = timezone(timedelta(hours=5, minutes=30))

# Exact 15 features required by the trained Random Forest model
MODEL_FEATURE_NAMES = [
    "max_capacity",
    "pop_t_minus_4",
    "pop_t_minus_3",
    "pop_t_minus_2",
    "pop_t_minus_1",
    "pop_t",
    "rainfall_mm",
    "rainfall_3h_avg_mm",
    "temperature_c",
    "humidity_pct",
    "river_level_m",
    "river_level_change_m",
    "population_change_1h",
    "population_change_3h",
    "hour_of_day",
]

BACKEND_DIR = Path(__file__).resolve().parents[2]


def find_model_path() -> Path:
    """Locate camp_population_rf_model.joblib across supported paths."""
    candidates = [
        BACKEND_DIR / "ml_models" / "disaster-donation-request" / "camp_population_rf_model.joblib",
        BACKEND_DIR / "md_models" / "disaster-donation-request" / "camp_population_rf_model.joblib",
        Path("ml_models/disaster-donation-request/camp_population_rf_model.joblib"),
        Path("md_models/disaster-donation-request/camp_population_rf_model.joblib"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    # Fallback search if moved
    for found in BACKEND_DIR.glob("**/camp_population_rf_model.joblib"):
        if found.is_file():
            return found.resolve()
    raise FileNotFoundError(
        "camp_population_rf_model.joblib not found in ml_models/disaster-donation-request or md_models/disaster-donation-request"
    )


@lru_cache(maxsize=1)
def load_population_rf_package() -> Dict[str, Any]:
    """
    Load the trained Random Forest model package once and cache the instance in memory.
    The joblib contains: model, features, model_name, target, version, metrics.
    """
    model_path = find_model_path()
    logger.info("Loading Camp Population Random Forest model from %s", model_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        package = joblib.load(str(model_path))

    if not isinstance(package, dict):
        raise ValueError(f"Expected dict package in joblib, got {type(package)}")

    if "model" not in package or "features" not in package:
        raise ValueError("Model package missing required 'model' or 'features' keys")

    features = list(package.get("features", []))
    if features != MODEL_FEATURE_NAMES:
        logger.warning(
            "Package features (%s) differ from expected features (%s)",
            features,
            MODEL_FEATURE_NAMES,
        )

    return package


def warm_up_population_model() -> None:
    """Pre-warm model during backend startup."""
    try:
        pkg = load_population_rf_package()
        logger.info(
            "Camp Population RF Model pre-warmed successfully: %s v%s (%d features)",
            pkg.get("model_name", "Random Forest"),
            pkg.get("version", "1.0"),
            len(pkg.get("features", [])),
        )
    except Exception as exc:
        logger.error("Failed to pre-warm Camp Population RF Model: %s", exc)
        raise


async def fetch_live_kelani_environment() -> Dict[str, Any]:
    """
    Retrieve live Kaduwela weather and Hanwella river gauge data from existing public telemetry APIs.
    Preserves and reuses the existing Open-Meteo and Hanwella telemetry data sources.
    """
    weather_url = "https://api.open-meteo.com/v1/forecast"
    river_url = "https://slwaterlevel.mevinu.com/api/gauges/Hanwella"
    weather_params = {
        "latitude": 6.9344,
        "longitude": 79.9830,
        "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation,rain",
        "hourly": "precipitation",
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "Asia/Colombo",
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        import asyncio
        weather_result, river_result = await asyncio.gather(
            client.get(weather_url, params=weather_params),
            client.get(river_url),
            return_exceptions=True,
        )

    weather_data: Dict[str, Any] = {"available": False}
    rain_history: List[float] = []

    if not isinstance(weather_result, Exception) and weather_result.is_success:
        try:
            payload = weather_result.json()
            current = payload.get("current", {})
            hourly = payload.get("hourly", {})
            times = hourly.get("time", [])
            precipitation = hourly.get("precipitation", [])
            current_time = current.get("time", "")
            current_hour = f"{current_time[:13]}:00" if current_time else ""
            current_index = max(
                (index for index, value in enumerate(times) if value <= current_hour),
                default=len(precipitation) - 1,
            )
            rain_history = [
                round(float(precipitation[index] or 0.0), 1)
                for index in range(current_index, max(-1, current_index - 7), -1)
            ]
            weather_data = {
                "available": True,
                "temperatureC": current.get("temperature_2m"),
                "humidityPercent": current.get("relative_humidity_2m"),
                "precipitationMm": current.get("precipitation", current.get("rain", 0.0)),
                "weatherCode": current.get("weather_code"),
                "observedAt": current_time,
                "source": "Open-Meteo",
            }
        except Exception as exc:
            logger.warning("Error parsing Open-Meteo weather response: %s", exc)

    river_data: Dict[str, Any] = {
        "available": False,
        "station": "Hanwella",
        "basin": "Kelani Ganga",
        "source": "Sri Lanka Flood Monitor / Irrigation telemetry",
    }

    if not isinstance(river_result, Exception) and river_result.is_success:
        try:
            payload = river_result.json()
            river_data.update({
                "available": True,
                "levelM": payload.get("water_level"),
                "status": payload.get("status"),
                "rateOfRiseMPerHour": payload.get("rate_of_rise"),
                "isRising": payload.get("is_rising"),
                "alertLevelM": payload.get("alertpull"),
                "observedAt": payload.get("last_updated_time"),
            })
        except Exception as exc:
            logger.warning("Error parsing Hanwella river gauge response: %s", exc)

    return {
        "location": "Kaduwela / Kelani River basin",
        "weather": weather_data,
        "rainHistory": rain_history,
        "river": river_data,
        "fetchedAt": datetime.now(timezone.utc),
    }


def predict_camp_population_rf(
    *,
    max_capacity: int,
    hourly_observations: List[int],
    rainfall_mm: float,
    rainfall_3h_avg_mm: float,
    temperature_c: float,
    humidity_pct: float,
    river_level_m: float,
    river_level_change_m: float,
    hour_of_day: Optional[int] = None,
    observation_timestamps: Optional[List[datetime]] = None,
) -> Dict[str, Any]:
    """
    Execute next-hour population prediction using the trained Random Forest model.

    Validation rules:
    - max_capacity must be > 0.
    - Exactly 5 or more hourly population observations are required (uses the latest 5 in chronological order).
    - Population values must be non-negative.
    - Environmental values must be valid floats and not None (never silently invented as zero).

    Feature vector constructed in exact training order:
    ['max_capacity', 'pop_t_minus_4', 'pop_t_minus_3', 'pop_t_minus_2', 'pop_t_minus_1', 'pop_t',
     'rainfall_mm', 'rainfall_3h_avg_mm', 'temperature_c', 'humidity_pct', 'river_level_m',
     'river_level_change_m', 'population_change_1h', 'population_change_3h', 'hour_of_day']
    """
    if max_capacity <= 0:
        raise ValueError(f"Maximum capacity must be positive; got {max_capacity}")

    if len(hourly_observations) < 5:
        raise ValueError(
            f"Five real hourly population observations are required for forecasting; got {len(hourly_observations)}"
        )

    # Use the latest 5 observations in chronological order
    recent_5 = hourly_observations[-5:]
    for val in recent_5:
        if val < 0:
            raise ValueError(f"Population observations cannot be negative; got {val}")

    pop_t_minus_4 = float(recent_5[0])
    pop_t_minus_3 = float(recent_5[1])
    pop_t_minus_2 = float(recent_5[2])
    pop_t_minus_1 = float(recent_5[3])
    pop_t = float(recent_5[4])

    # Trend calculations
    population_change_1h = pop_t - pop_t_minus_1
    population_change_3h = pop_t - pop_t_minus_3

    # Local hour of day (Asia/Colombo)
    if hour_of_day is None:
        if observation_timestamps and len(observation_timestamps) >= 5:
            latest_ts = observation_timestamps[-1]
            if latest_ts.tzinfo is None:
                latest_ts = latest_ts.replace(tzinfo=timezone.utc)
            hour_of_day = latest_ts.astimezone(SRI_LANKA_TZ).hour
        else:
            hour_of_day = datetime.now(SRI_LANKA_TZ).hour

    if not (0 <= hour_of_day <= 23):
        raise ValueError(f"hour_of_day must be between 0 and 23; got {hour_of_day}")

    # Validate environmental values
    env_inputs = {
        "rainfall_mm": rainfall_mm,
        "rainfall_3h_avg_mm": rainfall_3h_avg_mm,
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "river_level_m": river_level_m,
        "river_level_change_m": river_level_change_m,
    }
    for name, val in env_inputs.items():
        if val is None or not (isinstance(val, (int, float)) and not pd.isna(val)):
            raise ValueError(f"Forecasting input unavailable: required environmental feature '{name}' is missing or invalid")

    package = load_population_rf_package()
    model = package["model"]
    features_list = package["features"]

    input_data = {
        "max_capacity": float(max_capacity),
        "pop_t_minus_4": pop_t_minus_4,
        "pop_t_minus_3": pop_t_minus_3,
        "pop_t_minus_2": pop_t_minus_2,
        "pop_t_minus_1": pop_t_minus_1,
        "pop_t": pop_t,
        "rainfall_mm": float(rainfall_mm),
        "rainfall_3h_avg_mm": float(rainfall_3h_avg_mm),
        "temperature_c": float(temperature_c),
        "humidity_pct": float(humidity_pct),
        "river_level_m": float(river_level_m),
        "river_level_change_m": float(river_level_change_m),
        "population_change_1h": float(population_change_1h),
        "population_change_3h": float(population_change_3h),
        "hour_of_day": int(hour_of_day),
    }

    # Construct DataFrame with exact ordered columns
    input_df = pd.DataFrame([input_data], columns=features_list)

    # Model inference
    raw_prediction = float(model.predict(input_df)[0])
    predicted_population = max(0, int(round(raw_prediction)))

    # Separate concepts: Sheltered, predicted demand, max capacity, expected sheltered, and overflow
    expected_sheltered = min(predicted_population, max_capacity)
    overflow = max(0, predicted_population - max_capacity)
    status = "OVERFLOW_RISK" if overflow > 0 else "WITHIN_CAPACITY"

    delta = int(predicted_population - pop_t)
    occupancy_percent = round((predicted_population / max_capacity) * 100, 1) if max_capacity > 0 else 0.0

    if overflow > 0:
        note = (
            f"OVERFLOW RISK: Predicted demand of {predicted_population} people exceeds camp capacity of "
            f"{max_capacity} by {overflow} people (+{delta} from current {int(pop_t)}). Coordinate with divisional relief office for overflow shelters."
        )
    elif occupancy_percent >= 85:
        note = (
            f"HIGH OCCUPANCY: Predicted intake reaches {occupancy_percent}% of camp capacity ({predicted_population}/{max_capacity}). "
            f"Request additional ration supply units immediately."
        )
    else:
        note = (
            f"WITHIN CAPACITY: Projected intake of {predicted_population} people remains manageable within "
            f"the {max_capacity} capacity limit (margin: {max_capacity - predicted_population})."
        )

    # Projected multi-hour progression trajectory (1h to 6h)
    projected_hourly = []
    current_proj = float(pop_t)
    hourly_step = (predicted_population - pop_t)
    for h in range(1, 7):
        if h == 1:
            est_val = predicted_population
        else:
            # Dampened extrapolation for subsequent hours
            damping = 0.85 ** (h - 1)
            est_val = max(0, int(round(predicted_population + hourly_step * damping * (h - 1))))
        projected_hourly.append({
            "hour": f"+{h}h",
            "estimatedPeople": est_val,
            "occupancyPercent": round((est_val / max_capacity) * 100, 1) if max_capacity > 0 else 0.0,
            "overflow": max(0, est_val - max_capacity),
        })

    now_utc = datetime.now(timezone.utc)
    forecast_for_utc = now_utc + timedelta(hours=1)
    if observation_timestamps and len(observation_timestamps) >= 5:
        latest_obs_time = observation_timestamps[-1]
        if latest_obs_time.tzinfo is None:
            latest_obs_time = latest_obs_time.replace(tzinfo=timezone.utc)
        forecast_for_utc = latest_obs_time + timedelta(hours=1)

    return {
        "currentPopulation": int(pop_t),
        "predictedPopulation": predicted_population,
        "maxCapacity": max_capacity,
        "expectedSheltered": expected_sheltered,
        "overflow": overflow,
        "status": status,
        "delta": delta,
        "occupancyPercent": occupancy_percent,
        "forecastFor": forecast_for_utc,
        "predictionGeneratedAt": now_utc,
        "projectedHourly": projected_hourly,
        "note": note,
        "observationsUsed": [int(x) for x in recent_5],
        "environmentalConditions": {
            "rainfallMm": rainfall_mm,
            "rainfall3hAvgMm": rainfall_3h_avg_mm,
            "temperatureC": temperature_c,
            "humidityPercent": humidity_pct,
            "riverLevelM": river_level_m,
            "riverLevelChangeM": river_level_change_m,
            "hourOfDay": hour_of_day,
        },
        "modelMetadata": {
            "modelName": package.get("model_name", "Random Forest Regressor"),
            "version": package.get("version", "1.0"),
            "target": package.get("target", "next_hour_population"),
            "features": features_list,
        },
        "factors": {
            "maxCapacity": max_capacity,
            "populationChange1h": population_change_1h,
            "populationChange3h": population_change_3h,
            "rainfallMm": rainfall_mm,
            "recentRainfallMm": round(rainfall_3h_avg_mm, 1),
            "rainfall3hAvgMm": round(rainfall_3h_avg_mm, 1),
            "riverLevelM": round(river_level_m, 2),
            "riverLevelChangeM": round(river_level_change_m, 3),
            "temperatureC": temperature_c,
            "humidityPercent": humidity_pct,
            "hourOfDay": hour_of_day,
            "overflow": overflow,
            "status": status,
        },
    }
