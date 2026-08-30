"""
STEP 2 (v3 - strips GN division codes): Turn each text address into a
lat/lng coordinate.
Run: python step2_geocode.py

Fix from v2: gn_division values look like "317 A Lakshapana" (an
official division CODE glued to the name). Nominatim can't match that --
it needs just "Lakshapana". This version strips the leading code before
building queries, which should get many more rows matched at the
gn_division level (much better geographic spread than falling back to
ds_division for everything).

Input:  data/landslide_clean.csv
Output: data/landslide_geocoded.csv
"""
import re
import pandas as pd
import time
from geopy.geocoders import Nominatim

df = pd.read_csv("data/landslide_clean.csv")
geolocator = Nominatim(user_agent="disaster-relief-project")


def clean_gn_name(raw):
    # strips a leading code like "317 A " or "315 A " off the GN division name
    return re.sub(r"^\d+\s*[A-Za-z]?\s*", "", str(raw)).strip()


def try_geocode(query):
    try:
        loc = geolocator.geocode(query, timeout=10)
        time.sleep(1)
        return loc
    except Exception as e:
        print(f"    error on '{query}': {e}")
        time.sleep(1.5)
        return None


lats, lngs, precision = [], [], []

for i, row in df.iterrows():
    gn_clean = clean_gn_name(row["gn_division"])
    queries = [
        f"{row['address']}, {gn_clean}, Nuwara Eliya, Sri Lanka",
        f"{gn_clean}, {row['ds_division']}, Nuwara Eliya, Sri Lanka",
        f"{gn_clean}, Nuwara Eliya, Sri Lanka",
        f"{row['ds_division']}, Nuwara Eliya, Sri Lanka",
    ]
    levels = ["address", "gn_division_full", "gn_division", "ds_division"]

    found = False
    for query, level in zip(queries, levels):
        loc = try_geocode(query)
        if loc:
            lats.append(loc.latitude)
            lngs.append(loc.longitude)
            precision.append(level)
            found = True
            break

    if not found:
        lats.append(None)
        lngs.append(None)
        precision.append("failed")

    if i % 20 == 0:
        print(f"  geocoded {i}/{len(df)}...")

df["lat"] = lats
df["lng"] = lngs
df["geocode_precision"] = precision

before = len(df)
df_ok = df.dropna(subset=["lat", "lng"]).copy()
df_ok["label"] = 1

print(f"\nPrecision breakdown:")
print(df_ok["geocode_precision"].value_counts())

df_ok.to_csv("data/landslide_geocoded.csv", index=False)
print(f"\nDone: {len(df_ok)}/{before} addresses geocoded successfully -> data/landslide_geocoded.csv")