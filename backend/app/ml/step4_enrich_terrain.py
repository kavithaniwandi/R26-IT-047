"""
STEP 4 (v3 - slower but more reliable): For every point (positive and
negative), fetch elevation, slope, and rainfall.

Fix from v2: hitting the elevation API with big batches back-to-back
triggered rate limiting after the first request. Smaller batches (50
instead of 100), longer pauses between batches, and longer backoff on
retry should avoid that.

Run: python step4_enrich_terrain.py
Input:  data/landslide_geocoded.csv, data/landslide_negatives.csv
Output: data/landslide_training_data.csv
"""
import pandas as pd
import requests
import time

BATCH_SIZE = 50


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


def enrich(df, label_source):
    delta = 0.001
    orig_lat, orig_lng = df["lat"].tolist(), df["lng"].tolist()
    north_lat = [x + delta for x in orig_lat]
    east_lng = [x + delta for x in orig_lng]

    print(f"  {label_source}: fetching elevation for {len(df)*3} points in batches...")
    elev_orig = batch_elevation(orig_lat, orig_lng)
    elev_north = batch_elevation(north_lat, orig_lng)
    elev_east = batch_elevation(orig_lat, east_lng)

    rows = []
    for i, row in df.reset_index(drop=True).iterrows():
        if elev_orig[i] is None or elev_north[i] is None or elev_east[i] is None:
            continue
        slope = abs(elev_north[i] - elev_orig[i]) + abs(elev_east[i] - elev_orig[i])
        avg_rain, rain_7d = get_rainfall(row.lat, row.lng)
        if avg_rain is None:
            continue
        rows.append({
            "lat": row.lat, "lng": row.lng,
            "elevation": elev_orig[i], "slope": slope,
            "avg_rainfall": avg_rain, "rainfall_7d": rain_7d,
            "label": row.label,
        })
        time.sleep(0.3)
        if i % 20 == 0:
            print(f"    rainfall {i}/{len(df)}...")
    return pd.DataFrame(rows)


pos = pd.read_csv("data/landslide_geocoded.csv")
neg = pd.read_csv("data/landslide_negatives.csv")

print("Enriching positive (landslide) points...")
pos_enriched = enrich(pos, "positive")
print("Enriching negative (non-landslide) points...")
neg_enriched = enrich(neg, "negative")

full = pd.concat([pos_enriched, neg_enriched], ignore_index=True)
full.to_csv("data/landslide_training_data.csv", index=False)
print(f"Done: {len(full)} rows -> data/landslide_training_data.csv")