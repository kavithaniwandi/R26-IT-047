"""
tests/test_ml.py
----------------
Test suite for all 4 ML models:
  1. Landslide Risk Classifier (joblib load + predict)
  2. Flood Risk Classifier (joblib load + predict)
  3. Medical Camp Suitability Scorer (joblib load + predict continuous 0-100)
  4. SOS Priority Scorer (joblib load + predict continuous 0-100)
  5. JSON metadata and lookup tables integrity
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pytest

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml_models"


class TestMLModels:
    def test_model_files_exist(self):
        """Verify all 13 artifacts exist in ml_models directory."""
        required_files = [
            "landslide_risk_model.joblib",
            "landslide_risk_scaler.joblib",
            "landslide_gn_encoder.joblib",
            "flood_risk_model.joblib",
            "flood_risk_scaler.joblib",
            "camp_suitability_model.joblib",
            "camp_suitability_scaler.joblib",
            "priority_score_model.joblib",
            "priority_score_scaler.joblib",
            "feature_metadata.json",
            "model_report.json",
            "gnd_landslide_risk_table.json",
            "dsd_flood_risk_table.json",
        ]
        for fname in required_files:
            p = MODEL_DIR / fname
            assert p.exists(), f"Missing artifact: {fname}"

    def test_landslide_model_inference(self):
        """Test Landslide Random Forest Classifier inference."""
        model = joblib.load(MODEL_DIR / "landslide_risk_model.joblib")
        scaler = joblib.load(MODEL_DIR / "landslide_risk_scaler.joblib")

        # 10 features: gn_encoded, incident_count, total_families, total_people,
        # mean_families, mean_people, max_people, std_people, people_per_family, severity_score
        sample = np.array([[5, 4, 10, 45, 2.5, 11.25, 20, 3.5, 4.5, 65.0]])
        sample_scaled = scaler.transform(sample)

        pred_class = model.predict(sample_scaled)[0]
        pred_proba = model.predict_proba(sample_scaled)[0]

        assert pred_class in [0, 1, 2]  # Low, Medium, High
        assert len(pred_proba) == 3
        assert np.isclose(np.sum(pred_proba), 1.0)

    def test_flood_model_inference(self):
        """Test Flood Random Forest Classifier inference."""
        model = joblib.load(MODEL_DIR / "flood_risk_model.joblib")
        scaler = joblib.load(MODEL_DIR / "flood_risk_scaler.joblib")

        # 12 features
        sample = np.array([[6.936, 79.957, 5.2, 0.85, 0.08, 0.07, 0.40, 0.15, 8.5, 2100.0, 3.8, 1]])
        sample_scaled = scaler.transform(sample)

        pred_class = model.predict(sample_scaled)[0]
        pred_proba = model.predict_proba(sample_scaled)[0]

        assert pred_class in [0, 1, 2]
        assert len(pred_proba) == 3
        assert np.isclose(np.sum(pred_proba), 1.0)

    def test_camp_suitability_model_inference(self):
        """Test Camp Suitability Scorer inference (continuous 0-100)."""
        model = joblib.load(MODEL_DIR / "camp_suitability_model.joblib")
        scaler = joblib.load(MODEL_DIR / "camp_suitability_scaler.joblib")

        # 10 features
        sample = np.array([[6.936, 79.957, 4.0, 0.3, 0.1, 0.8, 0.9, 1.0, 1.0, 0.7]])
        sample_scaled = scaler.transform(sample)

        pred_score = float(model.predict(sample_scaled)[0])
        assert 0.0 <= pred_score <= 100.0

    def test_priority_score_model_inference(self):
        """Test Priority Scorer inference (continuous 0-100)."""
        model = joblib.load(MODEL_DIR / "priority_score_model.joblib")
        scaler = joblib.load(MODEL_DIR / "priority_score_scaler.joblib")

        # 11 features: urgency, affected_people, affected_families, has_elderly, has_children,
        # has_disabled, medical_needs_count, flood_risk_score, landslide_risk_score, hours_since_sos, access_difficulty
        sample = np.array([[5.0, 30.0, 8.0, 1.0, 1.0, 1.0, 4.0, 0.8, 0.2, 2.0, 0.7]])
        sample_scaled = scaler.transform(sample)

        pred_score = float(model.predict(sample_scaled)[0])
        assert 0.0 <= pred_score <= 100.0

    def test_metadata_and_tables(self):
        """Validate metadata JSON schema and lookup tables."""
        with open(MODEL_DIR / "feature_metadata.json", "r") as f:
            meta = json.load(f)
            assert "landslide_model" in meta
            assert "flood_model" in meta
            assert "camp_model" in meta
            assert "priority_model" in meta

        with open(MODEL_DIR / "gnd_landslide_risk_table.json", "r") as f:
            gnd_table = json.load(f)
            assert len(gnd_table) > 0
            assert "gn_name" in gnd_table[0]
            assert "severity_score" in gnd_table[0]

        with open(MODEL_DIR / "dsd_flood_risk_table.json", "r") as f:
            dsd_table = json.load(f)
            assert len(dsd_table) == 11
            assert "dsd" in dsd_table[0]
            assert "flood_risk_score" in dsd_table[0]
