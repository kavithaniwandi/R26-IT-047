"""
STEP 2b: Add a small random spread to points that only geocoded at the
coarse ds_division level, so they don't all sit on the exact same
coordinate (which would give the model no variation to learn from).

Jitter radius: ~2km, roughly matching the scale of a DS division, so
points stay plausible for the area they came from. Precise-level points
(address, gn_division_full, gn_division) are left untouched.

Run: python step2b_add_jitter.py
Input:  data/landslide_geocoded.csv
Output: data/landslide_geocoded.csv (overwritten, with 2 new columns)
"""
import pandas as pd
import numpy as np

df = pd.read_csv("data/landslide_geocoded.csv")

np.random.seed(42)
JITTER_KM = 2.0
KM_PER_DEGREE_LAT = 111.0

coarse_mask = df["geocode_precision"] == "ds_division"
n_coarse = coarse_mask.sum()
print(f"Jittering {n_coarse} coarse-precision points by up to {JITTER_KM}km...")

# random angle and distance within the jitter radius, per point
angles = np.random.uniform(0, 2 * np.pi, n_coarse)
distances_km = np.random.uniform(0, JITTER_KM, n_coarse)

lat_offset = (distances_km * np.cos(angles)) / KM_PER_DEGREE_LAT
lng_offset = (distances_km * np.sin(angles)) / (KM_PER_DEGREE_LAT * np.cos(np.radians(df.loc[coarse_mask, "lat"])))

df.loc[coarse_mask, "lat"] = df.loc[coarse_mask, "lat"] + lat_offset
df.loc[coarse_mask, "lng"] = df.loc[coarse_mask, "lng"] + lng_offset.values
df["jittered"] = coarse_mask

df.to_csv("data/landslide_geocoded.csv", index=False)
print(f"Done. {n_coarse} points jittered, {len(df) - n_coarse} left at original precision.")
print("Saved -> data/landslide_geocoded.csv (overwritten)")