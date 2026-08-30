"""
STEP 3: A model needs both "yes this is a landslide site" and "no this isn't"
examples. We only have "yes" examples, so we generate random points in the
same area and treat them as "no" (as long as they're not right next to a
real landslide site).
Run: python step3_negative_samples.py
Input:  data/landslide_geocoded.csv
Output: data/landslide_negatives.csv
"""
import pandas as pd
import numpy as np

pos = pd.read_csv("data/landslide_geocoded.csv")

lat_min, lat_max = pos.lat.min() - 0.05, pos.lat.max() + 0.05
lng_min, lng_max = pos.lng.min() - 0.05, pos.lng.max() + 0.05

n_neg = len(pos)  # keep classes balanced
np.random.seed(42)
neg = pd.DataFrame({
    "lat": np.random.uniform(lat_min, lat_max, n_neg),
    "lng": np.random.uniform(lng_min, lng_max, n_neg),
})


def too_close_to_known_site(r):
    d = ((pos.lat - r.lat) ** 2 + (pos.lng - r.lng) ** 2) ** 0.5
    return (d < 0.003).any()  # roughly 300m


neg = neg[~neg.apply(too_close_to_known_site, axis=1)].copy()
neg["label"] = 0
neg.to_csv("data/landslide_negatives.csv", index=False)
print(f"Generated {len(neg)} negative samples -> data/landslide_negatives.csv")
