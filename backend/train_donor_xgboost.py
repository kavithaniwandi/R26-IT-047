"""
backend/train_donor_xgboost.py
------------------------------
Trains an XGBoost Classification & Ranking model to predict the probability
of a donor completing a donation handover to a disaster officer.

Compatible with:
  1. Local backend execution: python train_donor_xgboost.py
  2. Google Colab: upload donor_matching_training_data.csv and run the script!

Outputs:
  - backend/ml_models/disaster-donation-request/donor_xgboost_model.joblib
"""
import os
import sys
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)

# ── Paths ────────────────────────────────────────────────────────────────────
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if (CURRENT_DIR.parent / "dataset").exists() else CURRENT_DIR

POSSIBLE_CSV_PATHS = [
    ROOT_DIR / "dataset" / "donor_matching_training_data.csv",
    CURRENT_DIR / "donor_matching_training_data.csv",
    Path("donor_matching_training_data.csv"),
    Path("/content/donor_matching_training_data.csv"),
]

CSV_PATH = None
for p in POSSIBLE_CSV_PATHS:
    if p.exists():
        CSV_PATH = p
        break

if CSV_PATH is None:
    raise FileNotFoundError("donor_matching_training_data.csv not found in expected locations.")

OUTPUT_MODEL_DIR = CURRENT_DIR / "ml_models" / "disaster-donation-request"
OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_MODEL_PATH = OUTPUT_MODEL_DIR / "donor_xgboost_model.joblib"


def train_model():
    print(f"Loading dataset from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Dataset shape: {df.shape}")

    # Feature definitions
    categorical_features = [
        "donor_type",
        "preferred_category",
        "capacity_level",
        "disaster_type",
        "severity",
        "required_category",
    ]

    numeric_features = [
        "affected_population",
        "required_quantity",
        "distance_km",
        "category_match_score",
        "capacity_match_score",
        "proximity_score",
        "past_fulfillment_rate",
        "days_since_last_donation",
    ]

    feature_cols = categorical_features + numeric_features
    target_col = "is_completed"

    X = df[feature_cols]
    y = df[target_col]

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
            (
                "num",
                "passthrough",
                numeric_features,
            ),
        ]
    )

    # XGBoost Classifier
    classifier = xgb.XGBClassifier(
        n_estimators=180,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
    )

    model_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    print("\nTraining XGBoost model...")
    model_pipeline.fit(X_train, y_train)

    # Evaluation
    y_pred = model_pipeline.predict(X_test)
    y_prob = model_pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print("\n" + "=" * 55)
    print("XGBOOST MODEL EVALUATION RESULTS:")
    print("=" * 55)
    print(f"  Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {auc:.4f}")
    print("-" * 55)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Not Completed (0)", "Completed Handover (1)"]))

    # Extract transformed feature names and importances
    ohe = model_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
    cat_names = list(ohe.get_feature_names_out(categorical_features))
    all_feature_names = cat_names + numeric_features

    importances = model_pipeline.named_steps["classifier"].feature_importances_
    importance_df = pd.DataFrame({
        "Feature": all_feature_names,
        "Importance": importances,
    }).sort_values("Importance", ascending=False)

    print("\nTop 10 Most Important Features:")
    print(importance_df.head(10).to_string(index=False))

    # Package model artifact with complete metadata
    model_package = {
        "model": model_pipeline,
        "model_name": "XGBoost Donor Matching & Handover Predictor",
        "algorithm": "XGBClassifier (Gradient Boosted Decision Trees)",
        "version": "1.0.0",
        "feature_columns": feature_cols,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
        },
        "target_description": "is_completed (Handover completed to disaster officer)",
    }

    joblib.dump(model_package, str(OUTPUT_MODEL_PATH))
    print(f"\nModel artifact saved successfully to:\n -> {OUTPUT_MODEL_PATH}")

    # Self-test demonstration
    print("\n" + "=" * 55)
    print("SELF-TEST: PREDICTING MATCH % FOR SAMPLE DONOR")
    print("=" * 55)
    sample_donor_request = pd.DataFrame([{
        "donor_type": "Individual",
        "preferred_category": "Dry Rations",
        "capacity_level": "Medium",
        "disaster_type": "Flood",
        "severity": "High",
        "affected_population": 80,
        "required_category": "Dry Rations",
        "required_quantity": 150.0,
        "distance_km": 4.5,
        "category_match_score": 1.0,
        "capacity_match_score": 1.0,
        "proximity_score": 1.0,
        "past_fulfillment_rate": 0.95,
        "days_since_last_donation": 14,
    }])

    prob = float(model_pipeline.predict_proba(sample_donor_request)[0, 1])
    match_pct = round(prob * 100, 1)
    print(f"Input: Dry Rations, Distance 4.5km, High Past Reliability (95%)")
    print(f"Predicted Handover Probability: {prob:.4f}")
    print(f"Calculated Match %:              {match_pct}% MATCH")
    print("=" * 55)


if __name__ == "__main__":
    train_model()
