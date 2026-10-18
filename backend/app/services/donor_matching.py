"""Explainable donor-request matching for live relief operations.

The score combines profile fit, proximity, capacity, completed-delivery
reliability, and donation recency. It is a ranking aid, not a response
probability. A learned ranker can replace it after real outreach outcomes have
been collected at sufficient scale.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Optional

import joblib
import numpy as np
import pandas as pd

from app.models.disaster_donation_request import whole_required_quantity
HYBRID_SCORE_NAME = "Explainable Hybrid Match Score"
XGBOOST_MODEL_FILE = Path(__file__).resolve().parents[2] / "ml_models" / "disaster-donation-request" / "donor_xgboost_model.joblib"


@lru_cache(maxsize=1)
def load_donor_xgboost_package() -> Optional[dict]:
    if not XGBOOST_MODEL_FILE.is_file():
        return None
    try:
        return joblib.load(str(XGBOOST_MODEL_FILE))
    except Exception:
        return None
HYBRID_WEIGHTS = {
    "category": 0.30,
    "proximity": 0.25,
    "capacity": 0.20,
    "reliability": 0.15,
    "recency": 0.10,
}
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


def model_information() -> dict:
    info = {
        "selectedModel": HYBRID_SCORE_NAME,
        "method": "weighted_rule_based",
        "scoreMeaning": "Explainable donor-request match score, not response probability",
        "weights": {name: round(weight * 100) for name, weight in HYBRID_WEIGHTS.items()},
        "futureModel": "CatBoostRanker after sufficient real outreach outcomes are collected",
    }
    xgb_pkg = load_donor_xgboost_package()
    if xgb_pkg:
        info["mlModel"] = {
            "name": xgb_pkg.get("model_name", "XGBoost Donor Matching & Handover Predictor"),
            "algorithm": xgb_pkg.get("algorithm", "XGBClassifier"),
            "version": xgb_pkg.get("version", "1.0.0"),
            "metrics": xgb_pkg.get("metrics", {}),
        }
    return info


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


def _history_factors(history: Iterable[Mapping]) -> tuple[float, float, int, list[str]]:
    records = list(history)
    resolved = [record for record in records if record.get("status") in {"received", "cancelled", "expired"}]
    received = [record for record in resolved if record.get("status") == "received"]
    reliability = len(received) / len(resolved) if resolved else 0.5

    received_dates = []
    for record in received:
        value = record.get("acceptedAt") or record.get("donatedAt")
        if isinstance(value, datetime):
            received_dates.append(value if value.tzinfo else value.replace(tzinfo=timezone.utc))
    if not received_dates:
        recency = 0.5
    else:
        age_days = max(0, (datetime.now(timezone.utc) - max(received_dates)).days)
        if age_days <= 30:
            recency = 1.0
        elif age_days <= 90:
            recency = 0.8
        elif age_days <= 180:
            recency = 0.6
        elif age_days <= 365:
            recency = 0.4
        else:
            recency = 0.2

    warnings_out = []
    if not resolved:
        warnings_out.append("No completed donation history; neutral reliability and recency were used")
    return reliability, recency, len(received), warnings_out


def predict_compatibility(
    donor: Mapping,
    requests: Iterable[Mapping],
    donation_history: Optional[Iterable[Mapping]] = None,
) -> tuple[Optional[float], dict]:
    rows, details = prepare_candidate_rows(donor, requests)
    if not rows:
        return None, details

    weights = np.asarray([max(float(row["required_quantity"]), 1.0) for row in rows], dtype=float)
    category = float(np.average([row["category_match_score"] for row in rows], weights=weights))
    capacity = float(np.average([row["capacity_match_score"] for row in rows], weights=weights))
    proximity = float(rows[0]["proximity_score"])
    history_records = list(donation_history or [])
    reliability, recency, received_count, warnings_out = _history_factors(history_records)

    if details["distanceSource"] == "registered-address estimate":
        warnings_out.append("Distance is a broad address fallback; add coordinates for precise proximity")

    factors = {
        "category": category,
        "proximity": proximity,
        "capacity": capacity,
        "reliability": reliability,
        "recency": recency,
    }

    xgb_pkg = load_donor_xgboost_package()
    scoring_method = HYBRID_SCORE_NAME
    if xgb_pkg and "model" in xgb_pkg:
        try:
            received_dates = []
            for record in history_records:
                if record.get("status") == "received":
                    val = record.get("acceptedAt") or record.get("donatedAt")
                    if isinstance(val, datetime):
                        received_dates.append(val if val.tzinfo else val.replace(tzinfo=timezone.utc))
            days_since_last = float(max(0, (datetime.now(timezone.utc) - max(received_dates)).days)) if received_dates else 90.0

            df_input = pd.DataFrame([
                {
                    "donor_type": row["donor_type"],
                    "preferred_category": row["preferred_category"],
                    "capacity_level": row["capacity_level"],
                    "disaster_type": row["disaster_type"],
                    "severity": row["severity"],
                    "affected_population": row["affected_population"],
                    "required_category": row["required_category"],
                    "distance_km": row["distance_km"],
                    "required_quantity": row["required_quantity"],
                    "category_match_score": row["category_match_score"],
                    "capacity_match_score": row["capacity_match_score"],
                    "proximity_score": row["proximity_score"],
                    "past_fulfillment_rate": float(reliability),
                    "days_since_last_donation": float(days_since_last),
                }
                for row in rows
            ])
            probs = xgb_pkg["model"].predict_proba(df_input)[:, 1]
            score = float(np.average(probs, weights=weights))
            scoring_method = "XGBoost Handover Predictor"
        except Exception:
            score = sum(factors[name] * weight for name, weight in HYBRID_WEIGHTS.items())
            scoring_method = HYBRID_SCORE_NAME
    else:
        score = sum(factors[name] * weight for name, weight in HYBRID_WEIGHTS.items())
        scoring_method = HYBRID_SCORE_NAME

    has_coordinates = details["distanceSource"] == "registered coordinates"
    resolved_count = sum(
        1 for record in history_records
        if record.get("status") in {"received", "cancelled", "expired"}
    )
    confidence = "High" if has_coordinates and resolved_count >= 5 else "Medium" if has_coordinates or resolved_count >= 2 else "Low"
    details.update({
        "priorityScore": round(score, 6),
        "compatibilityScore": round(score * 100, 1),
        "scoringMethod": scoring_method,
        "modelType": "XGBoost" if scoring_method.startswith("XGBoost") else "Hybrid",
        "categoryMatchScore": round(category, 3),
        "capacityMatchScore": round(capacity, 3),
        "proximityScore": round(proximity, 3),
        "reliabilityScore": round(reliability, 3),
        "recencyScore": round(recency, 3),
        "factorScores": {name: round(value * 100, 1) for name, value in factors.items()},
        "confidence": confidence,
        "dataQualityWarnings": warnings_out,
        "receivedHistoryCount": received_count,
    })
    return score, details
