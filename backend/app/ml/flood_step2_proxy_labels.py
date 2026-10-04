"""
FLOOD STEP 2 -- PLAN B (fallback: use only if no real flood incident data
turned up by end of Day 1). Labels divisions as flood-prone using a
documented elevation + river-proximity heuristic. NOT verified ground
truth -- say so explicitly in your report and viva.
Run: python flood_step2_proxy_labels.py
Input:  data/kaduwela_enriched.csv
Output: data/flood_training_data.csv
"""
import pandas as pd

df = pd.read_csv("data/kaduwela_enriched.csv")

# proxy rule: low elevation AND close to the river => historically flood-prone
df["label"] = (
    (df["elevation"] < df["elevation"].median())
    & (df["dist_to_river_km"] < df["dist_to_river_km"].median())
).astype(int)

df.to_csv("data/flood_training_data.csv", index=False)
print(f"Proxy-labeled {df['label'].sum()} flood-prone / {len(df)} total divisions -> data/flood_training_data.csv")
print("Reminder: these are heuristic proxy labels, not verified flood records. Disclose this in your report.")
