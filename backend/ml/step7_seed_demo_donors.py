"""
STEP 7 (Day 4): seed some fake donors so your demo has data to match
against. Run from backend/: python ml/step7_seed_demo_donors.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo_donors = [
    {"name": "Colombo Relief Warehouse", "lat": 6.9271, "lng": 79.8612, "item_type": "food", "quantity": 500},
    {"name": "Kaduwela Community Center", "lat": 6.9339, "lng": 79.9835, "item_type": "medicine", "quantity": 100},
    {"name": "Red Cross Kandy Branch", "lat": 7.2906, "lng": 80.6337, "item_type": "medicine", "quantity": 250},
    {"name": "Nuwara Eliya Relief Camp", "lat": 6.9497, "lng": 80.7891, "item_type": "food", "quantity": 300},
    {"name": "Local Mosque Donation Drive", "lat": 6.9350, "lng": 79.9900, "item_type": "water", "quantity": 1000},
]

for d in demo_donors:
    db.add(models.Donor(**d, available=True))

db.commit()
print(f"Seeded {len(demo_donors)} demo donors.")
