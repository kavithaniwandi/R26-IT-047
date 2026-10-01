"""Acceptance tests for the v3 severity model adapter. Run from backend/:   python -m pytest tests/test_severity_ml_service.py -q
Optional parity test: set SEVERITY_TEST_CSV to the path of nhamcs_2022_camp_relabeled_v2.csv."""
import os
import threading

import numpy as np
import pytest

from app.models import severity_ml_service as ml
from app.models import severity_pipeline as sp

KEYS = {"severity", "priority_score", "scores", "matched_rules", "critical_trigger"}
VITALS_OK = {"vital_hr": 72, "vital_spo2": 98, "vital_sbp": 120, "vital_rr": 16, "vital_temp": 36.8, "pain_score": 1}
VITALS_BAD = {"vital_hr": 122, "vital_spo2": 86, "vital_sbp": 92, "vital_rr": 30, "vital_temp": 38.9, "pain_score": 8}


def check_shape(r):
    assert set(r) == KEYS
    assert r["severity"] in ("LOW", "MEDIUM", "HIGH") and r["critical_trigger"] is None
    assert set(r["scores"]) == {"CRITICAL", "HIGH", "MEDIUM", "LOW"} and r["scores"]["CRITICAL"] == 0.0
    assert abs(r["scores"]["HIGH"] + r["scores"]["MEDIUM"] + r["scores"]["LOW"] - 1) < 2e-3
    band = {"LOW": 0, "MEDIUM": 40, "HIGH": 60}[r["severity"]]
    assert band <= r["priority_score"] <= band + 19.9 + 1e-6
    assert isinstance(r["matched_rules"], list)


def test_model_loads_and_warms_up():
    assert ml.warm_up() is True


def test_app_payload_shape_without_vitals():
    r = ml.predict_severity_ml(clinical_note="Chest pain | Cough", age=58, condition_group="Respiratory",
                               has_red_flag=1, red_flag_count=1, rf_flags={"chest_pain": 1},
                               symptoms="Chest pain | Cough")
    check_shape(r)
    assert r["severity"] == "HIGH"


def test_mild_case_with_vitals_is_low():
    r = ml.predict_severity_ml("Cold", age=25, vitals=VITALS_OK, symptoms="Cold")
    check_shape(r)
    assert r["severity"] == "LOW"


def test_severe_case_with_vitals_is_high():
    r = ml.predict_severity_ml("Shortness of breath", age=70, vitals=VITALS_BAD, symptoms="Shortness of breath")
    check_shape(r)
    assert r["severity"] == "HIGH"


@pytest.mark.parametrize("kw", [
    dict(clinical_note="Cough", age=None),
    dict(clinical_note="", symptoms="", age=40),
    dict(clinical_note="Abdominal pain | Vomiting", age=33),
    dict(clinical_note="Fever", age=30, vitals={"vital_hr": "110", "pain_score": "6"}),
    dict(clinical_note="Fever", age=30, vitals={"vital_hr": "abc", "vital_spo2": None, "vital_rr": ""}),
    dict(clinical_note="Fever", age=30, vitals={"hr": 99, "temperature": 39}),
    dict(clinical_note="Fever", age=30, rf_flags={"dx_resus": 1, "made_up": 1}),
    dict(clinical_note="Fever", age=250),
    dict(clinical_note=" | ".join(["Chest pain"] * 80), age=60),
])
def test_edge_inputs_never_crash_and_keep_shape(kw):
    check_shape(ml.predict_severity_ml(**kw))


def test_post_triage_dx_flags_are_ignored():
    d = ml.predict_severity_ml_detailed("Fever", age=30, rf_flags={"dx_resus": 1})
    assert d["layers_fired"]["red_flag"] is False


def test_explicit_red_flag_is_authoritative():
    assert ml.predict_severity_ml("Headache", age=30, has_red_flag=1, red_flag_count=1)["severity"] == "HIGH"


def test_detailed_result_reports_version_and_vitals():
    d = ml.predict_severity_ml_detailed("Fever", age=30, vitals={"vital_hr": 110})
    assert d["model_version"] and d["vitals_provided"] == ["vital_hr"]


def test_thread_safety():
    errs = []

    def worker():
        try:
            for _ in range(10):
                check_shape(ml.predict_severity_ml("Chest pain", age=50, rf_flags={"chest_pain": 1}))
        except Exception as e:  # noqa: BLE001
            errs.append(e)

    ts = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs, errs


@pytest.mark.skipif(not os.environ.get("SEVERITY_TEST_CSV"), reason="set SEVERITY_TEST_CSV to run the parity test")
def test_request_path_matches_bundle_on_dataset_rows():
    import pandas as pd
    df = pd.read_csv(os.environ["SEVERITY_TEST_CSV"], low_memory=False).sample(300, random_state=7).reset_index(drop=True)
    cols = ["symptoms", "age", "has_red_flag", "red_flag_count"] + [f"rf_{f}" for f in sp.KNOWN_FLAGS] + sp.VITAL_COLS
    ref = ml._load_bundle().predict(df[cols])
    for i, row in df.iterrows():
        flags = {f: int(row[f"rf_{f}"]) for f in sp.KNOWN_FLAGS if row[f"rf_{f}"]}
        vit = {c: (None if pd.isna(row[c]) else float(row[c])) for c in sp.VITAL_COLS}
        out = ml.predict_severity_ml_detailed(row["symptoms"], age=row["age"], vitals=vit,
                                              has_red_flag=int(row["has_red_flag"]),
                                              red_flag_count=int(row["red_flag_count"]),
                                              rf_flags=flags, symptoms=row["symptoms"])
        assert out["severity"] == ref["final_labels"][i]
        assert abs(out["scores"]["HIGH"] - round(float(ref["proba"][i, 2]), 4)) < 1e-4
