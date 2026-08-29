"""
app/routers/heatmap.py
----------------------
Geospatial risk heatmap aggregation and ML Flood/Landslide inference endpoints.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import joblib
import numpy as np
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_role, get_current_user_payload
from app.database import get_db
from app.models.sos import SOSRequest
from app.models.camp import MedicalCamp

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models"

router = APIRouter(prefix="", tags=["Geospatial & ML Analytics"])

# Load pre-trained models
_flood_model = None
_flood_scaler = None
_landslide_model = None
_landslide_scaler = None
_landslide_encoder = None
_gnd_risk_data = None
_dsd_risk_data = None


def _patch_sklearn_compat(model) -> None:
    """
    Back-fill the ``monotonic_cst`` attribute that sklearn >= 1.4 expects on
    every DecisionTree node but that is absent when a model was serialised
    under sklearn 1.3.x.  The patch is applied in-place and is a no-op when
    the attribute already exists (i.e. models retrained on sklearn >= 1.4).
    """
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

    trees = []
    # Ensemble models expose their individual estimators here
    if hasattr(model, "estimators_"):
        trees = model.estimators_
        if trees and isinstance(trees[0], list):   # multi-output forests
            trees = [t for row in trees for t in row]
    elif isinstance(model, (DecisionTreeClassifier, DecisionTreeRegressor)):
        trees = [model]

    for tree in trees:
        if not hasattr(tree, "monotonic_cst"):
            tree.monotonic_cst = None
        # The compiled Cython Tree object also needs the attribute
        if hasattr(tree, "tree_") and not hasattr(tree.tree_, "monotonic_cst"):
            try:
                tree.tree_.monotonic_cst = None
            except AttributeError:
                pass  # read-only Cython slot – already set internally


def get_ml_models():
    global _flood_model, _flood_scaler, _landslide_model, _landslide_scaler, _landslide_encoder, _gnd_risk_data, _dsd_risk_data
    if _flood_model is None:
        if (MODEL_DIR / "flood_risk_model.joblib").exists():
            _flood_model = joblib.load(MODEL_DIR / "flood_risk_model.joblib")
            _patch_sklearn_compat(_flood_model)
            _flood_scaler = joblib.load(MODEL_DIR / "flood_risk_scaler.joblib")
        if (MODEL_DIR / "landslide_risk_model.joblib").exists():
            _landslide_model = joblib.load(MODEL_DIR / "landslide_risk_model.joblib")
            _patch_sklearn_compat(_landslide_model)
            _landslide_scaler = joblib.load(MODEL_DIR / "landslide_risk_scaler.joblib")
            _landslide_encoder = joblib.load(MODEL_DIR / "landslide_gn_encoder.joblib")
        if (MODEL_DIR / "gnd_landslide_risk_table.json").exists():
            with open(MODEL_DIR / "gnd_landslide_risk_table.json") as f:
                _gnd_risk_data = json.load(f)
        if (MODEL_DIR / "dsd_flood_risk_table.json").exists():
            with open(MODEL_DIR / "dsd_flood_risk_table.json") as f:
                _dsd_risk_data = json.load(f)
    return _flood_model, _flood_scaler, _landslide_model, _landslide_scaler, _landslide_encoder, _gnd_risk_data, _dsd_risk_data


class FloodPredictRequest(BaseModel):
    latitude: float = 6.936
    longitude: float = 79.957
    dist_to_kelani_km: float = 4.5
    boggy_frac: float = 0.08
    water_frac: float = 0.07
    river_level_m: float = 3.5
    rainfall_mm: float = 210.0
    is_kelani_zone: int = 1

class LandslidePredictRequest(BaseModel):
    gn_name: str = "Lakshapana"
    incident_count: int = 4
    total_families: int = 10
    total_people: int = 40
    mean_families: float = 2.5
    mean_people: float = 10.0
    max_people: int = 20
    std_people: float = 3.5
    people_per_family: float = 4.0

@router.get("/heatmap")
def get_heatmap_data(db: Session = Depends(get_db)):
    """Return blended spatial risk points, GN boundaries, active SOS clusters, and camps."""
    _, _, _, _, _, gnd_table, dsd_table = get_ml_models()
    
    # Active SOS coordinates
    active_sos = db.query(SOSRequest).filter(SOSRequest.status == "active").all()
    sos_points = [
        {
            "id": s.id,
            "lat": s.latitude,
            "lng": s.longitude,
            "priority": s.priority_score,
            "people": s.affected_people,
            "district": s.district,
            "gn": s.gn_division,
        }
        for s in active_sos
    ]

    # Medical camps
    camps = db.query(MedicalCamp).all()
    camp_points = [
        {
            "id": c.id,
            "name": c.name,
            "lat": c.latitude,
            "lng": c.longitude,
            "suitability": c.suitability_score,
            "status": c.status,
            "capacity": c.estimated_capacity,
        }
        for c in camps
    ]

    # Default Kaduwela / Kelani reference zones with computed risk levels
    zones = [
        {"name": "Ranala (KAD-001)", "lat": 6.936419, "lng": 79.957216, "hazard": "Flood", "risk_level": "High", "score": 88.5},
        {"name": "Nawagamuwa (KAD-002)", "lat": 6.933356, "lng": 79.968899, "hazard": "Flood", "risk_level": "High", "score": 86.2},
        {"name": "Ihala Bomiriya (KAD-004)", "lat": 6.930782, "lng": 79.985223, "hazard": "Flood", "risk_level": "High", "score": 84.1},
        {"name": "Kaduwela Central (KAD-009)", "lat": 6.923639, "lng": 80.002176, "hazard": "Flood", "risk_level": "High", "score": 91.0},
        {"name": "Malabe East (KAD-014)", "lat": 6.912208, "lng": 79.968664, "hazard": "Flood", "risk_level": "Medium", "score": 62.4},
        {"name": "Athurugiriya (KAD-031)", "lat": 6.917654, "lng": 79.923300, "hazard": "Flood", "risk_level": "Low", "score": 38.0},
        {"name": "Lakshapana (317A)", "lat": 6.905000, "lng": 80.498000, "hazard": "Landslide", "risk_level": "High", "score": 90.7},
        {"name": "Ginigathhena (315A)", "lat": 6.989000, "lng": 80.490000, "hazard": "Landslide", "risk_level": "High", "score": 84.2},
        {"name": "Kalugala (316C)", "lat": 6.920000, "lng": 80.450000, "hazard": "Landslide", "risk_level": "Medium", "score": 66.8},
        {"name": "Pitawala (316D)", "lat": 6.915000, "lng": 80.430000, "hazard": "Landslide", "risk_level": "Medium", "score": 58.3},
    ]

    return {
        "hazard_zones": zones,
        "sos_clusters": sos_points,
        "medical_camps": camp_points,
        "landslide_gnd_table": gnd_table[:15] if gnd_table else [],
        "dsd_flood_table": dsd_table if dsd_table else [],
    }

@router.post("/predict/flood", dependencies=[Depends(require_role(["authority", "admin"]))])
def predict_flood_risk(payload: FloodPredictRequest):
    """Execute Model 1 (Flood RF Classifier) on environmental telemetry."""
    f_model, f_scaler, _, _, _, _, _ = get_ml_models()
    if f_model is None or f_scaler is None:
        raise HTTPException(status_code=503, detail="Flood model artifact is not loaded.")

    try:
        # 12 features
        prox = max(0.0, min(1.0, 1.0 - (payload.dist_to_kelani_km / 15.0)))
        elev = 10.0
        road_dens = 0.25
        builtup = 0.40
        vec = np.array([[
            payload.latitude, payload.longitude, payload.dist_to_kelani_km,
            prox, payload.boggy_frac, payload.water_frac, builtup, road_dens,
            elev, payload.rainfall_mm, payload.river_level_m, payload.is_kelani_zone
        ]])
        scaled = f_scaler.transform(vec)
        pred_class = int(f_model.predict(scaled)[0])
        pred_proba = f_model.predict_proba(scaled)[0].tolist()

        class_map = {0: "Low", 1: "Medium", 2: "High"}
        return {
            "predicted_risk_tier": class_map.get(pred_class, "Medium"),
            "risk_tier_code": pred_class,
            "probabilities": {
                "Low": round(pred_proba[0], 4),
                "Medium": round(pred_proba[1], 4),
                "High": round(pred_proba[2], 4),
            },
            "proxy_label_notice": "Evaluated using heuristic proxy model (Proposal Sec 8.2)",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference error: {str(e)}")

@router.post("/predict/landslide", dependencies=[Depends(require_role(["authority", "admin"]))])
def predict_landslide_risk(payload: LandslidePredictRequest):
    """Execute Model 2 (Landslide RF Classifier) on GN Division historical and exposure stats."""
    _, _, l_model, l_scaler, l_encoder, _, _ = get_ml_models()
    if l_model is None or l_scaler is None:
        raise HTTPException(status_code=503, detail="Landslide model artifact is not loaded.")

    try:
        # Calculate severity score
        sev = (
            0.4 * (payload.total_people / 73.0) +
            0.3 * (payload.incident_count / 15.0) +
            0.2 * (payload.total_families / 16.0) +
            0.1 * (payload.max_people / 73.0)
        ) * 100

        gn_code = 0
        if l_encoder is not None:
            try:
                gn_code = int(l_encoder.transform([payload.gn_name])[0])
            except Exception:
                gn_code = 0

        vec = np.array([[
            gn_code,
            payload.incident_count,
            payload.total_families,
            payload.total_people,
            payload.mean_families,
            payload.mean_people,
            payload.max_people,
            payload.std_people,
            payload.people_per_family,
            sev,
        ]])
        scaled = l_scaler.transform(vec)
        pred_class = int(l_model.predict(scaled)[0])
        pred_proba = l_model.predict_proba(scaled)[0].tolist()

        class_map = {0: "Low", 1: "Medium", 2: "High"}
        return {
            "gn_name": payload.gn_name,
            "predicted_risk_tier": class_map.get(pred_class, "Medium"),
            "risk_tier_code": pred_class,
            "severity_score": round(sev, 2),
            "probabilities": {
                "Low": round(pred_proba[0], 4),
                "Medium": round(pred_proba[1], 4),
                "High": round(pred_proba[2], 4),
            },
            "data_provenance": "Trained on real NBRO historical records (257 incidents)",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference error: {str(e)}")


class CampPredictRequest(BaseModel):
    latitude: float = 6.947
    longitude: float = 80.012
    dist_to_road_km: float = 1.2
    dist_to_hospital_km: float = 4.5
    population_5km: int = 12000
    elevation_m: int = 145


class PriorityPredictRequest(BaseModel):
    urgency_level: int = 4
    affected_people: int = 25
    has_vulnerable: int = 1
    hours_since_alert: float = 3.0
    has_medical_emergency: int = 1
    district_risk_tier: int = 3


_camp_model = None
_camp_scaler = None
_priority_model = None
_priority_scaler = None

def get_camp_and_priority_models():
    global _camp_model, _camp_scaler, _priority_model, _priority_scaler
    if _camp_model is None:
        if (MODEL_DIR / "camp_suitability_model.joblib").exists():
            _camp_model = joblib.load(MODEL_DIR / "camp_suitability_model.joblib")
            _patch_sklearn_compat(_camp_model)
            _camp_scaler = joblib.load(MODEL_DIR / "camp_suitability_scaler.joblib")
        if (MODEL_DIR / "priority_score_model.joblib").exists():
            _priority_model = joblib.load(MODEL_DIR / "priority_score_model.joblib")
            _patch_sklearn_compat(_priority_model)
            _priority_scaler = joblib.load(MODEL_DIR / "priority_score_scaler.joblib")
    return _camp_model, _camp_scaler, _priority_model, _priority_scaler


@router.post("/predict/camp", dependencies=[Depends(require_role(["authority", "admin", "donor", "volunteer", "victim"]))])
def predict_camp_suitability(payload: CampPredictRequest):
    """Execute Model 3 (Camp Suitability Scorer) on candidate coordinates and infrastructure parameters."""
    c_model, c_scaler, _, _ = get_camp_and_priority_models()
    if c_model is None or c_scaler is None:
        raise HTTPException(status_code=503, detail="Camp suitability model artifact is not loaded.")

    try:
        # 10 features: lat, lng, dist_road, dist_hosp, pop_density, flood_safe, road_access, med_proximity, water_access, comms_access
        flood_safe = 0.85
        road_acc = max(0.1, min(1.0, 1.0 - (payload.dist_to_road_km / 10.0)))
        med_prox = max(0.1, min(1.0, 1.0 - (payload.dist_to_hospital_km / 20.0)))
        water_acc = 0.9
        comms_acc = 0.85
        pop_dens = min(1.0, payload.population_5km / 20000.0)

        vec = np.array([[
            payload.latitude, payload.longitude, payload.dist_to_road_km,
            payload.dist_to_hospital_km, pop_dens, flood_safe, road_acc,
            med_prox, water_acc, comms_acc
        ]])
        scaled = c_scaler.transform(vec)
        score = float(c_model.predict(scaled)[0])
        score = max(0.0, min(100.0, score))

        tier = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
        return {
            "suitability_score": round(score, 2),
            "score": round(score, 2),
            "tier": tier,
            "accessibility_factor": round(road_acc, 2),
            "medical_proximity_factor": round(med_prox, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Camp inference error: {str(e)}")


@router.post("/predict/priority", dependencies=[Depends(require_role(["authority", "admin", "donor", "volunteer", "victim"]))])
def predict_priority_score(payload: PriorityPredictRequest):
    """Execute Model 4 (SOS Priority Scorer) on incident parameters."""
    _, _, p_model, p_scaler = get_camp_and_priority_models()
    if p_model is None or p_scaler is None:
        raise HTTPException(status_code=503, detail="Priority score model artifact is not loaded.")

    try:
        # 11 features: urgency, affected_people, affected_families, has_elderly, has_children,
        # has_disabled, medical_needs_count, flood_risk_score, landslide_risk_score, hours_since_sos, access_difficulty
        aff_fam = max(1, payload.affected_people // 4)
        has_eld = 1.0 if payload.has_vulnerable == 1 else 0.0
        has_chi = 1.0 if payload.has_vulnerable == 1 else 0.0
        has_dis = 1.0 if payload.has_vulnerable == 1 else 0.0
        med_cnt = 2.0 if payload.has_medical_emergency == 1 else 0.0
        flood_risk = 0.8 if payload.district_risk_tier == 3 else 0.5 if payload.district_risk_tier == 2 else 0.2
        land_risk = 0.7 if payload.district_risk_tier == 3 else 0.4 if payload.district_risk_tier == 2 else 0.1
        acc_diff = 0.6 if payload.district_risk_tier == 3 else 0.3

        vec = np.array([[
            float(payload.urgency_level), float(payload.affected_people), float(aff_fam),
            has_eld, has_chi, has_dis, med_cnt, flood_risk, land_risk,
            float(payload.hours_since_alert), acc_diff
        ]])
        scaled = p_scaler.transform(vec)
        score = float(p_model.predict(scaled)[0])
        score = max(0.0, min(100.0, score))

        tier = "Critical" if score >= 85 else "High" if score >= 70 else "Medium" if score >= 50 else "Low"
        return {
            "priority_score": round(score, 2),
            "score": round(score, 2),
            "tier": tier,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Priority inference error: {str(e)}")
