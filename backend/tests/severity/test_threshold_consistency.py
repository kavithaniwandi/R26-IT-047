import json
from pathlib import Path

from app.models import severity_pipeline as sp


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent


def test_severity_thresholds_match_config_metrics_and_bundle():
    config = json.loads((REPO_ROOT / "backend/ml_models/severity_ml/model_config.json").read_text())
    metrics = json.loads((REPO_ROOT / "backend/app/models/severity_model/metrics.json").read_text())
    bundle = sp.load_bundle(str(REPO_ROOT / "backend/app/models/severity_model/severity_bundle.joblib"))

    expected_high, expected_low = metrics["thresholds"]

    assert config["threshold_high"] == expected_high == bundle.t_high
    assert config["threshold_low"] == expected_low == bundle.t_low
