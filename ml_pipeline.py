"""
ml_pipeline.py
==============================================================================
Full ML Pipeline for Disaster Relief Medical Donation Module (R26-IT-047)
==============================================================================
Implements:
  1. Data cleaning & preprocessing for all datasets
  2. Feature engineering per model
  3. Training + evaluation of all 4 models
  4. Saving models & encoders with joblib
  5. Generating a machine-readable model report

Run from the project root:
    python ml_pipeline.py

Outputs (written to backend/ml_models/):
  flood_risk_model.joblib
  flood_risk_scaler.joblib
  landslide_risk_model.joblib
  landslide_risk_scaler.joblib
  camp_suitability_model.joblib
  camp_suitability_scaler.joblib
  priority_score_model.joblib
  priority_score_scaler.joblib
  feature_metadata.json
  model_report.json
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

#  Paths 
ROOT        = Path(__file__).parent
DATASET_DIR = ROOT / "dataset"
MODEL_DIR   = ROOT / "backend" / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

#  Imports 
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler, label_binarize
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, accuracy_score,
    mean_absolute_error, r2_score
)
from sklearn.pipeline import Pipeline
import joblib

np.random.seed(42)

REPORT = {}     # accumulate model results

# ===========================================================================
# SECTION 1: DATA LOADING & CLEANING
# ===========================================================================

def banner(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

banner("STEP 1: Loading & Cleaning All Datasets")

#  1.1 Landslide records 
df_ls = pd.read_csv(DATASET_DIR / "Landslide_Cleaned.csv")
print(f"\n[Landslide] Loaded {len(df_ls)} records, {df_ls.shape[1]} columns")

# Strip whitespace from string columns
for col in df_ls.select_dtypes("object").columns:
    df_ls[col] = df_ls[col].str.strip()

# Standardize gn_division: remove GND code prefix (e.g. "317 A Lakshapana" -> "Lakshapana")
df_ls["gn_name"] = df_ls["gn_division"].str.replace(r"^\d+\s+[A-Z]\s+", "", regex=True).str.strip()

# Fill any numeric nulls (none expected, but defensive)
df_ls["affected_families"] = df_ls["affected_families"].fillna(df_ls["affected_families"].median())
df_ls["affected_people"]   = df_ls["affected_people"].fillna(df_ls["affected_people"].median())

print(f"  Unique GN divisions: {df_ls['gn_name'].nunique()}")
print(f"  Affected people range: {df_ls['affected_people'].min():.0f}  {df_ls['affected_people'].max():.0f}")
print(f"  Affected families range: {df_ls['affected_families'].min():.0f}  {df_ls['affected_families'].max():.0f}")
print(f"  Missing values after clean:\n{df_ls.isnull().sum()[df_ls.isnull().sum()>0]}")

#  1.2 Kaduwela GND master (geo-reference) 
df_gnd = pd.read_csv(DATASET_DIR / "Kaduwela_GN_Master.csv")
# Drop unnamed/empty column
df_gnd = df_gnd.drop(columns=[c for c in df_gnd.columns if "Unnamed" in str(c)])
# Named GNDs only (rows 0-33)
df_gnd_named = df_gnd.dropna(subset=["gn_division"]).copy()
# Boundary-only lat/long rows (flood perimeter points  unlabelled)
df_kelani_pts = df_gnd[df_gnd["gn_division"].isna()].copy()
print(f"\n[GND Master] Named GNDs: {len(df_gnd_named)}, Boundary pts: {len(df_kelani_pts)}")

#  1.3 Kelani Admin Boundaries (forward-fill sparse structure) 
df_adm = pd.read_excel(DATASET_DIR / "Kelani_Admin_Boundaries_2025.xlsx")
df_adm["District"] = df_adm["District"].ffill()
df_adm["DSD"]      = df_adm["DSD"].ffill()
df_adm.columns     = ["district", "dsd", "gnd", "gnd_no"]
df_adm["gnd"]      = df_adm["gnd"].str.strip()
df_adm["dsd"]      = df_adm["dsd"].str.strip()
df_adm["district"] = df_adm["district"].str.strip()
print(f"\n[Kelani Admin] {len(df_adm)} GNDs | Districts: {df_adm['district'].unique().tolist()}")
print(f"  DSDs: {df_adm['dsd'].unique().tolist()}")

#  1.4 Kelani Exposed Buildings 
df_bld = pd.read_excel(DATASET_DIR / "Kelani_Exposed_Buildings_2025.xlsx")
df_bld.columns = ["building_type", "building_name", "building_count"]
df_bld = df_bld.dropna(subset=["building_count"])
df_bld["building_count"] = pd.to_numeric(df_bld["building_count"], errors="coerce").fillna(0)
print(f"\n[Buildings] {len(df_bld)} records | Building types: {df_bld['building_type'].nunique()}")

#  1.5 Kelani Affected Roads 
df_rds = pd.read_excel(DATASET_DIR / "Kelani_Affected_Roads_2025 (1).xlsx")
df_rds.columns = ["road_type", "road_count", "length_km"]
df_rds = df_rds.dropna()
print(f"\n[Roads] {len(df_rds)} road types | Total length: {df_rds['length_km'].sum():.1f} km")

#  1.6 Kelani Landuse Impact 
df_lu_raw = pd.read_excel(DATASET_DIR / "Kelani_Landuse_Impact_2025.xlsx", header=None)
# Parse the landuse table (skip first 2 rows which are headers)
df_lu = df_lu_raw.iloc[2:].copy()
df_lu.columns = ["landuse_class", "extent_ha"]
df_lu = df_lu.dropna()
df_lu["landuse_class"] = df_lu["landuse_class"].str.strip().str.lower().str.replace(" ", "_")
df_lu["extent_ha"]     = pd.to_numeric(df_lu["extent_ha"], errors="coerce")
df_lu = df_lu.dropna()
df_lu = df_lu.reset_index(drop=True)
print(f"\n[Landuse] {len(df_lu)} classes:")
print(df_lu.to_string(index=False))

# ===========================================================================
# SECTION 2: FEATURE ENGINEERING
# ===========================================================================

banner("STEP 2: Feature Engineering")

#  2.1 Landslide GND-level risk aggregation 
print("\n[FE] Landslide GND-level aggregation...")
gnd_stats = df_ls.groupby("gn_name").agg(
    incident_count       = ("id", "count"),
    total_families       = ("affected_families", "sum"),
    total_people         = ("affected_people", "sum"),
    mean_families        = ("affected_families", "mean"),
    mean_people          = ("affected_people", "mean"),
    max_people           = ("affected_people", "max"),
    std_people           = ("affected_people", "std"),
).reset_index()
gnd_stats["std_people"] = gnd_stats["std_people"].fillna(0)
gnd_stats["people_per_family"] = (
    gnd_stats["total_people"] / gnd_stats["total_families"].replace(0, 1)
)

# Composite severity score (used as target proxy)
gnd_stats["severity_score"] = (
    0.4 * gnd_stats["total_people"] / gnd_stats["total_people"].max() +
    0.3 * gnd_stats["incident_count"] / gnd_stats["incident_count"].max() +
    0.2 * gnd_stats["total_families"] / gnd_stats["total_families"].max() +
    0.1 * gnd_stats["max_people"] / gnd_stats["max_people"].max()
) * 100

print(f"  GND-level records: {len(gnd_stats)}")
print(f"  Severity score range: {gnd_stats['severity_score'].min():.1f}  {gnd_stats['severity_score'].max():.1f}")

#  2.2 Landslide Basin-level Kelani flood features 
print("\n[FE] Building flood risk features from Kelani data...")

# Building exposure: critical vs residential vs other
critical_types = [
    "Hospitals - Unspecified", "Police Station", "Schools - National",
    "Schools - Maha Vidyalaya", "Schools - Central College",
    "Tertiary Educational Institutes", "Dispensary"
]
residential_types = ["Private House"]
commercial_types  = ["Commercial Buildings", "Hotel", "Factory Building"]

df_bld["is_critical"]    = df_bld["building_type"].isin(critical_types).astype(int)
df_bld["is_residential"] = df_bld["building_type"].isin(residential_types).astype(int)
df_bld["is_commercial"]  = df_bld["building_type"].isin(commercial_types).astype(int)

basin_critical_count    = df_bld[df_bld["is_critical"] == 1]["building_count"].sum()
basin_residential_count = df_bld[df_bld["is_residential"] == 1]["building_count"].sum()
basin_commercial_count  = df_bld[df_bld["is_commercial"] == 1]["building_count"].sum()
basin_total_buildings   = df_bld["building_count"].sum()

print(f"  Basin buildings: total={basin_total_buildings:.0f}, critical={basin_critical_count:.0f}, residential={basin_residential_count:.0f}")

# Road exposure
total_road_km  = df_rds["length_km"].sum()
major_road_km  = df_rds[df_rds["road_type"].str.contains("Main Road|Expressway", case=False)]["length_km"].sum()
jeep_track_km  = df_rds[df_rds["road_type"].str.contains("Jeep|Track", case=False)]["length_km"].sum()

# Landuse fractions
lu_dict = df_lu.set_index("landuse_class")["extent_ha"].to_dict()
total_ha = sum(lu_dict.values())
boggy_frac    = lu_dict.get("boggy_area", 0) / total_ha
water_frac    = lu_dict.get("water_area", 0) / total_ha
builtup_frac  = lu_dict.get("built_up_area", 0) / total_ha
culti_frac    = lu_dict.get("cultivation_area", 0) / total_ha
forest_frac   = lu_dict.get("forest_area", 0) / total_ha

print(f"  Landuse fractions -> boggy:{boggy_frac:.3f}, water:{water_frac:.3f}, "
      f"builtup:{builtup_frac:.3f}, culti:{culti_frac:.3f}, forest:{forest_frac:.3f}")

#  2.3 GND-level coordinate enrichment 
# Compute centroid of Kelani boundary points (proxy for basin centre)
kelani_lat_centre = df_kelani_pts["latitude"].mean()
kelani_lon_centre = df_kelani_pts["longitude"].mean()
print(f"\n  Kelani basin centre: lat={kelani_lat_centre:.4f}, lon={kelani_lon_centre:.4f}")

# For each named GND in Kaduwela, compute distance from Kelani basin centre
def haversine_km(lat1, lon1, lat2, lon2):
    """Approximate haversine distance in km."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

df_gnd_named = df_gnd_named.copy()
df_gnd_named["dist_to_kelani_km"] = df_gnd_named.apply(
    lambda r: haversine_km(r["latitude"], r["longitude"], kelani_lat_centre, kelani_lon_centre),
    axis=1
)

# ===========================================================================
# SECTION 3: MODEL 2  LANDSLIDE RISK CLASSIFIER
# ===========================================================================

banner("STEP 3: Model 2  Landslide Risk Classifier (Random Forest)")

print("\n[Landslide Model] Building dataset from GND-level statistics...")

# Label: severity tier based on percentiles of severity_score
p33 = gnd_stats["severity_score"].quantile(0.33)
p67 = gnd_stats["severity_score"].quantile(0.67)

def assign_risk(score):
    if score <= p33:
        return 0    # Low
    elif score <= p67:
        return 1    # Medium
    else:
        return 2    # High

gnd_stats["risk_class"] = gnd_stats["severity_score"].apply(assign_risk)
print(f"  Risk class distribution:\n{gnd_stats['risk_class'].value_counts().sort_index()}")
print(f"  Thresholds: Low<={p33:.1f}, Medium<={p67:.1f}, High>{p67:.1f}")

# Encode GN division name (ordinal based on incident frequency)
le_gn = LabelEncoder()
gnd_stats["gn_encoded"] = le_gn.fit_transform(gnd_stats["gn_name"])

# Feature matrix for landslide model
LS_FEATURES = [
    "gn_encoded", "incident_count", "total_families", "total_people",
    "mean_families", "mean_people", "max_people", "std_people",
    "people_per_family", "severity_score"
]
X_ls = gnd_stats[LS_FEATURES].values
y_ls = gnd_stats["risk_class"].values

print(f"\n  Feature matrix shape: {X_ls.shape}")
print(f"  Features: {LS_FEATURES}")

# Scale
scaler_ls = StandardScaler()
X_ls_scaled = scaler_ls.fit_transform(X_ls)

# Stratified 5-fold cross-validation (dataset is small, 54 GNDs)
print("\n  Running 5-fold stratified cross-validation...")
rf_ls = RandomForestClassifier(
    n_estimators=200,
    max_depth=6,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

cv_f1 = cross_val_score(rf_ls, X_ls_scaled, y_ls, cv=5, scoring="f1_weighted")
cv_acc = cross_val_score(rf_ls, X_ls_scaled, y_ls, cv=5, scoring="accuracy")
print(f"  CV F1 (weighted): {cv_f1.mean():.4f}  {cv_f1.std():.4f}")
print(f"  CV Accuracy:      {cv_acc.mean():.4f}  {cv_acc.std():.4f}")

# Train on full dataset (all 54 GNDs  no held-out split due to tiny size)
# We'll do a single 80/20 split for a held-out eval report
X_tr_ls, X_te_ls, y_tr_ls, y_te_ls = train_test_split(
    X_ls_scaled, y_ls, test_size=0.20, stratify=y_ls, random_state=42
)
rf_ls.fit(X_tr_ls, y_tr_ls)
y_pred_ls = rf_ls.predict(X_te_ls)

print("\n  Held-out 20% evaluation:")
print(classification_report(y_te_ls, y_pred_ls, target_names=["Low", "Medium", "High"], zero_division=0))
print(f"  Confusion matrix:\n{confusion_matrix(y_te_ls, y_pred_ls)}")

# Feature importances
feat_imp_ls = sorted(zip(LS_FEATURES, rf_ls.feature_importances_), key=lambda x: -x[1])
print("\n  Feature importances:")
for feat, imp in feat_imp_ls:
    bar = "#" * int(imp * 40)
    print(f"    {feat:<25} {bar} {imp:.4f}")

# Retrain on 100% data for production model
rf_ls_final = RandomForestClassifier(
    n_estimators=200, max_depth=6, min_samples_split=2,
    min_samples_leaf=1, class_weight="balanced", random_state=42, n_jobs=-1
)
rf_ls_final.fit(X_ls_scaled, y_ls)

# Save
joblib.dump(rf_ls_final, MODEL_DIR / "landslide_risk_model.joblib")
joblib.dump(scaler_ls,   MODEL_DIR / "landslide_risk_scaler.joblib")
joblib.dump(le_gn,       MODEL_DIR / "landslide_gn_encoder.joblib")
print(f"\n  [SAVED] landslide_risk_model.joblib, landslide_risk_scaler.joblib, landslide_gn_encoder.joblib")

REPORT["landslide_model"] = {
    "cv_f1_weighted_mean": round(float(cv_f1.mean()), 4),
    "cv_f1_weighted_std":  round(float(cv_f1.std()), 4),
    "cv_acc_mean":         round(float(cv_acc.mean()), 4),
    "n_training_gnds":     len(gnd_stats),
    "features":            LS_FEATURES,
    "target_classes":      ["Low", "Medium", "High"],
    "risk_thresholds":     {"low_max": round(p33, 2), "medium_max": round(p67, 2)},
    "note": "Trained on 54 GND-level aggregated records from Landslide_Cleaned.csv (257 incident rows). "
            "Class labels derived from severity_score percentiles. 5-fold CV used due to small N."
}

# ===========================================================================
# SECTION 4: MODEL 1  FLOOD RISK CLASSIFIER (Heuristic Proxy Labels)
# ===========================================================================

banner("STEP 4: Model 1  Flood Risk Classifier (RF, Proxy Labels)")

print("""
[IMPORTANT  Transparency Statement]
  The flood model uses HEURISTIC PROXY labels because verified flood-incident
  records from DMC are not yet available. Labels are derived from:
    - Geographic proximity to Kelani River basin
    - Boggy/water area fraction in the catchment
    - Built-up density (exposure)
    - Distance from the Kelani flood boundary centroid
  These labels describe MODELLED RISK, not verified ground-truth events.
  See proposal Section 8.2 for methodology.
""")

#  Build a synthetic GND-level flood dataset 
# Base: Kaduwela GND master (named GNDs = 34 rows)
np.random.seed(42)
n_gnds = len(df_gnd_named)

# Simulated spatial features per GND
lat   = df_gnd_named["latitude"].values
lon   = df_gnd_named["longitude"].values
dist  = df_gnd_named["dist_to_kelani_km"].values  # distance from Kelani centre

# Synthesize correlated flood risk features (domain-informed):
# GNDs closer to the basin have higher boggy/water proximity
proximity_score = np.clip(1 - (dist / dist.max()), 0, 1)   # 1=close, 0=far

# Simulate per-GND features with realistic variation
rng = np.random.RandomState(42)
boggy_frac_per_gnd    = np.clip(boggy_frac    + 0.05 * proximity_score + rng.normal(0, 0.02, n_gnds), 0, 1)
water_frac_per_gnd    = np.clip(water_frac    + 0.04 * proximity_score + rng.normal(0, 0.01, n_gnds), 0, 1)
builtup_frac_per_gnd  = np.clip(builtup_frac  + 0.03 * rng.uniform(0, 1, n_gnds), 0, 1)
road_density_per_gnd  = (major_road_km / total_road_km) + 0.1 * rng.uniform(0, 1, n_gnds)

# Approximate elevation proxy: GNDs further from coast tend to be higher
# Colombo basin is ~6-7N; lower lat = closer to sea = lower elevation
elevation_proxy = 5 + 15 * ((lat - lat.min()) / (lat.max() - lat.min() + 1e-9))
elevation_proxy = elevation_proxy + rng.normal(0, 1, n_gnds)

# Rainfall proxy (monsoon-season; heavier closer to hills)
rainfall_proxy = 1800 + 400 * proximity_score + rng.normal(0, 80, n_gnds)

# River level proxy (higher near basin centre)
river_level_proxy = 2.5 + 1.5 * proximity_score + rng.normal(0, 0.2, n_gnds)

# Is this GND within the Kelani flood boundary polygon? (heuristic)
# Kelani boundary pts lat: 6.863-6.917, lon: 79.914-80.033
is_kelani_zone = (
    (lat >= 6.863) & (lat <= 6.940) &
    (lon >= 79.900) & (lon <= 80.040)
).astype(int)

#  Composite heuristic flood risk label 
# Risk score: weighted combination of proxy features
flood_risk_score = (
    0.30 * proximity_score +
    0.20 * (boggy_frac_per_gnd / boggy_frac_per_gnd.max()) +
    0.15 * (water_frac_per_gnd / water_frac_per_gnd.max()) +
    0.15 * is_kelani_zone +
    0.10 * np.clip((river_level_proxy - 2.0) / 2.5, 0, 1) +
    0.10 * np.clip((rainfall_proxy - 1600) / 800, 0, 1)
) * 100

# Label: tertiles
p33f = np.percentile(flood_risk_score, 33)
p67f = np.percentile(flood_risk_score, 67)
flood_label = np.where(flood_risk_score <= p33f, 0,
               np.where(flood_risk_score <= p67f, 1, 2))

print(f"  GND count: {n_gnds}")
print(f"  Flood risk score range: {flood_risk_score.min():.1f}  {flood_risk_score.max():.1f}")
print(f"  Label distribution: Low={sum(flood_label==0)}, Medium={sum(flood_label==1)}, High={sum(flood_label==2)}")
print(f"  Kelani zone GNDs: {is_kelani_zone.sum()}")

# Add more GNDs from Kelani admin boundaries with synthesized features
# (to give the model more training points)
n_kelani_gnds = len(df_adm)
rng2 = np.random.RandomState(99)

# DSDs closer to Kelani River have higher risk
dsd_risk_map = {
    "KADUWELA": 0.85, "KOLONNAWA": 0.80, "KELANIYA": 0.90,
    "BIYAGAMA": 0.75, "WATTALA": 0.70, "MAHARA": 0.65,
    "DOMPE": 0.55, "COLOMBO": 0.60, "HOMAGAMA": 0.35,
    "PADUKKA": 0.30, "SEETHAWAKA": 0.40
}
dsd_risk = df_adm["dsd"].map(dsd_risk_map).fillna(0.5).values
district_risk = (df_adm["district"] == "COLOMBO").astype(float).values * 0.1

# Simulate features for Kelani GNDs
prox2 = dsd_risk + 0.05 * rng2.uniform(0, 1, n_kelani_gnds)
boggy2   = np.clip(boggy_frac   + 0.06 * prox2 + rng2.normal(0, 0.02, n_kelani_gnds), 0, 1)
water2   = np.clip(water_frac   + 0.04 * prox2 + rng2.normal(0, 0.01, n_kelani_gnds), 0, 1)
builtup2 = np.clip(builtup_frac + 0.04 * rng2.uniform(0, 1, n_kelani_gnds), 0, 1)
road2    = (major_road_km / total_road_km) + 0.1 * rng2.uniform(0, 1, n_kelani_gnds)
elev2    = 3 + 10 * (1 - prox2) + rng2.normal(0, 2, n_kelani_gnds)
rain2    = 1700 + 500 * prox2 + rng2.normal(0, 100, n_kelani_gnds)
river2   = 2.0 + 2.0 * prox2 + rng2.normal(0, 0.3, n_kelani_gnds)
zone2    = (dsd_risk >= 0.70).astype(int)

# Approximate lat/lon for Kelani basin (centred around 6.97N, 79.98E)
lat2 = 6.97 + rng2.normal(0, 0.05, n_kelani_gnds)
lon2 = 79.98 + rng2.normal(0, 0.05, n_kelani_gnds)

dist2 = haversine_km(lat2, lon2, kelani_lat_centre, kelani_lon_centre)
prox2 = np.clip(1 - (dist2 / max(dist2.max(), 1)), 0, 1)

risk2 = (
    0.30 * prox2 +
    0.20 * (boggy2 / (boggy2.max() + 1e-9)) +
    0.15 * (water2 / (water2.max() + 1e-9)) +
    0.15 * zone2 +
    0.10 * np.clip((river2 - 2.0) / 2.5, 0, 1) +
    0.10 * np.clip((rain2 - 1600) / 800, 0, 1)
) * 100

label2 = np.where(risk2 <= np.percentile(risk2, 33), 0,
          np.where(risk2 <= np.percentile(risk2, 67), 1, 2))

#  Combine both GND sources 
FLOOD_FEATURES = [
    "latitude", "longitude", "dist_to_kelani_km", "proximity_score",
    "boggy_frac", "water_frac", "builtup_frac", "road_density",
    "elevation_proxy", "rainfall_proxy", "river_level_proxy", "is_kelani_zone"
]

X_flood_part1 = np.column_stack([
    lat, lon, dist, proximity_score, boggy_frac_per_gnd,
    water_frac_per_gnd, builtup_frac_per_gnd, road_density_per_gnd,
    elevation_proxy, rainfall_proxy, river_level_proxy, is_kelani_zone
])
X_flood_part2 = np.column_stack([
    lat2, lon2, dist2, prox2, boggy2,
    water2, builtup2, road2,
    elev2, rain2, river2, zone2
])
X_flood = np.vstack([X_flood_part1, X_flood_part2])
y_flood  = np.concatenate([flood_label, label2])

# Global label re-calibration with combined data
f_score_combined = (
    0.30 * X_flood[:, 3] +   # proximity
    0.20 * (X_flood[:, 4] / (X_flood[:, 4].max() + 1e-9)) +  # boggy
    0.15 * (X_flood[:, 5] / (X_flood[:, 5].max() + 1e-9)) +  # water
    0.15 * X_flood[:, 11] +  # kelani zone
    0.10 * np.clip((X_flood[:, 10] - 2.0) / 2.5, 0, 1) +    # river
    0.10 * np.clip((X_flood[:, 9] - 1600) / 800, 0, 1)       # rainfall
) * 100
y_flood = np.where(f_score_combined <= np.percentile(f_score_combined, 33), 0,
           np.where(f_score_combined <= np.percentile(f_score_combined, 67), 1, 2))

print(f"\n  Combined GND count: {len(X_flood)}")
print(f"  Final label distribution: Low={sum(y_flood==0)}, Medium={sum(y_flood==1)}, High={sum(y_flood==2)}")

#  Train Flood RF 
scaler_fl = StandardScaler()
X_flood_scaled = scaler_fl.fit_transform(X_flood)

X_tr_fl, X_te_fl, y_tr_fl, y_te_fl = train_test_split(
    X_flood_scaled, y_flood, test_size=0.20, stratify=y_flood, random_state=42
)

rf_fl = RandomForestClassifier(
    n_estimators=300, max_depth=8, min_samples_split=3,
    min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1
)
rf_fl.fit(X_tr_fl, y_tr_fl)
y_pred_fl = rf_fl.predict(X_te_fl)

print("\n  Held-out 20% evaluation:")
print(classification_report(y_te_fl, y_pred_fl, target_names=["Low", "Medium", "High"], zero_division=0))
print(f"  Confusion matrix:\n{confusion_matrix(y_te_fl, y_pred_fl)}")

# CV
cv_f1_fl  = cross_val_score(rf_fl, X_flood_scaled, y_flood, cv=5, scoring="f1_weighted")
cv_acc_fl = cross_val_score(rf_fl, X_flood_scaled, y_flood, cv=5, scoring="accuracy")
print(f"\n  5-fold CV F1 (weighted): {cv_f1_fl.mean():.4f}  {cv_f1_fl.std():.4f}")
print(f"  5-fold CV Accuracy:      {cv_acc_fl.mean():.4f}  {cv_acc_fl.std():.4f}")

# Feature importances
feat_imp_fl = sorted(zip(FLOOD_FEATURES, rf_fl.feature_importances_), key=lambda x: -x[1])
print("\n  Feature importances:")
for feat, imp in feat_imp_fl:
    bar = "#" * int(imp * 40)
    print(f"    {feat:<30} {bar} {imp:.4f}")

# Retrain final on 100%
rf_fl_final = RandomForestClassifier(
    n_estimators=300, max_depth=8, min_samples_split=3,
    min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1
)
rf_fl_final.fit(X_flood_scaled, y_flood)

joblib.dump(rf_fl_final, MODEL_DIR / "flood_risk_model.joblib")
joblib.dump(scaler_fl,   MODEL_DIR / "flood_risk_scaler.joblib")
print(f"\n  [SAVED] flood_risk_model.joblib, flood_risk_scaler.joblib")

REPORT["flood_model"] = {
    "cv_f1_weighted_mean": round(float(cv_f1_fl.mean()), 4),
    "cv_f1_weighted_std":  round(float(cv_f1_fl.std()), 4),
    "cv_acc_mean":         round(float(cv_acc_fl.mean()), 4),
    "n_training_gnds":     len(X_flood),
    "features":            FLOOD_FEATURES,
    "target_classes":      ["Low", "Medium", "High"],
    "proxy_label_method":  "Composite heuristic: proximity_to_kelani, boggy_frac, water_frac, river_level, rainfall, kelani_zone",
    "note": (
        "PROXY LABELS  labels derived from geographic and hydrological heuristics, "
        "NOT from verified DMC flood incident records. Accuracy reflects agreement with "
        "the proxy rule, not ground-truth. See proposal Sec 8.2."
    )
}

# ===========================================================================
# SECTION 5: MODEL 3  MEDICAL CAMP SUITABILITY SCORER
# ===========================================================================

banner("STEP 5: Model 3  Medical Camp Suitability (RF Regressor)")

print("\n[Camp Model] Generating synthetic suitability dataset...")

# Generate candidate camp locations from GND grid
rng3 = np.random.RandomState(77)
n_camps = 400

# Use Kaduwela + Kelani GND coordinates as candidate locations
camp_lat = np.concatenate([
    lat + rng3.normal(0, 0.005, n_gnds),
    6.97 + rng3.normal(0, 0.08, n_camps - n_gnds)
])[:n_camps]
camp_lon = np.concatenate([
    lon + rng3.normal(0, 0.005, n_gnds),
    79.98 + rng3.normal(0, 0.08, n_camps - n_gnds)
])[:n_camps]

camp_dist = haversine_km(camp_lat, camp_lon, kelani_lat_centre, kelani_lon_centre)
camp_prox = np.clip(1 - (camp_dist / camp_dist.max()), 0, 1)

# Flood & landslide risk at each location (from models)
camp_flood_risk      = rng3.uniform(0, 1, n_camps)                 # 0=low, 1=high
camp_landslide_risk  = np.clip(0.3 - camp_prox * 0.2 + rng3.normal(0, 0.1, n_camps), 0, 1)
camp_sos_density     = np.clip(camp_prox * 5 + rng3.poisson(1, n_camps), 0, 15) / 15.0
camp_road_access     = np.clip(1 - camp_flood_risk * 0.5 + rng3.normal(0, 0.1, n_camps), 0, 1)
camp_critical_nearby = (rng3.uniform(0, 1, n_camps) > 0.5).astype(float)
camp_open_space      = (camp_landslide_risk < 0.4).astype(float)
camp_elev_suitable   = np.clip(0.5 + rng3.normal(0, 0.2, n_camps), 0, 1)

# Suitability score: high when close to SOS, low flood risk, good access
suitability = (
    0.25 * camp_sos_density +
    0.20 * (1 - camp_flood_risk) +
    0.20 * camp_road_access +
    0.15 * camp_critical_nearby +
    0.10 * (1 - camp_landslide_risk) +
    0.10 * camp_open_space
) * 100

suitability = np.clip(suitability + rng3.normal(0, 3, n_camps), 0, 100)

CAMP_FEATURES = [
    "latitude", "longitude", "dist_to_kelani_km",
    "flood_risk_score", "landslide_risk_score",
    "sos_density", "road_accessibility",
    "critical_facility_nearby", "open_space_available", "elevation_suitability"
]
X_camp = np.column_stack([
    camp_lat, camp_lon, camp_dist, camp_flood_risk, camp_landslide_risk,
    camp_sos_density, camp_road_access, camp_critical_nearby, camp_open_space, camp_elev_suitable
])
y_camp = suitability

scaler_camp = StandardScaler()
X_camp_scaled = scaler_camp.fit_transform(X_camp)

X_tr_c, X_te_c, y_tr_c, y_te_c = train_test_split(X_camp_scaled, y_camp, test_size=0.20, random_state=42)

rf_camp = RandomForestRegressor(
    n_estimators=200, max_depth=8, min_samples_split=3,
    min_samples_leaf=2, random_state=42, n_jobs=-1
)
rf_camp.fit(X_tr_c, y_tr_c)
y_pred_c = rf_camp.predict(X_te_c)

camp_mae = mean_absolute_error(y_te_c, y_pred_c)
camp_r2  = r2_score(y_te_c, y_pred_c)
print(f"\n  Test MAE:  {camp_mae:.3f} (out of 100)")
print(f"  Test R:   {camp_r2:.4f}")

feat_imp_camp = sorted(zip(CAMP_FEATURES, rf_camp.feature_importances_), key=lambda x: -x[1])
print("\n  Feature importances:")
for feat, imp in feat_imp_camp:
    bar = "#" * int(imp * 40)
    print(f"    {feat:<30} {bar} {imp:.4f}")

# Final model
rf_camp_final = RandomForestRegressor(
    n_estimators=200, max_depth=8, min_samples_split=3,
    min_samples_leaf=2, random_state=42, n_jobs=-1
)
rf_camp_final.fit(X_camp_scaled, y_camp)

joblib.dump(rf_camp_final, MODEL_DIR / "camp_suitability_model.joblib")
joblib.dump(scaler_camp,   MODEL_DIR / "camp_suitability_scaler.joblib")
print(f"\n  [SAVED] camp_suitability_model.joblib, camp_suitability_scaler.joblib")

REPORT["camp_model"] = {
    "test_mae": round(float(camp_mae), 3),
    "test_r2":  round(float(camp_r2), 4),
    "n_samples": n_camps,
    "features":  CAMP_FEATURES,
    "target":    "suitability_score (0-100 continuous)",
    "note": "Trained on synthetic candidate locations; suitability label derived from domain-weighted formula."
}

# ===========================================================================
# SECTION 6: MODEL 4  SOS PRIORITY SCORER
# ===========================================================================

banner("STEP 6: Model 4  SOS Priority Scorer (RF Regressor)")

print("\n[Priority Model] Generating synthetic SOS scenario dataset...")

rng4 = np.random.RandomState(123)
n_sos = 800

urgency              = rng4.randint(1, 6, n_sos).astype(float)         # 1-5
affected_people_sos  = rng4.randint(1, 50, n_sos).astype(float)
affected_families_s  = np.clip(affected_people_sos / rng4.uniform(2, 5, n_sos), 1, 20)
has_elderly          = rng4.binomial(1, 0.3, n_sos).astype(float)
has_children         = rng4.binomial(1, 0.4, n_sos).astype(float)
has_disabled         = rng4.binomial(1, 0.2, n_sos).astype(float)
medical_needs_count  = rng4.randint(0, 8, n_sos).astype(float)
flood_risk_sos       = rng4.uniform(0, 1, n_sos)
landslide_risk_sos   = rng4.uniform(0, 1, n_sos)
hours_since_sos      = rng4.exponential(12, n_sos)  # decay urgency over time
access_difficulty    = rng4.uniform(0, 1, n_sos)    # 0=easy, 1=very hard to reach

# Priority score formula (domain-expert rules):
priority = (
    0.25 * (urgency / 5.0) +
    0.15 * np.clip(affected_people_sos / 50.0, 0, 1) +
    0.10 * np.clip(affected_families_s / 20.0, 0, 1) +
    0.10 * has_elderly +
    0.08 * has_children +
    0.05 * has_disabled +
    0.10 * np.clip(medical_needs_count / 8.0, 0, 1) +
    0.08 * flood_risk_sos +
    0.05 * landslide_risk_sos +
    0.04 * access_difficulty
) * 100

# Time decay: older SOS requests gradually lose urgency (slight decay)
time_decay = np.exp(-0.01 * np.clip(hours_since_sos, 0, 72))
priority   = np.clip(priority * time_decay + rng4.normal(0, 2, n_sos), 0, 100)

SOS_FEATURES = [
    "urgency", "affected_people", "affected_families",
    "has_elderly", "has_children", "has_disabled",
    "medical_needs_count", "flood_risk_score", "landslide_risk_score",
    "hours_since_sos", "access_difficulty"
]
X_sos = np.column_stack([
    urgency, affected_people_sos, affected_families_s,
    has_elderly, has_children, has_disabled,
    medical_needs_count, flood_risk_sos, landslide_risk_sos,
    hours_since_sos, access_difficulty
])
y_sos = priority

scaler_sos = StandardScaler()
X_sos_scaled = scaler_sos.fit_transform(X_sos)

X_tr_s, X_te_s, y_tr_s, y_te_s = train_test_split(X_sos_scaled, y_sos, test_size=0.20, random_state=42)

rf_sos = RandomForestRegressor(
    n_estimators=300, max_depth=10, min_samples_split=4,
    min_samples_leaf=2, random_state=42, n_jobs=-1
)
rf_sos.fit(X_tr_s, y_tr_s)
y_pred_s = rf_sos.predict(X_te_s)

sos_mae = mean_absolute_error(y_te_s, y_pred_s)
sos_r2  = r2_score(y_te_s, y_pred_s)
print(f"\n  Test MAE:  {sos_mae:.3f} (out of 100)")
print(f"  Test R:   {sos_r2:.4f}")

feat_imp_sos = sorted(zip(SOS_FEATURES, rf_sos.feature_importances_), key=lambda x: -x[1])
print("\n  Feature importances:")
for feat, imp in feat_imp_sos:
    bar = "#" * int(imp * 40)
    print(f"    {feat:<30} {bar} {imp:.4f}")

rf_sos_final = RandomForestRegressor(
    n_estimators=300, max_depth=10, min_samples_split=4,
    min_samples_leaf=2, random_state=42, n_jobs=-1
)
rf_sos_final.fit(X_sos_scaled, y_sos)

joblib.dump(rf_sos_final, MODEL_DIR / "priority_score_model.joblib")
joblib.dump(scaler_sos,   MODEL_DIR / "priority_score_scaler.joblib")
print(f"\n  [SAVED] priority_score_model.joblib, priority_score_scaler.joblib")

REPORT["priority_model"] = {
    "test_mae": round(float(sos_mae), 3),
    "test_r2":  round(float(sos_r2), 4),
    "n_samples": n_sos,
    "features":  SOS_FEATURES,
    "target":    "priority_score (0-100 continuous)",
    "note": "Trained on synthetic SOS scenarios using domain-expert-informed priority formula. "
            "Includes time-decay to reduce urgency of unresolved stale requests."
}

# ===========================================================================
# SECTION 7: SAVE FEATURE METADATA & MODEL REPORT
# ===========================================================================

banner("STEP 7: Saving Feature Metadata & Model Report")

# Compute GND-level landslide risk score table (used by heatmap endpoint)
gnd_risk_table = gnd_stats[["gn_name", "severity_score", "risk_class",
                              "incident_count", "total_people", "total_families"]].copy()
gnd_risk_table["risk_label"] = gnd_risk_table["risk_class"].map({0:"Low", 1:"Medium", 2:"High"})
gnd_risk_table.to_json(MODEL_DIR / "gnd_landslide_risk_table.json", orient="records", indent=2)
print(f"\n  [SAVED] gnd_landslide_risk_table.json ({len(gnd_risk_table)} GNDs)")

# Compute Kelani DSD-level flood risk table
dsd_risk_table = pd.DataFrame({
    "dsd": list(dsd_risk_map.keys()),
    "flood_risk_score": [v * 100 for v in dsd_risk_map.values()],
    "risk_label": ["High" if v >= 0.67 else "Medium" if v >= 0.33 else "Low" for v in dsd_risk_map.values()]
})
dsd_risk_table.to_json(MODEL_DIR / "dsd_flood_risk_table.json", orient="records", indent=2)
print(f"  [SAVED] dsd_flood_risk_table.json ({len(dsd_risk_table)} DSDs)")

# Feature metadata for FastAPI inference endpoints
feature_metadata = {
    "landslide_model": {
        "input_features":  LS_FEATURES,
        "output_classes":  ["Low", "Medium", "High"],
        "scaler":          "landslide_risk_scaler.joblib",
        "encoder":         "landslide_gn_encoder.joblib",
        "gn_classes":      le_gn.classes_.tolist(),
        "risk_thresholds": {"low_max": round(p33, 2), "medium_max": round(p67, 2)},
    },
    "flood_model": {
        "input_features":  FLOOD_FEATURES,
        "output_classes":  ["Low", "Medium", "High"],
        "scaler":          "flood_risk_scaler.joblib",
        "proxy_label":     True,
    },
    "camp_model": {
        "input_features":  CAMP_FEATURES,
        "output":          "suitability_score_0_to_100",
        "scaler":          "camp_suitability_scaler.joblib",
    },
    "priority_model": {
        "input_features":  SOS_FEATURES,
        "output":          "priority_score_0_to_100",
        "scaler":          "priority_score_scaler.joblib",
    }
}
with open(MODEL_DIR / "feature_metadata.json", "w") as f:
    json.dump(feature_metadata, f, indent=2)
print(f"  [SAVED] feature_metadata.json")

REPORT["dataset_summary"] = {
    "landslide_csv": {"rows": 257, "gn_divisions": int(df_ls["gn_name"].nunique())},
    "kaduwela_gnd_master": {"named_gnds": int(len(df_gnd_named)), "boundary_pts": int(len(df_kelani_pts))},
    "kelani_admin_boundaries": {"gnds": 261, "dsds": 11, "districts": 2},
    "kelani_exposed_buildings": {"records": 404, "total_buildings": int(basin_total_buildings)},
    "kelani_affected_roads": {"road_types": 28, "total_km": round(float(total_road_km), 1)},
    "kelani_landuse": {"classes": 7},
}

with open(MODEL_DIR / "model_report.json", "w") as f:
    json.dump(REPORT, f, indent=2)
print(f"  [SAVED] model_report.json")

# ===========================================================================
# FINAL SUMMARY
# ===========================================================================

banner("FINAL SUMMARY")

print(f"""

              ML PIPELINE COMPLETE  ALL 4 MODELS TRAINED             

  Model 2: Landslide Risk Classifier (RF)                             
    CV F1 (weighted): {REPORT["landslide_model"]["cv_f1_weighted_mean"]:.4f}  {REPORT["landslide_model"]["cv_f1_weighted_std"]:.4f}                              
    Training GNDs:    {REPORT["landslide_model"]["n_training_gnds"]}                                         
                                                                      
  Model 1: Flood Risk Classifier (RF, proxy labels)                   
    CV F1 (weighted): {REPORT["flood_model"]["cv_f1_weighted_mean"]:.4f}  {REPORT["flood_model"]["cv_f1_weighted_std"]:.4f}                              
    Training GNDs:    {REPORT["flood_model"]["n_training_gnds"]}                                       
      Proxy labels  not verified ground truth                       
                                                                      
  Model 3: Camp Suitability Scorer (RF Regressor)                     
    Test MAE: {REPORT["camp_model"]["test_mae"]:.3f} / 100   Test R: {REPORT["camp_model"]["test_r2"]:.4f}                       
                                                                      
  Model 4: SOS Priority Scorer (RF Regressor)                         
    Test MAE: {REPORT["priority_model"]["test_mae"]:.3f} / 100   Test R: {REPORT["priority_model"]["test_r2"]:.4f}                       
                                                                      
  All models saved  backend/ml_models/                               

""")

files = list(MODEL_DIR.glob("*"))
print(f"  Files in backend/ml_models/ ({len(files)} total):")
for f in sorted(files):
    size_kb = f.stat().st_size / 1024
    print(f"    {f.name:<45} {size_kb:>8.1f} KB")
