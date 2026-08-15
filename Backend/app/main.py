from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import joblib
import os

from . import models, logic
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Disaster Relief API")

# Allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load trained models if they exist yet (they won't on day 1 -- that's fine)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
landslide_bundle = None
flood_bundle = None
try:
    landslide_bundle = joblib.load(os.path.join(MODEL_DIR, "landslide_model.pkl"))
except FileNotFoundError:
    pass
try:
    flood_bundle = joblib.load(os.path.join(MODEL_DIR, "flood_model.pkl"))
except FileNotFoundError:
    pass


# ---------- request/response shapes ----------

class SOSRequestIn(BaseModel):
    user_id: int | None = None
    disaster_type: str
    lat: float
    lng: float
    num_affected: int = 1
    has_children: bool = False
    has_elderly: bool = False
    has_injured: bool = False
    needed_item: str = "food"


class TerrainFeatures(BaseModel):
    elevation: float
    slope: float
    avg_rainfall: float
    rainfall_7d: float


# ---------- SOS component ----------

@app.post("/sos")
def create_sos(payload: SOSRequestIn, db: Session = Depends(get_db)):
    # find nearest risk zone to get its current live_risk_score for priority scoring
    zones = db.query(models.RiskZone).filter(
        models.RiskZone.disaster_type == payload.disaster_type).all()
    nearest_risk = 0.5  # neutral default if no zone data yet
    if zones:
        nearest = min(zones, key=lambda z: logic.haversine_km(payload.lat, payload.lng, z.lat, z.lng))
        nearest_risk = nearest.live_risk_score or nearest.base_risk_score or 0.5

    score = logic.priority_score(payload.num_affected, payload.has_children,
                                  payload.has_elderly, payload.has_injured, nearest_risk)

    sos = models.SOSRequest(
        user_id=payload.user_id, disaster_type=payload.disaster_type,
        lat=payload.lat, lng=payload.lng, num_affected=payload.num_affected,
        has_children=payload.has_children, has_elderly=payload.has_elderly,
        has_injured=payload.has_injured, needed_item=payload.needed_item,
        priority_score=score,
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)

    # refresh the nearest zone's live heatmap score using this new SOS as a signal
    if zones:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = db.query(models.SOSRequest).filter(
            models.SOSRequest.disaster_type == payload.disaster_type,
            models.SOSRequest.created_at >= one_hour_ago).count()
        nearest.live_risk_score = logic.update_heatmap(
            nearest.base_risk_score or 0.5, recent_count, payload.num_affected)
        db.commit()

    return {"id": sos.id, "priority_score": sos.priority_score, "status": sos.status}


@app.get("/sos/queue")
def get_priority_queue(db: Session = Depends(get_db)):
    """Response-team view: open SOS requests sorted by urgency."""
    requests_ = db.query(models.SOSRequest).filter(
        models.SOSRequest.status == "open").order_by(models.SOSRequest.priority_score.desc()).all()
    return requests_


@app.post("/sos/{sos_id}/match_donor")
def match_donor_for_sos(sos_id: int, db: Session = Depends(get_db)):
    sos = db.query(models.SOSRequest).filter(models.SOSRequest.id == sos_id).first()
    if not sos:
        raise HTTPException(404, "SOS request not found")
    donors = db.query(models.Donor).all()
    match = logic.match_donor(sos.lat, sos.lng, sos.needed_item, donors)
    if not match:
        return {"matched": False}
    sos.status = "matched"
    db.commit()
    return {"matched": True, "donor_id": match.id, "donor_name": match.name}


# ---------- heatmap / risk zones ----------

@app.get("/heatmap/{disaster_type}")
def get_heatmap(disaster_type: str, db: Session = Depends(get_db)):
    zones = db.query(models.RiskZone).filter(models.RiskZone.disaster_type == disaster_type).all()
    return zones


# ---------- ML prediction endpoints ----------

@app.post("/predict/landslide")
def predict_landslide(features: TerrainFeatures):
    if landslide_bundle is None:
        raise HTTPException(503, "Landslide model not trained yet -- run ml/train_landslide.py first")
    model, feat_names = landslide_bundle["model"], landslide_bundle["features"]
    row = [[getattr(features, f) for f in feat_names]]
    prob = model.predict_proba(row)[0][1]
    return {"risk_score": round(float(prob), 3)}


@app.post("/predict/flood")
def predict_flood(features: TerrainFeatures):
    if flood_bundle is None:
        raise HTTPException(503, "Flood model not trained yet -- run ml/train_flood.py first")
    model, feat_names = flood_bundle["model"], flood_bundle["features"]
    row = [[getattr(features, f) for f in feat_names]]
    prob = model.predict_proba(row)[0][1]
    return {"risk_score": round(float(prob), 3)}


@app.get("/")
def health():
    return {"status": "ok", "landslide_model_loaded": landslide_bundle is not None,
             "flood_model_loaded": flood_bundle is not None}
