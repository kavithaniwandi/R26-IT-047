"""Inference for the trained donor-request compatibility pipeline.

The serialized sklearn Pipeline is the source of truth for column order,
one-hot encoding and the Linear Regression model.  This module only prepares
live donor/request records for that pipeline; it never fits or replaces the
supplied estimator.
"""
from __future__ import annotations

import csv
import math
import warnings
from collections import UserList
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Optional

import joblib
import numpy as np

from app.models.disaster_donation_request import whole_required_quantity
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning


MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models"
MODEL_PATH = MODEL_DIR / "donor_matching_pipeline.joblib"
EVALUATION_PATH = MODEL_DIR / "donor_model_comparison.csv"

MODEL_NAME = "Linear Regression"
EXPECTED_FEATURES = [
    "donor_type",
    "preferred_category",
    "capacity_level",
    "disaster_type",
    "severity",
    "affected_population",
    "required_category",
    "distance_km",
    "required_quantity",
    "category_match_score",
    "capacity_match_score",
    "proximity_score",
]

DONOR_TYPES = {"Business", "Hospital", "Individual", "NGO", "Organization", "Pharmacy"}
DONATION_CATEGORIES = {"Blankets", "Dry Rations", "Medical", "Multiple", "Tarpaulins", "Water"}
CAPACITY_LEVELS = {"Low", "Medium", "High"}


class DonorModelUnavailable(RuntimeError):
    """Raised when the supplied model artifact cannot be loaded safely."""


@lru_cache(maxsize=1)
def load_pipeline():
    if not MODEL_PATH.exists():
        raise DonorModelUnavailable(f"Donor matching model is missing: {MODEL_PATH.name}")
    try:
        # The supplied artifact was produced by sklearn 1.6.1. The rest of this
        # repository's artifacts require 1.7.2, where this private pickle-only
        # list class was removed. Re-introducing the data container allows the
        # original fitted pipeline to load without changing any estimator state.
        import sklearn.compose._column_transformer as column_transformer

        if not hasattr(column_transformer, "_RemainderColsList"):
            class _RemainderColsList(UserList):
                def __init__(self, columns, **state):
                    super().__init__(columns)
                    self.__dict__.update(state)

            _RemainderColsList.__module__ = column_transformer.__name__
            setattr(column_transformer, "_RemainderColsList", _RemainderColsList)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            pipeline = joblib.load(MODEL_PATH)
    except Exception as exc:  # pragma: no cover - exact joblib/sklearn error varies
        raise DonorModelUnavailable(
            "The donor matching pipeline could not be loaded with the backend dependencies."
        ) from exc

    artifact_features = list(getattr(pipeline, "feature_names_in_", []))
    if artifact_features != EXPECTED_FEATURES:
        raise DonorModelUnavailable(
            f"Unexpected donor model features: {artifact_features or 'not recorded'}"
        )
    return pipeline


@lru_cache(maxsize=1)
def model_information() -> dict:
    rows: list[dict] = []
    if EVALUATION_PATH.exists():
        with EVALUATION_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append({
                    "model": row["Model"],
                    "r2": float(row["R2"]),
                    "mae": float(row["MAE"]),
                    "rmse": float(row["RMSE"]),
                })
    selected = next((row for row in rows if row["model"] == MODEL_NAME), None)
    if selected is None:
        raise DonorModelUnavailable("Linear Regression metrics are missing from the evaluation file")
    return {
        "selectedModel": MODEL_NAME,
        "target": "priority_score",
        "scoreMeaning": "Synthetic donor-request compatibility, not response probability",
        "features": EXPECTED_FEATURES,
        "metrics": selected,
        "comparison": sorted(rows, key=lambda row: row["r2"], reverse=True),
    }


def _normalise(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _canonical(value: object, allowed: set[str]) -> Optional[str]:
    key = _normalise(value)
    return next((candidate for candidate in allowed if candidate.casefold() == key), None)


def required_category(item: Mapping) -> Optional[str]:
    explicit = _canonical(
        item.get("requiredCategory") or item.get("category"),
        DONATION_CATEGORIES - {"Multiple"},
    )
    if explicit:
        return explicit

    name = _normalise(item.get("itemName"))
    if any(token in name for token in ("water", "litre", "liter")):
        return "Water"
    if any(token in name for token in ("ration", "food", "meal", "rice", "milk", "formula")):
        return "Dry Rations"
    if "blanket" in name:
        return "Blankets"
    if any(token in name for token in ("tarpaulin", "tent", "sheet")):
        return "Tarpaulins"
    if any(token in name for token in (
        "medicine", "medical", "insulin", "saline", "tablet", "capsule", "syringe",
        "bandage", "first aid", "stretcher", "sanitary", "hygiene",
    )):
        return "Medical"
    return None


def proximity_score(distance_km: float) -> float:
    """Apply the exact distance bands recorded in the workbook Scoring_Rules sheet."""
    if distance_km <= 5:
        return 1.0
    if distance_km <= 15:
        return 0.9
    if distance_km <= 30:
        return 0.75
    if distance_km <= 60:
        return 0.55
    if distance_km <= 100:
        return 0.35
    return 0.15


def category_match_score(preferred_category: str, category: str) -> float:
    """Use production-safe deterministic values from the workbook scoring rules."""
    if preferred_category == category:
        return 1.0
    if preferred_category == "Multiple":
        return 0.9
    # The workbook used random 0-.15 variation for synthetic mismatches. Random
    # noise is intentionally not generated during live inference.
    return 0.0


def capacity_match_score(capacity_level: str, required_quantity: float) -> float:
    """Convert the workbook's capacity level + demand rule to a stable live feature.

    Training data contains no physical maximum-capacity field.  Its documented
    Low/Medium/High bands are therefore combined with request demand tiers.  No
    synthetic noise is introduced at inference time.
    """
    if required_quantity <= 250:
        scores = {"Low": 0.9, "Medium": 1.0, "High": 1.0}
    elif required_quantity <= 1000:
        scores = {"Low": 0.55, "Medium": 0.9, "High": 1.0}
    else:
        scores = {"Low": 0.3, "Medium": 0.6, "High": 0.9}
    return scores[capacity_level]


def _float(value: object) -> Optional[float]:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def donor_distance(donor: Mapping, requests: Iterable[Mapping]) -> tuple[Optional[float], str]:
    request_list = list(requests)
    donor_lat = _float(donor.get("latitude") or donor.get("lat"))
    donor_lon = _float(donor.get("longitude") or donor.get("lng"))
    request_points = [
        (_float(request.get("latitude") or request.get("lat")), _float(request.get("longitude") or request.get("lng")))
        for request in request_list
    ]
    request_points = [(lat, lon) for lat, lon in request_points if lat is not None and lon is not None]
    if donor_lat is not None and donor_lon is not None and request_points:
        target_lat = sum(point[0] for point in request_points) / len(request_points)
        target_lon = sum(point[1] for point in request_points) / len(request_points)
        return round(_haversine_km(donor_lat, donor_lon, target_lat, target_lon), 3), "registered coordinates"

    # Legacy records contain administrative addresses rather than coordinates.
    # The bounds correspond to the workbook's proximity bands and are surfaced
    # to the UI as estimates, never as GPS measurements.
    address = _normalise(donor.get("address"))
    gn = _normalise(request_list[0].get("gnDivision")) if request_list else ""
    ds = _normalise(request_list[0].get("dsArea")) if request_list else ""
    if address and gn and gn in address:
        return 5.0, "GN-division address estimate"
    if address and ds and ds in address:
        return 15.0, "DS-area address estimate"
    if address:
        return 100.0, "registered-address estimate"
    return None, "location unavailable"


def prepare_candidate_rows(donor: Mapping, requests: Iterable[Mapping]) -> tuple[list[dict], dict]:
    request_list = list(requests)
    donor_type = _canonical(donor.get("donor_type") or donor.get("donorType"), DONOR_TYPES)
    preferred = _canonical(
        donor.get("preferred_category")
        or donor.get("preferredCategory")
        or donor.get("preferred_donation_category"),
        DONATION_CATEGORIES,
    )
    capacity = _canonical(donor.get("capacity_level") or donor.get("capacityLevel"), CAPACITY_LEVELS)
    distance, distance_source = donor_distance(donor, request_list)

    missing = []
    if donor_type is None:
        missing.append("donor type")
    if preferred is None:
        missing.append("preferred category")
    if capacity is None:
        missing.append("capacity level")
    if distance is None:
        missing.append("registered location")
    if not request_list:
        missing.append("request data")
    if missing:
        return [], {"eligible": False, "missing": missing, "distanceSource": distance_source}

    affected_population = sum(max(0, int(request.get("people_count") or 0)) for request in request_list)
    severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
    severity = max(
        (_canonical(request.get("severity"), set(severity_rank)) or "Moderate" for request in request_list),
        key=lambda value: severity_rank[value],
    )
    disaster_type = str(request_list[0].get("disasterType") or "Flood")

    quantities: dict[str, float] = {}
    for request in request_list:
        for item in request.get("items", []):
            category = required_category(item)
            remaining = _float(item.get("remainingQuantity"))
            if remaining is None:
                remaining = max(
                    0.0,
                    float(whole_required_quantity(item.get("neededQuantity") or 0))
                    - float(item.get("pledgedQuantity") or 0)
                    - float(item.get("donatedQuantity") or 0),
                )
            if category and remaining > 0:
                quantities[category] = quantities.get(category, 0.0) + remaining

    rows = []
    for category, quantity in quantities.items():
        rows.append({
            "donor_type": donor_type,
            "preferred_category": preferred,
            "capacity_level": capacity,
            "disaster_type": disaster_type,
            "severity": severity,
            "affected_population": affected_population,
            "required_category": category,
            "distance_km": distance,
            "required_quantity": quantity,
            "category_match_score": category_match_score(preferred, category),
            "capacity_match_score": capacity_match_score(capacity, quantity),
            "proximity_score": proximity_score(distance),
        })

    if not rows:
        return [], {
            "eligible": False,
            "missing": ["a supported open request category"],
            "distanceSource": distance_source,
        }
    return rows, {
        "eligible": True,
        "missing": [],
        "distanceKm": distance,
        "distanceSource": distance_source,
        "donorType": donor_type,
        "preferredCategory": preferred,
        "capacityLevel": capacity,
    }


def predict_compatibility(donor: Mapping, requests: Iterable[Mapping]) -> tuple[Optional[float], dict]:
    rows, details = prepare_candidate_rows(donor, requests)
    if not rows:
        return None, details

    frame = pd.DataFrame(rows, columns=EXPECTED_FEATURES)
    predictions = np.clip(load_pipeline().predict(frame), 0.0, 1.0)
    weights = np.asarray([max(float(row["required_quantity"]), 1.0) for row in rows], dtype=float)
    score = float(np.average(predictions, weights=weights))
    details.update({
        "priorityScore": round(score, 6),
        "compatibilityScore": round(score * 100, 1),
        "categoryScores": [
            {
                "category": row["required_category"],
                "requiredQuantity": row["required_quantity"],
                "score": round(float(prediction), 6),
            }
            for row, prediction in zip(rows, predictions)
        ],
        "categoryMatchScore": round(max(row["category_match_score"] for row in rows), 3),
        "capacityMatchScore": round(float(np.average(
            [row["capacity_match_score"] for row in rows], weights=weights
        )), 3),
        "proximityScore": rows[0]["proximity_score"],
    })
    return score, details
