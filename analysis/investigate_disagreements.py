from __future__ import annotations

import csv
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score


ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def print_header(name: str) -> None:
    print(f"\n=== {name} ===")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def severity_thresholds() -> None:
    print_header("I1 severity thresholds")
    metrics_path = ROOT / "backend/app/models/severity_model/metrics.json"
    config_path = ROOT / "backend/ml_models/severity_ml/model_config.json"
    bundle_path = ROOT / "backend/app/models/severity_model/severity_bundle.joblib"
    test_proba_path = ROOT / "backend/ml_models/severity_ml/test_avg_proba.npy"

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    print("metrics_json_thresholds", metrics.get("thresholds"))
    print("model_config_threshold_high_low", config.get("threshold_high"), config.get("threshold_low"))

    sp_path = ROOT / "backend/app/models/severity_pipeline.py"
    sp = load_module(sp_path, "severity_pipeline")
    bundle = sp.load_bundle(str(bundle_path))
    print("bundle_threshold_high_low", bundle.t_high, bundle.t_low)
    print("bundle_layers", bundle.layers)

    print("test_avg_proba_exists", test_proba_path.exists())
    if test_proba_path.exists():
        proba = np.load(test_proba_path)
        print("test_avg_proba_shape", proba.shape)
    label_candidates = sorted(ROOT.rglob("*test*y*.npy")) + sorted(ROOT.rglob("*label*.npy"))
    print("label_npy_candidates", [rel(p) for p in label_candidates] or "NOT FOUND")
    csv_path = next(ROOT.rglob("nhamcs_2022_camp_relabeled_v2.csv"), None)
    print("nhamcs_csv", rel(csv_path) if csv_path else "NOT FOUND")
    print("metrics_json_test", metrics["metrics"]["test"])


def appeal_predictions() -> None:
    print_header("I2 appeal parity predictions")
    pred_path = ROOT / "robustness/outputs/appeal_parity_predictions.csv"
    metrics_path = ROOT / "robustness/outputs/appeal_parity_metrics.json"
    manifest_path = ROOT / "backend/ml_models/Donation Appeal/appeal_quality_training_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print("manifest_metrics", manifest.get("metrics"))
    print("manifest_split", manifest.get("split"))
    print("manifest_test_rows", manifest.get("test_rows"))
    if metrics_path.exists():
        print("parity_metrics_json", json.loads(metrics_path.read_text(encoding="utf-8")))
    if pred_path.exists():
        df = pd.read_csv(pred_path)
        print("pred_rows", len(df))
        if "language" in df:
            print("pred_language_counts", df["language"].value_counts().to_dict())
        if {"true_label", "pred_label"}.issubset(df.columns):
            print("pred_accuracy", float(accuracy_score(df["true_label"], df["pred_label"])))
        if {"true_score", "pred_score"}.issubset(df.columns):
            print("pred_mae", float(mean_absolute_error(df["true_score"], df["pred_score"])))
            print("pred_r2", float(r2_score(df["true_score"], df["pred_score"])))
        print("pred_columns", list(df.columns))


def appeal_split_indices() -> None:
    print_header("I2c appeal saved test indices")
    idx_path = ROOT / "backend/ml_models/Donation Appeal/appeal_quality_test_indices.npy"
    selected_path = ROOT / "backend/ml_models/Donation Appeal/appeal_quality_selected_indices.npy"
    print("test_indices_exists", idx_path.exists())
    if idx_path.exists():
        idx = np.load(idx_path)
        print("test_indices_len", len(idx))
        print("test_indices_head", idx[:10].tolist())
    print("selected_indices_exists", selected_path.exists())
    if selected_path.exists():
        sel = np.load(selected_path)
        print("selected_indices_len", len(sel))


def triage_csv() -> None:
    print_header("I3 triage csv")
    matches = sorted(ROOT.rglob("nhamcs_2022_camp_relabeled_v2.csv"))
    print("matches", [rel(p) for p in matches] or "NOT FOUND")
    for p in matches:
        df = pd.read_csv(p, low_memory=False)
        print("file", rel(p), "rows", len(df))
        if "camp_triage_label_final" in df:
            print("class_counts", df["camp_triage_label_final"].value_counts().to_dict())


def feature_counts() -> None:
    print_header("I4 features")
    sp_path = ROOT / "backend/app/models/severity_pipeline.py"
    sp = load_module(sp_path, "severity_pipeline_features")
    bundle = sp.load_bundle(str(ROOT / "backend/app/models/severity_model/severity_bundle.joblib"))
    features = bundle.features
    tfidf_names = list(features.tfidf_.get_feature_names_out())
    dense_names = list(features.dense_names_)
    complaint_names = list(features.complaint_vec_.get_feature_names_out())
    linear = tfidf_names + dense_names
    tree = dense_names + complaint_names
    print("linear_feature_count", len(linear))
    print("tree_feature_count", len(tree))
    groups = defaultdict(list)
    for name in linear:
        if name.startswith("vital_") or name.startswith("vf_") or name.startswith("miss_vital"):
            groups["linear_vitals"].append(name)
        elif name.startswith("rf_") or name in {"has_red_flag", "red_flag_count"}:
            groups["linear_red_flags"].append(name)
        elif name.startswith("age_") or name == "age_n":
            groups["linear_age"].append(name)
        elif name in {"n_complaints", "n_words"}:
            groups["linear_other"].append(name)
        else:
            groups["linear_complaint_tokens"].append(name)
    print("linear_group_counts", {k: len(v) for k, v in groups.items()})
    print("tree_group_counts", {
        "vitals": len([n for n in tree if n.startswith("vital_") or n.startswith("vf_") or n.startswith("miss_vital")]),
        "red_flags": len([n for n in tree if n.startswith("rf_") or n in {"has_red_flag", "red_flag_count"}]),
        "age": len([n for n in tree if n.startswith("age_") or n == "age_n"]),
        "complaint_tokens": len(complaint_names),
        "other": len([n for n in tree if n in {"n_complaints", "n_words"}]),
    })
    forbidden = [n for n in linear + tree if "entity" in n.lower() or "specialty" in n.lower() or "condition_group" in n.lower()]
    print("ner_or_routing_features", forbidden or "NOT FOUND")
    label_rule_overlap = sorted(set(sp.VITAL_COLS + [f"rf_{f}" for f in sp.KNOWN_FLAGS] + ["has_red_flag", "red_flag_count"]) & set(linear + tree))
    print("label_rule_overlap_candidates", label_rule_overlap)


def triggers() -> None:
    print_header("I5 critical triggers")
    path = ROOT / "backend/ml_models/severity_rule_based/keywords.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    critical = data.get("critical_triggers", [])
    print("count", len(critical))
    for i, trig in enumerate(critical, 1):
        print(f"{i:02d}", trig)
    shadowed = []
    for i, trig in enumerate(critical):
        earlier = critical[:i]
        if any(prev in trig for prev in earlier):
            shadowed.append((trig, [prev for prev in earlier if prev in trig]))
    print("shadowed", shadowed or "NOT FOUND")
    print("can_match_under_own_name", len(critical) - len(shadowed))


def quality_latency() -> None:
    print_header("I6 quality service rough timings")
    sys.path.insert(0, str(ROOT / "backend"))
    from app.models import quality_service as qs

    text = "A family affected by flooding needs food, clean water, medicine and temporary shelter. Donate today to support verified emergency relief."
    timings = {}
    t0 = time.perf_counter()
    artifacts = qs._load_artifacts()
    timings["load_artifacts_ms"] = (time.perf_counter() - t0) * 1000
    language = "English"
    lsa_components = artifacts["cfg"]["lsa_components"]
    t0 = time.perf_counter(); hand_raw = qs._handcrafted(text, language, artifacts); timings["handcrafted_ms"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter(); hand_scaled = artifacts["scaler"].transform(hand_raw); timings["scaler_ms"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter(); tfidf_feat = artifacts["tfidf_en"].transform([text]); timings["tfidf_ms"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter(); lsa_en = artifacts["svd_en"].transform(tfidf_feat); timings["lsa_ms"] = (time.perf_counter() - t0) * 1000
    lsa_si = np.zeros((1, lsa_components["si"]))
    lsa_ta = np.zeros((1, lsa_components["ta"]))
    x_clf = hstack([csr_matrix(hand_scaled), tfidf_feat, artifacts["ZERO_SI"], artifacts["ZERO_TA"]])
    t0 = time.perf_counter(); proba = artifacts["clf"].predict_proba(x_clf); timings["random_forest_calibrator_ms"] = (time.perf_counter() - t0) * 1000
    x_reg = np.hstack([proba, hand_scaled, lsa_en, lsa_si, lsa_ta])
    t0 = time.perf_counter(); raw = artifacts["reg"].predict(x_reg); timings["regressor_ms"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter(); artifacts["iso"].predict(raw); timings["isotonic_ms"] = (time.perf_counter() - t0) * 1000
    print({k: round(v, 3) for k, v in timings.items()})
    print("calls_gemini", "NOT FOUND")


def gemini_llama() -> None:
    print_header("I11 gemini/llama config")
    cfg = (ROOT / "backend/app/models/config.py").read_text(encoding="utf-8")
    gem = (ROOT / "backend/app/models/gemini_service.py").read_text(encoding="utf-8")
    for line in cfg.splitlines():
        if "GEMINI_MODEL" in line:
            print(line.strip())
    for line in gem.splitlines():
        if "meta-llama" in line or "max_new_tokens" in line or "temperature" in line or "language" in line and "English" in line:
            print(line.strip())
    for lang in ["English", "Sinhala", "Tamil"]:
        print(lang, gem.count(f'"{lang}"') + gem.count(f"'{lang}'"))


def main() -> None:
    severity_thresholds()
    appeal_predictions()
    appeal_split_indices()
    triage_csv()
    feature_counts()
    triggers()
    quality_latency()
    gemini_llama()


if __name__ == "__main__":
    main()
