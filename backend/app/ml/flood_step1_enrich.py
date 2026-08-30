"""
FLOOD STEP 1 (v2 - reliable batched elevation): Enrich every Kaduwela GN
division with elevation, rainfall, and distance to the Kelani River.
Run: python flood_step1_enrich.py
Input:  data/Kaduwela_GN_Master.csv
Output: data/kaduwela_enriched.csv
"""
import pandas as pd
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
                print(f"    elevation batch {i}-{i+len(lat_chunk)} failed (attempt {attempt+1}): {e} -- waiting {wait}s")
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


df = pd.read_csv("data/Kaduwela_GN_Master.csv")
lat_list = df["latitude"].tolist()
lng_list = df["longitude"].tolist()

print(f"Fetching elevation for {len(df)} Kaduwela locations...")
elevations = batch_elevation(lat_list, lng_list)

rows = []
for i, row in df.reset_index(drop=True).iterrows():
    if elevations[i] is None:
        print(f"  skipping row {i}: no elevation")
        continue
    avg_rain, rain_7d = get_rainfall(row.latitude, row.longitude)
    if avg_rain is None:
        print(f"  skipping row {i}: no rainfall")
        continue
    dist_river = dist_to_river(row.latitude, row.longitude)
    rows.append({
        **row.to_dict(),
        "elevation": elevations[i], "avg_rainfall": avg_rain,
        "rainfall_7d": rain_7d, "dist_to_river_km": dist_river,
    })
    time.sleep(0.3)
    if i % 10 == 0:
        print(f"  {i}/{len(df)}...")

out = pd.DataFrame(rows)
out.to_csv("data/kaduwela_enriched.csv", index=False)
print(f"Done: {len(out)} rows -> data/kaduwela_enriched.csv")
print("\nReminder: no real flood-event labels yet. Check with your team, then use flood_step2_real_labels.py or flood_step2_proxy_labels.py.")