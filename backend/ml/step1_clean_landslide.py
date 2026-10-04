"""
STEP 1: Clean up the spelling variants in the landslide CSV.
Run this first: python step1_clean_landslide.py
Input:  data/Landslide.csv   (copy your uploaded file here first)
Output: data/landslide_clean.csv
"""
import pandas as pd

df = pd.read_csv("data/Landslide.csv")

ds_map = {
    "Ambagamuwa Korale": "Ambagamuwa",
    "Ambgamuwa": "Ambagamuwa",
    "Ambagam": "Ambagamuwa",
    "Ambagauwa": "Ambagamuwa",
    "Ambagamuwa East": "Ambagamuwa",
}
df["ds_division"] = df["ds_division"].replace(ds_map)
df.to_csv("data/landslide_clean.csv", index=False)
print(f"Cleaned {len(df)} rows -> data/landslide_clean.csv")
