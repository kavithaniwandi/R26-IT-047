"""
severity_ml_service.py  -  ML severity inference (v3 stacked ensemble).

Drop-in replacement for the old module: same public function name, same signature,
same return shape as severity_rules.predict_severity():
    severity, priority_score, scores, matched_rules, critical_trigger

Files this module needs (see the integration notes):
    app/models/severity_pipeline.py                      (module written by the training notebook)
    app/models/severity_model/severity_bundle.joblib     (trained model)
    app/models/severity_model/metrics.json               (training metrics + library versions)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import warnings
from pathlib import Path
from typing import Optional

from . import severity_pipeline as sp

logger = logging.getLogger(__name__)

# Some scikit-learn / LightGBM version pairs emit this cosmetic warning on every predict(): the model is always fed
# arrays built by the same FeatureBuilder (fixed column order), so it carries no information. Narrow filter only.
warnings.filterwarnings("ignore", message="X does not have valid feature names", category=UserWarning)

MODEL_VERSION = os.environ.get("SEVERITY_MODEL_VERSION", "v3_stack_vitals")
_MODEL_DIR = Path(os.environ.get("SEVERITY_MODEL_DIR", Path(__file__).resolve().parent / "severity_model"))

_BUNDLE = None
_MANIFEST: dict = {}
_LOCK = threading.Lock()

SCORE_BANDS = {"CRITICAL": 80.0, "HIGH": 60.0, "MEDIUM": 40.0, "LOW": 0.0}
_LAYER_NAMES = {"red_flag": "red_flag_override", "complaint": "complaint_override"}


# ----------------------------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------------------------
def _current_versions() -> dict:
    import lightgbm, numpy, sklearn, xgboost
    return {"numpy": numpy.__version__, "sklearn": sklearn.__version__,
            "xgboost": xgboost.__version__, "lightgbm": lightgbm.__version__}


def _check_versions(trained_with: Optional[dict]) -> None:
    """A model pickled under other library versions can fail to load or silently misbehave."""
    if not trained_with:
        logger.warning("severity model: metrics.json has no library versions; cannot verify the environment")
        return
    now = _current_versions()
    if trained_with != now and os.environ.get("SEVERITY_ALLOW_VERSION_MISMATCH") != "1":
        raise RuntimeError(
            f"Severity model was trained with {trained_with} but this environment has {now}. "
            "Retrain in this environment (or install the trained versions). "
            "Set SEVERITY_ALLOW_VERSION_MISMATCH=1 only for debugging.")


def _load_bundle():
    global _BUNDLE, _MANIFEST
    if _BUNDLE is not None:
        return _BUNDLE
    with _LOCK:
        if _BUNDLE is None:
            bundle_path = _MODEL_DIR / "severity_bundle.joblib"
            if not bundle_path.exists():
                raise FileNotFoundError(f"Severity model not found at {bundle_path}")
            manifest_path = _MODEL_DIR / "metrics.json"
            manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
            _check_versions(manifest.get("libraries"))
            _BUNDLE = sp.load_bundle(str(bundle_path))
            _MANIFEST = manifest
            logger.info("severity model loaded: %s (T_HIGH=%.2f, T_LOW=%.2f, layers=%s)",
                        MODEL_VERSION, _BUNDLE.t_high, _BUNDLE.t_low, _BUNDLE.layers)
    return _BUNDLE


def warm_up() -> bool:
    """Optional: call at app startup so the first patient does not pay the load time."""
    predict_severity_ml("warm up", age=30)
    return True


# ----------------------------------------------------------------------------------------------
# Input mapping
# ----------------------------------------------------------------------------------------------
def _clean_vitals(vitals: Optional[dict]) -> dict:
    out = {}
    unknown = sorted(set(vitals or {}) - set(sp.VITAL_COLS))
    if unknown:
        logger.warning("severity model: ignoring unknown vital keys %s (expected %s)", unknown, list(sp.VITAL_COLS))
    for key in sp.VITAL_COLS:
        value = (vitals or {}).get(key)
        if value is None or value == "":
            continue
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            logger.warning("severity model: ignoring non-numeric vital %s=%r", key, value)
    return out


def predict_severity_ml_detailed(
    clinical_note: str,
    age: float | None = None,
    condition_group: str = "Unknown",      # accepted for compatibility; the v3 model does not use it
    vitals: dict | None = None,
    has_red_flag: int = 0,
    red_flag_count: int = 0,
    rf_flags: dict | None = None,
    symptoms: str = "",
) -> dict:
    """Full result including model-only decision, layers and version (for stats / auditing)."""
    bundle = _load_bundle()

    text = (symptoms or "").strip() or (clinical_note or "").strip()
    flags = {f: 1 for f, v in (rf_flags or {}).items() if f in sp.KNOWN_FLAGS and v}
    clean_vitals = _clean_vitals(vitals)

    row = sp.row_from_request(text, age, flags, clean_vitals)
    if has_red_flag:                                            # keep the app's explicit flag authoritative
        row.loc[0, "has_red_flag"] = 1
    row.loc[0, "red_flag_count"] = max(int(row.loc[0, "red_flag_count"]), int(red_flag_count or 0))

    out = bundle.predict(row)
    proba = out["proba"][0]
    model_idx, final_idx = int(out["model_pred"][0]), int(out["final_pred"][0])
    masks = {k: bool(v[0]) for k, v in out["layer_masks"].items()}

    # a layer is reported only when it actually raised the model's decision
    matched = [_LAYER_NAMES[k] for k in bundle.layers if masks.get(k) and model_idx < 2]

    severity = sp.LABELS[final_idx]
    return {
        "severity": severity,
        "priority_score": round(SCORE_BANDS[severity] + float(proba[final_idx]) * 19.9, 4),
        "scores": {"CRITICAL": 0.0, "HIGH": round(float(proba[2]), 4),
                   "MEDIUM": round(float(proba[1]), 4), "LOW": round(float(proba[0]), 4)},
        "matched_rules": matched,
        "critical_trigger": None,
        # extras (not part of the legacy shape)
        "model_severity": sp.LABELS[model_idx],
        "layers_fired": masks,
        "vitals_provided": sorted(clean_vitals),
        "thresholds": {"high": bundle.t_high, "low": bundle.t_low},
        "model_version": MODEL_VERSION,
    }


def predict_severity_ml(
    clinical_note: str,
    age: float | None = None,
    condition_group: str = "Unknown",
    vitals: dict | None = None,
    has_red_flag: int = 0,
    red_flag_count: int = 0,
    rf_flags: dict | None = None,
    symptoms: str = "",
) -> dict:
    """
    Run the ML inference pipeline for a single patient.
    Returns the same shape as severity_rules.predict_severity():
        severity, priority_score, scores, matched_rules, critical_trigger
    """
    full = predict_severity_ml_detailed(clinical_note, age, condition_group, vitals,
                                        has_red_flag, red_flag_count, rf_flags, symptoms)
    return {k: full[k] for k in ("severity", "priority_score", "scores", "matched_rules", "critical_trigger")}
