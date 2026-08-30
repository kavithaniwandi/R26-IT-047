"""
STEP 6 (run after both models are trained): score every known location
once with the trained models and save the results into the risk_zones
table. This becomes the base layer of your heatmap -- the app then adjusts
it live as SOS requests come in (see app/logic.py: update_heatmap).
Run this from the backend/ folder: python ml/step6_seed_risk_zones.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import joblib
from app.database import SessionLocal, engine, Base
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- landslide zones ---
landslide_bundle = joblib.load("ml/models/landslide_model.pkl")
ls_model, ls_features = landslide_bundle["model"], landslide_bundle["features"]
ls_data = pd.read_csv("ml/data/landslide_training_data.csv")
ls_data = ls_data[ls_data.label == 1]

for _, row in ls_data.iterrows():
    score = ls_model.predict_proba([[row[f] for f in ls_features]])[0][1]
    zone = models.RiskZone(
        gn_division="Ambagamuwa", lat=row.lat, lng=row.lng,
        disaster_type="landslide", base_risk_score=float(score),
        live_risk_score=float(score),
    )
    db.add(zone)
print(f"Added {len(ls_data)} landslide zones.")

# --- flood zones ---
flood_bundle = joblib.load("ml/models/flood_model.pkl")
fl_model, fl_features = flood_bundle["model"], flood_bundle["features"]
fl_data = pd.read_csv("ml/data/flood_training_data.csv")
fl_data = fl_data[fl_data.label == 1]

for _, row in fl_data.iterrows():
    score = fl_model.predict_proba([[row[f] for f in fl_features]])[0][1]
    zone = models.RiskZone(
        gn_division="Kaduwela", lat=row.lat, lng=row.lng,
        disaster_type="flood", base_risk_score=float(score),
        live_risk_score=float(score),
    )
    db.add(zone)
print(f"Added {len(fl_data)} flood zones.")

db.commit()
count = db.query(models.RiskZone).count()
print(f"Seeded {count} total risk zones into the database.")