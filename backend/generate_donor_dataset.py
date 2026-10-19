"""
backend/generate_donor_dataset.py
---------------------------------
Fetches real disaster relief data directly from the running backend API
using the admin credentials, combines it with the GN Master coordinate data,
and generates a realistic synthetic donor-request interaction dataset for
training an XGBoost matching model.

Target:
  is_completed (1 = donation successfully handed over to disaster officer, 0 = not completed / unfulfilled)
"""
import os
import sys
import math
import random
from pathlib import Path
from typing import List, Dict, Any
import httpx
import pandas as pd
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "dataset"
OUTPUT_CSV = DATASET_DIR / "donor_matching_training_data.csv"

API_BASE = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = "admin@disaster.relief.lk"
ADMIN_PASS = "Admin@2026!"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def get_proximity_score(distance_km: float) -> float:
    if distance_km <= 5.0:
        return 1.0
    if distance_km <= 15.0:
        return 0.90
    if distance_km <= 30.0:
        return 0.75
    if distance_km <= 60.0:
        return 0.55
    if distance_km <= 100.0:
        return 0.35
    return 0.15


def get_capacity_match_score(capacity_level: str, quantity: float) -> float:
    if quantity <= 250:
        scores = {"Low": 0.90, "Medium": 1.0, "High": 1.0}
    elif quantity <= 1000:
        scores = {"Low": 0.55, "Medium": 0.90, "High": 1.0}
    else:
        scores = {"Low": 0.30, "Medium": 0.60, "High": 0.90}
    return scores.get(capacity_level, 0.70)


def fetch_api_data() -> Dict[str, Any]:
    print(f"Connecting to API at {API_BASE}...")
    with httpx.Client(timeout=15.0) as client:
        login_res = client.post(f"{API_BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if not login_res.is_success:
            raise RuntimeError(f"Login failed: {login_res.status_code} - {login_res.text}")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("Fetching relief camps...")
        camps = client.get(f"{API_BASE}/relief-camps", headers=headers).json()
        print(f" -> {len(camps)} relief camps fetched.")

        print("Fetching donation items catalog...")
        items = client.get(f"{API_BASE}/donation-items", headers=headers).json()
        print(f" -> {len(items)} catalog items fetched.")

        print("Fetching open disaster donation requests...")
        reqs = client.get(f"{API_BASE}/disaster-donation-requests?scope=all", headers=headers).json()
        print(f" -> {len(reqs)} disaster requests fetched.")

        print("Fetching user records...")
        users = client.get(f"{API_BASE}/users", headers=headers).json()
        donors = [u for u in users if u.get("role") == "donor"]
        print(f" -> {len(donors)} donor users fetched.")

    return {
        "camps": camps,
        "items": items,
        "requests": reqs,
        "donors": donors,
    }


def main():
    api_data = fetch_api_data()
    camps = api_data["camps"]
    catalog_items = api_data["items"]
    existing_donors = api_data["donors"]

    # Read GN coordinates master file
    gn_csv_path = DATASET_DIR / "Kaduwela_GN_Master.csv"
    gn_coords = {}
    if gn_csv_path.exists():
        gn_df = pd.read_csv(gn_csv_path)
        for _, row in gn_df.iterrows():
            gn = str(row.get("gn_division") or "").strip()
            lat = row.get("latitude")
            lon = row.get("longitude")
            if gn and pd.notna(lat) and pd.notna(lon):
                gn_coords[gn.lower()] = (float(lat), float(lon))

    # Standard donor categories and capacity levels
    donor_types = ["Individual", "Business", "NGO", "Hospital", "Pharmacy", "Organization"]
    categories = ["Dry Rations", "Water", "Medical", "Blankets", "Tarpaulins"]
    capacity_levels = ["Low", "Medium", "High"]
    disaster_types = ["Flood", "Landslide"]
    severities = ["Low", "Moderate", "High", "Critical"]

    # Map catalog items to standard categories
    def classify_item(name: str) -> str:
        name_l = name.lower()
        if any(w in name_l for w in ["water", "drink", "litre"]):
            return "Water"
        if any(w in name_l for w in ["rice", "ration", "formula", "food", "milk"]):
            return "Dry Rations"
        if any(w in name_l for w in ["first aid", "paracetamol", "medical", "napkin", "medicine"]):
            return "Medical"
        if "blanket" in name_l:
            return "Blankets"
        if any(w in name_l for w in ["tarpaulin", "tent", "sheet"]):
            return "Tarpaulins"
        return "Dry Rations"

    item_pool = []
    for it in catalog_items:
        it_name = it.get("item", "Dry Rations")
        item_pool.append({
            "name": it_name,
            "category": classify_item(it_name),
            "unit": it.get("unit", "packs"),
            "qtyPerPerson": float(it.get("quantityPerPerson", 1.0)),
        })

    # Fallback items if needed
    if not item_pool:
        item_pool = [
            {"name": "Rice", "category": "Dry Rations", "unit": "kg", "qtyPerPerson": 5.0},
            {"name": "Drinking Water", "category": "Water", "unit": "litres", "qtyPerPerson": 3.0},
            {"name": "First Aid Kits", "category": "Medical", "unit": "kits", "qtyPerPerson": 0.1},
            {"name": "Blankets", "category": "Blankets", "unit": "blankets", "qtyPerPerson": 1.0},
            {"name": "Dry Rations", "category": "Dry Rations", "unit": "packs", "qtyPerPerson": 2.0},
        ]

    # GN Division points list
    gn_names = list(gn_coords.keys()) if gn_coords else ["pahala bomiriya", "ranala", "hewagama", "kothalawala", "malabe"]

    # Generate 8,000 synthetic interaction samples
    N_SAMPLES = 8000
    rows = []

    print(f"Generating {N_SAMPLES} realistic donor-request interaction samples...")

    for i in range(N_SAMPLES):
        # 1. Pick or synthesize a relief camp
        camp = random.choice(camps) if camps else {}
        camp_name = camp.get("name", "Gunasekararamaya")
        camp_gn = (camp.get("gnDivision") or random.choice(gn_names)).strip()
        camp_cap = int(camp.get("maxCapacityPersons") or random.randint(50, 400))
        affected_pop = random.randint(15, max(20, camp_cap))

        # Camp coordinates
        camp_lat, camp_lon = gn_coords.get(camp_gn.lower(), (6.9344, 79.9830))

        # 2. Disaster attributes
        disaster = random.choice(disaster_types)
        severity = random.choice(severities)

        # 3. Item demand
        req_item = random.choice(item_pool)
        required_category = req_item["category"]
        base_demand = affected_pop * req_item["qtyPerPerson"]
        required_qty = round(max(5.0, base_demand * random.uniform(0.6, 1.4)), 0)

        # 4. Donor attributes
        donor_type = random.choice(donor_types)
        capacity_level = random.choice(capacity_levels)
        preferred_category = random.choice(categories + ["Multiple"])

        # Donor location
        donor_gn = random.choice(gn_names)
        donor_lat, donor_lon = gn_coords.get(donor_gn, (6.9344, 79.9830))
        # Add slight random spatial offset to simulate individual addresses (~0.5 - 25km)
        offset_lat = donor_lat + random.gauss(0, 0.04)
        offset_lon = donor_lon + random.gauss(0, 0.04)
        distance_km = max(0.5, haversine_km(offset_lat, offset_lon, camp_lat, camp_lon))

        # 5. Donor historical reliability (past handover completion rate)
        # 70% of donors have solid history (80-100%), 20% moderate (50-80%), 10% low (<50%)
        p_hist = random.random()
        if p_hist > 0.3:
            past_fulfillment_rate = round(random.uniform(0.80, 1.0), 2)
        elif p_hist > 0.1:
            past_fulfillment_rate = round(random.uniform(0.50, 0.79), 2)
        else:
            past_fulfillment_rate = round(random.uniform(0.10, 0.49), 2)

        days_since_last_donation = random.randint(3, 180)

        # 6. Engineered interaction features
        if preferred_category == required_category:
            category_match_score = 1.0
        elif preferred_category == "Multiple":
            category_match_score = 0.90
        else:
            category_match_score = 0.0

        proximity_score = get_proximity_score(distance_km)
        capacity_match_score = get_capacity_match_score(capacity_level, required_qty)

        # 7. Ground Truth Calculation (Handed over to disaster officer)
        # Latent probability of completing the handover based on real operational friction:
        # - Category match is primary (weight 0.35)
        # - Proximity / travel feasibility (weight 0.25)
        # - Capacity compatibility (weight 0.20)
        # - Past donor reliability (weight 0.15)
        # - Disaster urgency bonus (weight 0.05)
        urgency_bonus = 0.10 if severity in ["High", "Critical"] else 0.0

        latent_prob = (
            0.35 * category_match_score +
            0.25 * proximity_score +
            0.20 * capacity_match_score +
            0.15 * past_fulfillment_rate +
            0.05 * urgency_bonus
        )

        # Severe penalty if distance is huge (>60km) or category is completely mismatched (unless donor is Organization/Business)
        if category_match_score == 0.0 and donor_type not in ["Business", "Organization", "NGO"]:
            latent_prob *= 0.25
        if distance_km > 60:
            latent_prob *= 0.50

        # Clip probability to [0.03, 0.97] to preserve realistic stochastic variance
        latent_prob = min(0.97, max(0.03, latent_prob))

        # Ground truth target: 1 = completed and handed over to disaster officer, 0 = not completed
        is_completed = 1 if random.random() < latent_prob else 0

        rows.append({
            "donor_type": donor_type,
            "preferred_category": preferred_category,
            "capacity_level": capacity_level,
            "disaster_type": disaster,
            "severity": severity,
            "affected_population": affected_pop,
            "required_category": required_category,
            "item_name": req_item["name"],
            "required_quantity": required_qty,
            "distance_km": distance_km,
            "category_match_score": category_match_score,
            "capacity_match_score": capacity_match_score,
            "proximity_score": proximity_score,
            "past_fulfillment_rate": past_fulfillment_rate,
            "days_since_last_donation": days_since_last_donation,
            "camp_name": camp_name,
            "camp_gn_division": camp_gn,
            "is_completed": is_completed,
        })

    df = pd.DataFrame(rows)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSynthetic dataset successfully saved to: {OUTPUT_CSV}")
    print(f"Shape: {df.shape}")
    print(f"Class Balance (is_completed):")
    print(df["is_completed"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()
