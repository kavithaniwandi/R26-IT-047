"""
FLOOD STEP 2 -- PLAN A (use this if you got real flood incident data today).
Expects a CSV in the same shape as Landslide.csv: at minimum a gn_division
column and a flooded (1/0) or affected_people column.
Run: python flood_step2_real_labels.py
Input:  data/kaduwela_enriched.csv, data/flood_incidents.csv  <- put real data here
Output: data/flood_training_data.csv
"""
import pandas as pd

enriched = pd.read_csv("data/kaduwela_enriched.csv")
incidents = pd.read_csv("data/flood_incidents.csv")

flooded_divisions = set(incidents["gn_division"].str.strip().str.lower())
enriched["label"] = enriched["gn_division"].str.strip().str.lower().isin(flooded_divisions).astype(int)

enriched.to_csv("data/flood_training_data.csv", index=False)
print(f"Done: {enriched['label'].sum()} flooded / {len(enriched)} total divisions -> data/flood_training_data.csv")
