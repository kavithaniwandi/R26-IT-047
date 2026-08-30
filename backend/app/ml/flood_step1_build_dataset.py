"""
FLOOD STEP 1 (real data version): Build the flood training dataset.

Positive class: the 34 Kaduwela GN divisions in Kaduwela_GN_Master.csv,
confirmed as real flood-affected locations by cross-referencing against
Kelani_Admin_Boundaries_2025.xlsx (the official 2025 Kelani River flood
extent boundary data) -- every one of these 34 divisions appears in that
verified flood-impact list, so this is real ground truth, not a proxy.

Negative class: randomly generated points in the same wider area that
are NOT among the 34 known flood-affected divisions.

Run: python flood_step1_build_dataset.py
Input:  data/Kaduwela_GN_Master.csv
Output: data/flood_training_data.csv
"""
import pandas as pd
import numpy as np
import requests
import time
from math import radians, sin, cos, sqrt, atan2

BATCH_SIZE = 50

RIVER_POINTS = [
    (6.9553, 79.9439), (6.9481, 79.9578), (6.9401, 79.9686),
    (6.9364, 79.9791), (6.9308, 79.9911), (6.9290, 80.0031),
]


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def dist_to_river(lat, lng):
    return min(haversine_km(lat, lng, rlat, rlng) for rlat, rlng in RIVER_POINTS)


def batch_elevation(lat_list, lng_list):
    elevations = []
    for i in range(0, len(lat_list), BATCH_SIZE):
        lat_chunk = lat_list[i:i + BATCH_SIZE]
        lng_chunk = lng_list[i:i + BATCH_SIZE]
        success = False
        for attempt in range(4):
            try:
                r = requests.get(
                    "https://api.open-meteo.com/v1/elevation",
                    params={
                        "latitude": ",".join(str(x) for x in lat_chunk),
                        "longitude": ",".join(str(x) for x in lng_chunk),
                    },
                    timeout=20,
                )
                data = r.json()
                if "elevation" not in data:
                    raise ValueError(f"no 'elevation' key, response was: {data}")
                elevations.extend(data["elevation"])
                success = True
                break
            except Exception as e:
                wait = 5 * (attempt + 1)
                print(f"    elevation batch failed (attempt {attempt+1}): {e} -- waiting {wait}s")
                time.sleep(wait)
        if not success:
            elevations.extend([None] * len(lat_chunk))
        time.sleep(1.5)
    return elevations


def get_rainfall(lat, lng):
    for attempt in range(2):
        try:
            r = requests.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params={
                    "latitude": lat, "longitude": lng,
                    "start_date": "2024-01-01", "end_date": "2024-12-31",
                    "daily": "precipitation_sum", "timezone": "auto",
                },
                timeout=15,
            )
            daily = [d for d in r.json()["daily"]["precipitation_sum"] if d is not None]
            avg_daily = sum(daily) / len(daily) if daily else 0
            last_7d = sum(daily[-7:]) if len(daily) >= 7 else sum(daily)
            return avg_daily, last_7d
        except Exception as e:
            print(f"    rainfall failed for ({lat},{lng}), attempt {attempt+1}: {e}")
            time.sleep(3)
    return None, None


def enrich(lat_list, lng_list, labels, source):
    print(f"  {source}: fetching elevation for {len(lat_list)} points...")
    elevations = batch_elevation(lat_list, lng_list)
    rows = []
    for i in range(len(lat_list)):
        if elevations[i] is None:
            continue
        avg_rain, rain_7d = get_rainfall(lat_list[i], lng_list[i])
        if avg_rain is None:
            continue
        rows.append({
            "lat": lat_list[i], "lng": lng_list[i],
            "elevation": elevations[i], "avg_rainfall": avg_rain,
            "rainfall_7d": rain_7d,
            "dist_to_river_km": dist_to_river(lat_list[i], lng_list[i]),
            "label": labels[i],
        })
        time.sleep(0.3)
    return pd.DataFrame(rows)


master = pd.read_csv("data/Kaduwela_GN_Master.csv").dropna(subset=["gn_division"])
pos_lat = master["latitude"].tolist()
pos_lng = master["longitude"].tolist()
pos_labels = [1] * len(pos_lat)
print(f"Positive (confirmed flooded) points: {len(pos_lat)}")

np.random.seed(42)
lat_min, lat_max = min(pos_lat) - 0.05, max(pos_lat) + 0.05
lng_min, lng_max = min(pos_lng) - 0.05, max(pos_lng) + 0.05
n_neg = len(pos_lat)

candidate_lat = np.random.uniform(lat_min, lat_max, n_neg * 2)
candidate_lng = np.random.uniform(lng_min, lng_max, n_neg * 2)

neg_lat, neg_lng = [], []
for lat, lng in zip(candidate_lat, candidate_lng):
    too_close = any(haversine_km(lat, lng, plat, plng) < 0.5 for plat, plng in zip(pos_lat, pos_lng))
    if not too_close:
        neg_lat.append(lat)
        neg_lng.append(lng)
    if len(neg_lat) >= n_neg:
        break
neg_labels = [0] * len(neg_lat)
print(f"Negative (non-flooded) points generated: {len(neg_lat)}")

print("Enriching positive points...")
pos_df = enrich(pos_lat, pos_lng, pos_labels, "positive")
print("Enriching negative points...")
neg_df = enrich(neg_lat, neg_lng, neg_labels, "negative")

full = pd.concat([pos_df, neg_df], ignore_index=True)
full.to_csv("data/flood_training_data.csv", index=False)
print(f"\nDone: {len(full)} rows -> data/flood_training_data.csv")