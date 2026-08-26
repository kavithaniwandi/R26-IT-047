from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).resolve().parents[1]
MODEL_DIR  = BASE_DIR / "models" / "severity_ml"

# ── Lazy singleton loader ─────────────────────────────────────────────────────

_artefacts: dict | None = None


def _load_artefacts() -> dict:
    global _artefacts
    if _artefacts is not None:
        return _artefacts

    with (MODEL_DIR / "model_config.json").open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    _artefacts = {
        "cfg":       cfg,
        "tfidf":     joblib.load(MODEL_DIR / "tfidf_vectorizer.pkl"),
        "sc":        joblib.load(MODEL_DIR / "scaler_maxabs.pkl"),
        "sc_d":      joblib.load(MODEL_DIR / "scaler_standard.pkl"),
        "le_cg":     joblib.load(MODEL_DIR / "label_encoder_cg.pkl"),
        "meta":      joblib.load(MODEL_DIR / "meta_learner.pkl"),
        "lr_a":      joblib.load(MODEL_DIR / "base_lr_a.pkl"),
        "lr_b":      joblib.load(MODEL_DIR / "base_lr_b.pkl"),
        "lr_c":      joblib.load(MODEL_DIR / "base_lr_c.pkl"),
        "lgb":       joblib.load(MODEL_DIR / "base_lgb.pkl"),
        "xgb":       joblib.load(MODEL_DIR / "base_xgb.pkl"),
        "complaint_pattern": re.compile(
            "|".join(re.escape(p) for p in cfg["high_complaint_patterns"]),
            re.IGNORECASE,
        ),
    }
    return _artefacts


# ── Text cleaning (mirrors Colab clean_text exactly) ─────────────────────────

def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"symptoms:\s*", "", text)
    text = re.sub(r"age:\s*(\d+)", r"age\1", text)
    text = re.sub(r"[^a-z0-9_ ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ── Condition group encoder ───────────────────────────────────────────────────

def _encode_cg(condition_group: str, cfg: dict, le_cg) -> np.ndarray:
    """One-hot vector + [high_rate, med_rate, low_rate] for one sample."""
    classes  = le_cg.classes_
    n_cls    = len(classes)
    oh       = np.zeros(n_cls, dtype="float32")
    idx      = np.where(classes == condition_group)[0]
    if len(idx):
        oh[idx[0]] = 1.0

    hp = cfg["high_rate_map"].get(condition_group, 0.26)
    mp = cfg["med_rate_map"].get(condition_group,  0.33)
    lp = cfg["low_rate_map"].get(condition_group,  0.41)

    return np.concatenate([oh, [hp, mp, lp]]).astype("float32")


# ── Structured feature builder ────────────────────────────────────────────────

def _build_struct(
    age:            float,
    pain_score:     float,
    text_clean:     str,
    condition_group: str,
    has_red_flag:   int,
    red_flag_count: int,
    rf_flags:       dict[str, int],   # {rf_breathing_difficulty: 0/1, ...}
    vitals:         dict[str, float], # {vital_hr, vital_spo2, vital_sbp, vital_rr, vital_temp}
    cfg:            dict,
) -> np.ndarray:
    """Mirrors build_struct() from the notebook for a single sample."""

    VF_COLS = cfg["vf_cols"]
    RF_COLS = cfg["rf_cols"]   # ['has_red_flag','red_flag_count', rf_*]

    # ── Red flag columns ──────────────────────────────────────────────────────
    known_flags = [
        "breathing_difficulty", "chest_pain", "focal_neurologic_deficit",
        "active_bleeding", "syncope", "seizure",
    ]
    rf_vec = np.array(
        [float(has_red_flag), float(red_flag_count)]
        + [float(rf_flags.get(f, 0)) for f in known_flags],
        dtype="float32",
    )  # len == 8

    # ── Age features ──────────────────────────────────────────────────────────
    age    = float(age) if age is not None else 35.0
    age_n  = age / 100.0
    age_e  = float(age >= 65)
    age_c  = float(age <   5)
    age_a  = float(5 <= age < 65)

    # ── Symptom count ─────────────────────────────────────────────────────────
    sym_c = len(text_clean.split()) / 20.0

    # ── Prior rates ───────────────────────────────────────────────────────────
    hp = cfg["high_rate_map"].get(condition_group, 0.26)
    mp = cfg["med_rate_map"].get(condition_group,  0.33)
    lp = cfg["low_rate_map"].get(condition_group,  0.41)

    # ── Interaction terms ─────────────────────────────────────────────────────
    has_rf_inv = 1.0 - float(has_red_flag)
    med_score  = mp * age_a * has_rf_inv * min(max(sym_c, 0.1), 0.8)
    low_score  = lp * has_rf_inv * (1.0 - age_e)
    elder_x_hp = age_e * hp
    rf_x_hp    = float(red_flag_count) * hp

    # ── Vital threshold flags (mirrors apply_thresh) ──────────────────────────
    hr    = vitals.get("vital_hr",   None)
    spo2  = vitals.get("vital_spo2", None)
    sbp   = vitals.get("vital_sbp",  None)
    rr    = vitals.get("vital_rr",   None)
    temp  = vitals.get("vital_temp", None)
    pain  = pain_score if pain_score is not None else 5.0

    def _v(val, op, threshold):
        if val is None:
            return 0.0
        ops = {">": val > threshold, "<": val < threshold,
               ">=": val >= threshold, "==": val == threshold}
        return float(ops[op])

    vf_bradycardia       = _v(hr,   "<",  50)
    vf_hypox_severe      = _v(spo2, "<",  90)
    vf_hypox_moderate    = _v(spo2, "<",  94)
    vf_hypotension       = _v(sbp,  "<",  90)
    vf_hypertension_crit = _v(sbp,  ">",  180)
    vf_tachypnea_severe  = _v(rr,   ">",  24)
    vf_bradypnea         = _v(rr,   "<",  10)
    vf_hypothermia       = _v(temp, "<",  35.0)
    vf_high_fever        = _v(temp, ">",  38.5)
    vf_pain_severe       = _v(pain, ">=", 8)
    vf_pain_none         = _v(pain, "==", 0)
    vf_elderly           = float(age >= 65)
    vf_child             = float(age <   5)
    vf_pain_low          = float(pain <= 3)
    vf_critical_vital    = max(vf_hypox_severe, vf_hypotension,
                               vf_bradycardia, vf_hypothermia)
    vf_any_danger        = max(vf_hypox_severe, vf_hypotension,
                               vf_bradycardia, vf_hypothermia,
                               vf_tachypnea_severe, vf_bradypnea)
    vf_elder_x_pain      = age_e * (pain / 10.0)

    vf_vec = np.array([
        vf_bradycardia, vf_hypox_severe, vf_hypox_moderate,
        vf_hypotension, vf_hypertension_crit, vf_tachypnea_severe,
        vf_bradypnea, vf_hypothermia, vf_high_fever,
        vf_pain_severe, vf_pain_none,
        vf_elderly, vf_child, vf_pain_low,
        vf_critical_vital, vf_any_danger, vf_elder_x_pain,
    ], dtype="float32")

    pain_norm    = pain / 10.0
    pain_x_age   = pain_norm * age_e

    struct = np.concatenate([
        rf_vec,
        [age_n, age_c, age_e, age_a, sym_c, hp, mp, lp,
         med_score, low_score, elder_x_hp, rf_x_hp],
        vf_vec,
        [pain_norm, pain_x_age],
    ]).astype("float32")

    return struct


# ── Vital imputation using per-class medians from config 

def _impute_vitals(vitals: dict[str, float | None], severity_hint: int, cfg: dict) -> dict:
    """Fill missing vitals using training medians for the given class (0=LOW,1=MED,2=HIGH)."""
    medians = cfg["vital_medians"][str(severity_hint)]
    return {col: vitals.get(col) if vitals.get(col) is not None else medians[col]
            for col in cfg["vital_cols"]}


# ── Public inference entry point 

def predict_severity_ml(
    clinical_note:   str,
    age:             float | None = None,
    condition_group: str          = "Unknown",
    vitals:          dict | None  = None,
    has_red_flag:    int          = 0,
    red_flag_count:  int          = 0,
    rf_flags:        dict | None  = None,
    symptoms:        str          = "",
) -> dict:
    """
    Run the full ML inference pipeline for a single patient.

    Returns the same shape as severity_rules.predict_severity():
        severity, priority_score, scores, matched_rules, critical_trigger
    """
    art = _load_artefacts()
    cfg = art["cfg"]

    TH = cfg["threshold_high"]
    TL = cfg["threshold_low"]

    # ── 1. Text cleaning + TF-IDF ─────────────────────────────────────────────
    text_clean = _clean_text(clinical_note)
    X_tfidf    = art["tfidf"].transform([text_clean])   # sparse (1, 8000)

    # ── 2. Condition group encoding ───────────────────────────────────────────
    cg_vec = _encode_cg(condition_group, cfg, art["le_cg"])  # (n_cg_classes + 3,)

    # ── 3. Vital imputation + structured features ─────────────────────────────
    raw_vitals  = vitals or {}
    imp_vitals  = _impute_vitals(raw_vitals, severity_hint=1, cfg=cfg)  # impute as MEDIUM
    pain        = raw_vitals.get("pain_score", imp_vitals.get("pain_score", 5.0))
    struct_vec  = _build_struct(
        age             = age if age is not None else 35.0,
        pain_score      = pain,
        text_clean      = text_clean,
        condition_group = condition_group,
        has_red_flag    = has_red_flag,
        red_flag_count  = red_flag_count,
        rf_flags        = rf_flags or {},
        vitals          = imp_vitals,
        cfg             = cfg,
    )  # (n_struct,)

    # ── 4. Assemble sparse matrix (text + cg + struct) → MaxAbsScaler ─────────
    X_sparse = hstack([
        X_tfidf,
        csr_matrix(cg_vec.reshape(1, -1)),
        csr_matrix(struct_vec.reshape(1, -1)),
    ])
    X_sc = art["sc"].transform(X_sparse).astype("float32")

    # ── 5. Assemble dense matrix (cg + struct) → StandardScaler ───────────────
    Xd = np.hstack([cg_vec, struct_vec]).reshape(1, -1).astype("float32")
    Xd_sc = art["sc_d"].transform(Xd).astype("float32")

    # ── 6. Base model probabilities (5 models × 3 classes = 15 cols) ──────────
    proba_cols = np.hstack([
        art["lr_a"].predict_proba(X_sc),   # sparse
        art["lr_b"].predict_proba(X_sc),   # sparse
        art["lr_c"].predict_proba(X_sc),   # sparse
        art["lgb"].predict_proba(Xd_sc),   # dense
        art["xgb"].predict_proba(Xd_sc),   # dense
    ]).astype("float32")  # shape (1, 15)

    # ── 7. Meta-learner ───────────────────────────────────────────────────────
    mX    = np.hstack([proba_cols, struct_vec.reshape(1, -1)])
    proba = art["meta"].predict_proba(mX)[0]   # shape (3,) → [LOW, MED, HIGH]

    # ── 8. Threshold cascade ──────────────────────────────────────────────────
    ph = proba[2]   # HIGH probability
    pl = proba[0]   # LOW  probability

    if ph >= TH:
        pred_idx = 2
    elif pl >= TL:
        pred_idx = 0
    else:
        pred_idx = np.argmax(proba)

    # ── 9. Override layers ────────────────────────────────────────────────────
    override_reason: str | None = None

    # Layer 1 — red flag floor
    if has_red_flag and pred_idx < 2:
        pred_idx       = 2
        override_reason = "red_flag_override"

    # Layer 2 — dx resuscitation flags (passed via rf_flags)
    dx_override_cols = cfg.get("dx_override_cols", ["dx_resus", "dx_intubate", "dx_centline"])
    if any((rf_flags or {}).get(col, 0) for col in dx_override_cols):
        pred_idx       = 2
        override_reason = override_reason or "dx_override"

    # Layer 3 — complaint pattern
    if art["complaint_pattern"].search(symptoms or clinical_note):
        pred_idx       = 2
        override_reason = override_reason or "complaint_override"

    # ── 10. Map to label ──────────────────────────────────────────────────────
    label_map    = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
    severity     = label_map[pred_idx]
    matched_rules = [override_reason] if override_reason else []

    # ── 11. Build scores dict matching rule-based shape ───────────────────────
    scores = {
        "CRITICAL": 0.0,
        "HIGH":     round(float(proba[2]), 4),
        "MEDIUM":   round(float(proba[1]), 4),
        "LOW":      round(float(proba[0]), 4),
    }

    # ── 12. Priority score (reuse rule-based bands for consistency) ───────────
    SCORE_BANDS = {"CRITICAL": 80.0, "HIGH": 60.0, "MEDIUM": 40.0, "LOW": 0.0}
    priority_score = round(SCORE_BANDS[severity] + float(proba[pred_idx]) * 19.9, 4)

    return {
        "severity":        severity,
        "priority_score":  priority_score,
        "scores":          scores,
        "matched_rules":   matched_rules,
        "critical_trigger": None,   # CRITICAL is handled upstream by rule-based
    }