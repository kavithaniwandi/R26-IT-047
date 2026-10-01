"""severity_pipeline.py - SDRDCS Subsystem 3: features, 5-model stack, decision policy (training AND backend)."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MaxAbsScaler
from sklearn.utils.class_weight import compute_sample_weight

LABELS = ["LOW", "MEDIUM", "HIGH"]
LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
KNOWN_FLAGS = ["breathing_difficulty", "chest_pain", "focal_neurologic_deficit",
               "active_bleeding", "syncope", "seizure"]
VITAL_COLS = ["vital_hr", "vital_spo2", "vital_sbp", "vital_rr", "vital_temp", "pain_score"]
VITAL_THRESHOLDS = {
    "vf_bradycardia": ("vital_hr", "<", 50), "vf_hypox_severe": ("vital_spo2", "<", 90),
    "vf_hypox_moderate": ("vital_spo2", "<", 94), "vf_hypotension": ("vital_sbp", "<", 90),
    "vf_hypertension_crit": ("vital_sbp", ">", 180), "vf_tachypnea_severe": ("vital_rr", ">", 24),
    "vf_bradypnea": ("vital_rr", "<", 10), "vf_hypothermia": ("vital_temp", "<", 35.0),
    "vf_high_fever": ("vital_temp", ">", 38.5), "vf_pain_severe": ("pain_score", ">=", 8),
    "vf_pain_none": ("pain_score", "==", 0),
}
HIGH_COMPLAINT_PATTERNS = [
    "crush injury", "head trauma", "heart failure", "pregnancy complication", "traumatic brain injury",
    "head injury", "drowning", "electric shock", "gunshot wound", "stab wound", "chest trauma",
    "spinal injury", "paralysis weakness one side", "stroke", "seizure convulsion", "anaphylaxis"]
_KEEP = {"of", "in", "and", "or", "not", "no", "with", "without", "upper", "lower",
         "left", "right", "bilateral", "acute", "chronic"}
_STOP = [w for w in ENGLISH_STOP_WORDS if w not in _KEEP]


def clean_text(text) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"symptoms:\s*", "", text.lower())
    text = re.sub(r"[^a-z0-9_ ]", " ", text.replace("|", " "))
    return re.sub(r"\s+", " ", text).strip()


def split_complaints(text):
    if not isinstance(text, str):
        return []
    parts = [re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_ ]", " ", p.lower())).strip() for p in text.split("|")]
    return [p for p in parts if p]


class FeatureBuilder:
    """fit() on TRAIN ONLY. Missing vitals -> train-only medians + miss_* indicators (no labels used)."""

    def __init__(self, max_tfidf_features=8000, min_complaint_count=3):
        self.max_tfidf_features, self.min_complaint_count = max_tfidf_features, min_complaint_count

    def fit(self, df):
        text = df["symptoms"].map(clean_text)
        self.tfidf_ = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.90,
                                      max_features=self.max_tfidf_features, sublinear_tf=True,
                                      stop_words=_STOP).fit(text)
        self.complaint_vec_ = CountVectorizer(tokenizer=split_complaints, lowercase=False, token_pattern=None,
                                              binary=True, min_df=self.min_complaint_count).fit(df["symptoms"])
        self.age_median_ = float(pd.to_numeric(df["age"], errors="coerce").median())
        self.vital_medians_ = {c: float(pd.to_numeric(df[c], errors="coerce").median()) for c in VITAL_COLS}
        dense, self.dense_names_ = self._dense(df)
        self.scaler_ = MaxAbsScaler().fit(hstack([self.tfidf_.transform(text), csr_matrix(dense)]).tocsr())
        return self


    def _dense(self, df):
        cols, names = [], []

        def add(name, values):
            names.append(name); cols.append(np.asarray(values, dtype="float32").reshape(-1))

        age = pd.to_numeric(df["age"], errors="coerce").fillna(getattr(self, "age_median_", 35.0)).clip(0, 110)
        add("age_n", age / 100.0); add("age_infant", age < 1); add("age_child", age < 5)
        add("age_elderly", age >= 65); add("age_very_old", age >= 80)
        sym = df["symptoms"].fillna("").astype(str)
        add("n_complaints", sym.map(lambda s: len(split_complaints(s))))
        add("n_words", sym.map(lambda s: len(clean_text(s).split())))
        rf_total = np.zeros(len(df), dtype="float32")
        for f in KNOWN_FLAGS:
            v = pd.to_numeric(df[f"rf_{f}"], errors="coerce").fillna(0).values if f"rf_{f}" in df else np.zeros(len(df))
            add(f"rf_{f}", v); rf_total += (v > 0).astype("float32")
        has_rf = pd.to_numeric(df["has_red_flag"], errors="coerce").fillna(0).values if "has_red_flag" in df else rf_total
        add("has_red_flag", (np.asarray(has_rf) > 0) | (rf_total > 0)); add("red_flag_count", rf_total)
        raw = {c: (pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index))
               for c in VITAL_COLS}
        for c in VITAL_COLS:
            add(f"miss_{c}", raw[c].isna())
        for c in VITAL_COLS:
            add(c, raw[c].fillna(self.vital_medians_.get(c, np.nan)))
        flags = {}
        for name, (col, op, val) in VITAL_THRESHOLDS.items():
            v = raw[col]
            m = {"<": v < val, ">": v > val, ">=": v >= val, "==": v == val}[op]
            flags[name] = (m & v.notna()).astype(float); add(name, flags[name])
        crit = ["vf_hypox_severe", "vf_hypotension", "vf_bradycardia", "vf_hypothermia"]
        danger = crit + ["vf_tachypnea_severe", "vf_bradypnea"]
        add("vf_critical_vital", pd.concat([flags[c] for c in crit], axis=1).max(axis=1))
        add("vf_any_danger", pd.concat([flags[c] for c in danger], axis=1).max(axis=1))
        return np.column_stack(cols).astype("float32"), names


    def transform(self, df):
        df = df.reset_index(drop=True)
        dense, _ = self._dense(df)
        X_lin = self.scaler_.transform(
            hstack([self.tfidf_.transform(df["symptoms"].map(clean_text)), csr_matrix(dense)]).tocsr()).astype("float32")
        X_tree = np.hstack([dense, self.complaint_vec_.transform(df["symptoms"]).toarray()]).astype("float32")
        return X_lin, X_tree


BASE_NAMES = ["lr_a", "lr_b", "lr_c", "lgb", "xgb"]
BASE_INPUT = {"lr_a": "lin", "lr_b": "lin", "lr_c": "lin", "lgb": "tree", "xgb": "tree"}


def make_base(name, seed=42):
    if name.startswith("lr_"):
        C = {"lr_a": 0.3, "lr_b": 0.1, "lr_c": 0.05}[name]
        return LogisticRegression(C=C, max_iter=2000, class_weight="balanced", solver="lbfgs", random_state=seed)
    if name == "lgb":
        import lightgbm as lgb
        return lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                  class_weight="balanced", random_state=seed, verbosity=-1, n_jobs=-1)
    import xgboost as xgb
    return xgb.XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=5, min_child_weight=3, gamma=0.1,
                             subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, objective="multi:softprob",
                             eval_metric="mlogloss", tree_method="hist", random_state=seed, verbosity=0, n_jobs=-1)


def fit_base(name, X_lin, X_tree, y, seed=42):
    model, X = make_base(name, seed), (X_lin if BASE_INPUT[name] == "lin" else X_tree)
    if name == "xgb":
        model.fit(X, y, sample_weight=compute_sample_weight("balanced", y))
    else:
        model.fit(X, y)
    return model


def base_probabilities(models, X_lin, X_tree):
    return np.hstack([models[n].predict_proba(X_lin if BASE_INPUT[n] == "lin" else X_tree) for n in BASE_NAMES])


def meta_features(base_proba):
    return np.log(np.clip(base_proba, 1e-6, 1.0))


def threshold_cascade(proba, t_high, t_low):
    pred = np.argmax(proba, axis=1).copy()
    pred[proba[:, 2] >= t_high] = 2
    pred[(proba[:, 0] >= t_low) & (proba[:, 2] < t_high)] = 0
    return pred


_COMPLAINT_RE = re.compile("|".join(re.escape(p) for p in HIGH_COMPLAINT_PATTERNS), re.I)


def safety_masks(df):
    df = df.reset_index(drop=True)
    rf = np.zeros(len(df), dtype=bool)
    if "has_red_flag" in df:
        rf |= pd.to_numeric(df["has_red_flag"], errors="coerce").fillna(0).values > 0
    for f in KNOWN_FLAGS:
        if f"rf_{f}" in df:
            rf |= pd.to_numeric(df[f"rf_{f}"], errors="coerce").fillna(0).values > 0
    return {"red_flag": rf, "complaint": df["symptoms"].fillna("").astype(str).str.contains(_COMPLAINT_RE).values}


def apply_safety_layers(pred, df, layers=("red_flag", "complaint")):
    pred, masks = pred.copy(), safety_masks(df)
    for layer in layers:
        pred[masks[layer]] = 2          # floor to HIGH; never lowers a prediction
    return pred


class StackBundle:
    """Everything the backend needs: features + 5 base models (full-train) + meta-learner + thresholds."""

    def __init__(self, features, base_models, meta, t_high, t_low, layers=("red_flag", "complaint")):
        self.features, self.base_models, self.meta = features, base_models, meta
        self.t_high, self.t_low, self.layers = t_high, t_low, tuple(layers)

    def predict_proba(self, df):
        X_lin, X_tree = self.features.transform(df)
        return self.meta.predict_proba(meta_features(base_probabilities(self.base_models, X_lin, X_tree)))

    def predict(self, df, use_layers=True):
        proba = self.predict_proba(df)
        model_pred = threshold_cascade(proba, self.t_high, self.t_low)
        final = apply_safety_layers(model_pred, df, self.layers) if use_layers else model_pred
        return {"proba": proba, "model_pred": model_pred, "final_pred": final,
                "final_labels": [LABELS[i] for i in final], "layer_masks": safety_masks(df)}


def row_from_request(symptoms, age=None, rf_flags=None, vitals=None):
    """One-row DataFrame for a classify request (symptoms like 'Chest pain | Cough')."""
    rf_flags = rf_flags or {}
    row = {"symptoms": symptoms or "", "age": np.nan if age is None else float(age)}
    for f in KNOWN_FLAGS:
        row[f"rf_{f}"] = int(bool(rf_flags.get(f, 0)))
    row["red_flag_count"] = sum(row[f"rf_{f}"] for f in KNOWN_FLAGS)
    row["has_red_flag"] = int(row["red_flag_count"] > 0)
    for c in VITAL_COLS:
        row[c] = (vitals or {}).get(c, np.nan)
    return pd.DataFrame([row])


def load_bundle(path):
    import sys, joblib
    sys.modules.setdefault("severity_pipeline", sys.modules[__name__])   # works if imported under another path
    return joblib.load(path)


