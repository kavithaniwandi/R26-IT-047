import sys
import json
import hashlib
import platform
import time
import os

import numpy as np
import pandas as pd
import scipy
import sklearn
import joblib

from scipy.sparse import coo_matrix, csr_matrix, hstack
from scipy.sparse.csgraph import connected_components
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, r2_score

REQUIRED_PYTHON = (3, 10)
REQUIRED_NUMPY = "1.26.4"
REQUIRED_SKLEARN = "1.7.2"

if sys.version_info[:2] != REQUIRED_PYTHON:
    raise RuntimeError(f"Python {REQUIRED_PYTHON} required, found {sys.version.split()[0]}")
if np.__version__ != REQUIRED_NUMPY:
    raise RuntimeError(f"numpy {REQUIRED_NUMPY} required, found {np.__version__}")
if sklearn.__version__ != REQUIRED_SKLEARN:
    raise RuntimeError(f"scikit-learn {REQUIRED_SKLEARN} required, found {sklearn.__version__}")

DATA_PATH = sys.argv[1]
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "appeal_quality_v3"

SEED = 42
N_FOLDS = 5
NEAR_DUPLICATE_THRESHOLD = 0.8
TOLERANCE_MARGIN = 0.005
TOLERANCE_CANDIDATES = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
LANGUAGES = ["English", "Sinhala", "Tamil"]
LABELS = {"high", "low", "medium"}
HAND_NAMES = [
    "log_text_len", "log_word_count", "avg_word_len",
    "sentence_count", "avg_sent_len", "exclamation_count",
    "question_count", "digit_ratio", "upper_ratio",
    "has_currency", "has_donate_word", "is_sinhala", "is_tamil",
]
LANG_SPEC = {
    "English": dict(key="en", analyzer="word", ngram=(1, 2), max_features=25_000, lsa=150),
    "Sinhala": dict(key="si", analyzer="char_wb", ngram=(3, 5), max_features=8_000, lsa=50),
    "Tamil": dict(key="ta", analyzer="char_wb", ngram=(3, 5), max_features=8_000, lsa=50),
}

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def band(score):
    if score <= 2.0:
        return "low"
    if score <= 3.0:
        return "medium"
    return "high"


def resolve_labels(scores, probas, classes, tolerance):
    classes = np.asarray(classes)
    out = []
    for score, proba in zip(scores, probas):
        score_label = band(score)
        clf_label = classes[int(np.argmax(proba))]
        if score_label == clf_label:
            out.append(score_label)
        elif abs(score - 2.0) < tolerance or abs(score - 3.0) < tolerance:
            out.append(clf_label)
        else:
            out.append(score_label)
    return np.array(out)


def extract_handcrafted(frame):
    t = frame["appeal_text"].astype(str)
    f = pd.DataFrame(index=frame.index)
    f["log_text_len"] = np.log1p(t.str.len())
    f["log_word_count"] = np.log1p(t.str.split().str.len())
    f["avg_word_len"] = t.str.len() / (t.str.split().str.len() + 1)
    f["sentence_count"] = np.log1p(t.str.count(r"[.!?।]") + 1)
    f["avg_sent_len"] = t.str.split().str.len() / (t.str.count(r"[.!?།]") + 2)
    f["exclamation_count"] = np.log1p(t.str.count(r"!"))
    f["question_count"] = np.log1p(t.str.count(r"\?"))
    f["digit_ratio"] = t.str.count(r"\d") / (t.str.len() + 1)
    f["upper_ratio"] = t.str.count(r"[A-Z]") / (t.str.len() + 1)
    f["has_currency"] = t.str.contains(r"[$£€Rs\d]", regex=True).astype(int)
    f["has_donate_word"] = t.str.contains(
        r"donat|contribut|help|support|give|fund|රුපියල්|දීමනා|நன்கொடை",
        case=False, regex=True,
    ).astype(int)
    f["is_sinhala"] = (frame["language"] == "Sinhala").astype(int)
    f["is_tamil"] = (frame["language"] == "Tamil").astype(int)
    return f[HAND_NAMES].fillna(0).values.astype(float)


def load_corpus(path):
    raw = pd.read_csv(path)
    required = ["appeal_text", "quality_label", "overall_quality_score", "language"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise RuntimeError(f"Missing columns: {missing}")
    n_raw = len(raw)
    df = raw.dropna(subset=["appeal_text", "quality_label", "overall_quality_score"]).copy()
    df["appeal_text"] = df["appeal_text"].astype(str).str.strip()
    df["quality_label"] = df["quality_label"].astype(str).str.strip().str.lower()
    df["language"] = df["language"].astype(str).str.strip()
    df["overall_quality_score"] = pd.to_numeric(df["overall_quality_score"], errors="coerce")
    df = df.dropna(subset=["overall_quality_score"])
    df = df[df["appeal_text"].str.len() > 10]
    bad_labels = set(df["quality_label"].unique()) - LABELS
    if bad_labels:
        raise RuntimeError(f"Unexpected labels: {bad_labels}")
    bad_lang = set(df["language"].unique()) - set(LANGUAGES)
    if bad_lang:
        raise RuntimeError(f"Unexpected languages: {bad_lang}")
    if df["overall_quality_score"].min() < 1 or df["overall_quality_score"].max() > 5:
        raise RuntimeError("overall_quality_score outside 1..5")
    n_clean = len(df)
    df = df.drop_duplicates(subset=["appeal_text"], keep="first")
    n_nodup = len(df)
    df = df.reset_index(drop=True)
    info = dict(rows_in_file=int(n_raw), rows_after_cleaning=int(n_clean),
                rows_after_exact_duplicate_removal=int(n_nodup), corpus_rows=int(len(df)))
    return df, info


def build_groups(df):
    groups = np.full(len(df), -1, dtype=int)
    offset = 0
    for lang in LANGUAGES:
        idx = np.where(df["language"].values == lang)[0]
        if len(idx) == 0:
            continue
        spec = LANG_SPEC[lang]
        vec = TfidfVectorizer(analyzer=spec["analyzer"], ngram_range=spec["ngram"],
                              sublinear_tf=True, min_df=2)
        X = vec.fit_transform(df.loc[idx, "appeal_text"]).tocsr()
        rows, cols = [], []
        step = 500
        XT = X.T.tocsc()
        for start in range(0, X.shape[0], step):
            sim = (X[start:start + step] @ XT).tocoo()
            mask = (sim.data >= NEAR_DUPLICATE_THRESHOLD) & (sim.row + start != sim.col)
            rows.append(sim.row[mask] + start)
            cols.append(sim.col[mask])
        rows = np.concatenate(rows) if rows else np.array([], dtype=int)
        cols = np.concatenate(cols) if cols else np.array([], dtype=int)
        graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(idx), len(idx)))
        _, labels = connected_components(graph, directed=False)
        groups[idx] = labels + offset
        offset += labels.max() + 1
    if (groups < 0).any():
        raise RuntimeError("Group assignment failed")
    return groups


def fit_components(train_df):
    comps = {}
    for lang in LANGUAGES:
        spec = LANG_SPEC[lang]
        texts = train_df.loc[train_df["language"] == lang, "appeal_text"]
        vec = TfidfVectorizer(analyzer=spec["analyzer"], ngram_range=spec["ngram"],
                              max_features=spec["max_features"], sublinear_tf=True,
                              strip_accents=None, min_df=3)
        Xl = vec.fit_transform(texts)
        svd = TruncatedSVD(n_components=spec["lsa"], random_state=SEED)
        svd.fit(Xl)
        comps[spec["key"]] = (vec, svd)
    scaler = StandardScaler()
    scaler.fit(extract_handcrafted(train_df))
    comps["scaler"] = scaler
    return comps


def featurize(df, comps):
    n = len(df)
    hand = comps["scaler"].transform(extract_handcrafted(df))
    blocks = []
    lsa_blocks = []
    col_offset = 0
    rows_all, cols_all, data_all = [], [], []
    for lang in LANGUAGES:
        spec = LANG_SPEC[lang]
        vec, svd = comps[spec["key"]]
        idx = np.where(df["language"].values == lang)[0]
        width = len(vec.vocabulary_)
        lsa_full = np.zeros((n, spec["lsa"]))
        if len(idx):
            Xl = vec.transform(df["appeal_text"].values[idx]).tocoo()
            rows_all.append(idx[Xl.row])
            cols_all.append(Xl.col + col_offset)
            data_all.append(Xl.data)
            lsa_full[idx] = svd.transform(Xl.tocsr())
        lsa_blocks.append(lsa_full)
        col_offset += width
    tfidf_full = coo_matrix(
        (np.concatenate(data_all), (np.concatenate(rows_all), np.concatenate(cols_all))),
        shape=(n, col_offset),
    ).tocsr()
    X_clf = hstack([csr_matrix(hand), tfidf_full]).tocsr()
    X_reg_base = np.hstack([hand] + lsa_blocks)
    return X_clf, X_reg_base


def make_base_clf():
    return RandomForestClassifier(
        n_estimators=500, max_depth=20, min_samples_leaf=5,
        max_features="sqrt", class_weight="balanced",
        random_state=SEED, n_jobs=-1,
    )


def make_reg():
    return GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=SEED,
    )


def inner_splits(y, groups):
    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    return [(tr, va) for tr, va in sgkf.split(np.zeros(len(y)), y, groups)]


def fit_pipeline(train_df, y_train, s_train, g_train):
    comps = fit_components(train_df)
    X_clf, X_reg_base = featurize(train_df, comps)
    splits = inner_splits(y_train, g_train)
    clf = CalibratedClassifierCV(make_base_clf(), method="isotonic", cv=splits)
    clf.fit(X_clf, y_train)
    n_classes = len(clf.classes_)
    oof_proba = np.zeros((X_clf.shape[0], n_classes))
    for (tr, va), cal in zip(splits, clf.calibrated_classifiers_):
        oof_proba[va] = cal.predict_proba(X_clf[va])
    X_reg = np.hstack([oof_proba, X_reg_base])
    reg_tr, reg_va = splits[0]
    reg = make_reg()
    reg.fit(X_reg[reg_tr], s_train[reg_tr])
    raw_va = np.clip(reg.predict(X_reg[reg_va]), 1.0, 5.0)
    iso = IsotonicRegression(y_min=1.0, y_max=5.0, out_of_bounds="clip")
    iso.fit(raw_va, s_train[reg_va])
    return dict(comps=comps, clf=clf, reg=reg, iso=iso)


def predict_pipeline(pipe, df):
    X_clf, X_reg_base = featurize(df, pipe["comps"])
    proba = pipe["clf"].predict_proba(X_clf)
    raw = np.clip(pipe["reg"].predict(np.hstack([proba, X_reg_base])), 1.0, 5.0)
    score = pipe["iso"].predict(raw)
    return proba, score


log(f"python {platform.python_version()} numpy {np.__version__} sklearn {sklearn.__version__} "
    f"scipy {scipy.__version__} pandas {pd.__version__} joblib {joblib.__version__}")

df, load_info = load_corpus(DATA_PATH)
log(f"corpus: {load_info}")
print(df.groupby(["language", "quality_label"]).size().unstack(fill_value=0))

le = LabelEncoder()
y = le.fit_transform(df["quality_label"])
s = df["overall_quality_score"].values.astype(float)
classes = le.classes_.tolist()
log(f"label classes: {classes}")

groups = build_groups(df)
log(f"near-duplicate groups: {len(np.unique(groups))} for {len(df)} rows "
    f"(largest group {np.bincount(groups).max()})")

strat = (df["language"] + "_" + df["quality_label"]).values
sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
dev_idx, test_idx = next(iter(sgkf.split(np.zeros(len(df)), strat, groups)))
if set(groups[dev_idx]) & set(groups[test_idx]):
    raise RuntimeError("Group leakage between development and test sets")
dev_df = df.iloc[dev_idx].reset_index(drop=True)
test_df = df.iloc[test_idx].reset_index(drop=True)
y_dev, y_test = y[dev_idx], y[test_idx]
s_dev, s_test = s[dev_idx], s[test_idx]
g_dev = groups[dev_idx]
if len(set(y_test)) != 3:
    raise RuntimeError("Test set is missing a class")
log(f"development rows: {len(dev_df)}  held-out test rows: {len(test_df)}")
print(test_df.groupby(["language", "quality_label"]).size().unstack(fill_value=0))

log("cross-validation on development rows (tolerance selection)")
cv_splits = inner_splits(y_dev, g_dev)
oof_proba = np.zeros((len(dev_df), len(classes)))
oof_score = np.zeros(len(dev_df))
fold_of = np.zeros(len(dev_df), dtype=int)
for k, (tr, va) in enumerate(cv_splits):
    pipe = fit_pipeline(dev_df.iloc[tr].reset_index(drop=True), y_dev[tr], s_dev[tr], g_dev[tr])
    p, sc = predict_pipeline(pipe, dev_df.iloc[va].reset_index(drop=True))
    oof_proba[va] = p
    oof_score[va] = sc
    fold_of[va] = k
    clf_acc = (p.argmax(axis=1) == y_dev[va]).mean()
    log(f"  fold {k + 1}/{N_FOLDS}: classifier accuracy {clf_acc:.4f}")

true_dev_labels = le.inverse_transform(y_dev)
tol_table = {}
for tol in TOLERANCE_CANDIDATES:
    lab = resolve_labels(oof_score, oof_proba, classes, tol)
    tol_table[tol] = float((lab == true_dev_labels).mean())
top_acc = max(tol_table.values())
best_tol = min(t for t in TOLERANCE_CANDIDATES if tol_table[t] >= top_acc - TOLERANCE_MARGIN)
log("tolerance sweep on cross-validated predictions (true labels):")
for tol in TOLERANCE_CANDIDATES:
    log(f"  tolerance {tol:.2f}: accuracy {tol_table[tol]:.4f}{'  <- selected' if tol == best_tol else ''}")
final_oof = resolve_labels(oof_score, oof_proba, classes, best_tol)
cv_fold_acc = [float((final_oof[fold_of == k] == true_dev_labels[fold_of == k]).mean())
               for k in range(N_FOLDS)]
cv_clf_acc = [float((oof_proba[fold_of == k].argmax(axis=1) == y_dev[fold_of == k]).mean())
              for k in range(N_FOLDS)]
log(f"cross-validated accuracy (selected tolerance): {np.mean(cv_fold_acc):.4f} +/- {np.std(cv_fold_acc):.4f}")

log("training final model on all development rows")
final = fit_pipeline(dev_df, y_dev, s_dev, g_dev)

os.makedirs(OUT_DIR, exist_ok=True)
config = {
    "label_classes": classes,
    "boundary_tolerance": best_tol,
    "lsa_components": {"en": 150, "si": 50, "ta": 50},
    "scaler_feature_names": HAND_NAMES,
}
artifact_files = {
    "appeal_quality_vectorizer.joblib": final["comps"]["en"][0],
    "appeal_quality_vectorizer_si.joblib": final["comps"]["si"][0],
    "appeal_quality_vectorizer_ta.joblib": final["comps"]["ta"][0],
    "appeal_quality_svd_en.joblib": final["comps"]["en"][1],
    "appeal_quality_svd_si.joblib": final["comps"]["si"][1],
    "appeal_quality_svd_ta.joblib": final["comps"]["ta"][1],
    "appeal_quality_scaler.joblib": final["comps"]["scaler"],
    "appeal_quality_classifier.joblib": final["clf"],
    "appeal_quality_label_encoder.joblib": le,
    "appeal_quality_regressor.joblib": final["reg"],
    "appeal_quality_isotonic.joblib": final["iso"],
    "appeal_quality_config.joblib": config,
}
for name, obj in artifact_files.items():
    joblib.dump(obj, os.path.join(OUT_DIR, name))
log(f"saved {len(artifact_files)} artifacts to {OUT_DIR}")

reloaded = dict(
    comps=dict(
        en=(joblib.load(os.path.join(OUT_DIR, "appeal_quality_vectorizer.joblib")),
            joblib.load(os.path.join(OUT_DIR, "appeal_quality_svd_en.joblib"))),
        si=(joblib.load(os.path.join(OUT_DIR, "appeal_quality_vectorizer_si.joblib")),
            joblib.load(os.path.join(OUT_DIR, "appeal_quality_svd_si.joblib"))),
        ta=(joblib.load(os.path.join(OUT_DIR, "appeal_quality_vectorizer_ta.joblib")),
            joblib.load(os.path.join(OUT_DIR, "appeal_quality_svd_ta.joblib"))),
        scaler=joblib.load(os.path.join(OUT_DIR, "appeal_quality_scaler.joblib")),
    ),
    clf=joblib.load(os.path.join(OUT_DIR, "appeal_quality_classifier.joblib")),
    reg=joblib.load(os.path.join(OUT_DIR, "appeal_quality_regressor.joblib")),
    iso=joblib.load(os.path.join(OUT_DIR, "appeal_quality_isotonic.joblib")),
)
reloaded_cfg = joblib.load(os.path.join(OUT_DIR, "appeal_quality_config.joblib"))
reloaded_le = joblib.load(os.path.join(OUT_DIR, "appeal_quality_label_encoder.joblib"))

log("evaluating once on the held-out test set using the reloaded artifacts")
proba_t, score_t = predict_pipeline(reloaded, test_df)
proba_mem, score_mem = predict_pipeline(final, test_df)
if not (np.allclose(proba_t, proba_mem) and np.allclose(score_t, score_mem)):
    raise RuntimeError("Reloaded artifacts do not reproduce in-memory predictions")
if reloaded_le.classes_.tolist() != classes or reloaded_cfg["label_classes"] != classes:
    raise RuntimeError("Label order mismatch")
pred_labels = resolve_labels(score_t, proba_t, reloaded_cfg["label_classes"],
                             reloaded_cfg["boundary_tolerance"])
true_labels = le.inverse_transform(y_test)
clf_labels = le.inverse_transform(proba_t.argmax(axis=1))
correct = pred_labels == true_labels
test_acc = float(correct.mean())
clf_only_acc = float((clf_labels == true_labels).mean())
band_only_acc = float((np.array([band(v) for v in score_t]) == true_labels).mean())
majority = pd.Series(true_labels).value_counts(normalize=True).max()
consistent = float((pred_labels == np.array([band(v) for v in score_t])).mean())

per_lang = {}
for lang in LANGUAGES:
    m = test_df["language"].values == lang
    per_lang[lang] = dict(n=int(m.sum()), accuracy=float(correct[m].mean()) if m.any() else None)
report = classification_report(true_labels, pred_labels, output_dict=True, zero_division=0)
cm = confusion_matrix(true_labels, pred_labels, labels=sorted(LABELS)).tolist()

metrics = dict(
    test_accuracy=test_acc,
    test_rows=int(len(test_df)),
    test_rows_correct=int(correct.sum()),
    test_label_matches_score_band=consistent,
    test_macro_f1=float(report["macro avg"]["f1-score"]),
    test_classifier_only_accuracy=clf_only_acc,
    test_score_band_only_accuracy=band_only_acc,
    majority_class_baseline=float(majority),
    test_score_mae=float(mean_absolute_error(s_test, score_t)),
    test_score_r2=float(r2_score(s_test, score_t)),
    per_language=per_lang,
    per_class={k: report[k] for k in sorted(LABELS)},
    confusion_matrix_labels=sorted(LABELS),
    confusion_matrix=cm,
    cv_accuracy_mean=float(np.mean(cv_fold_acc)),
    cv_accuracy_std=float(np.std(cv_fold_acc)),
    cv_fold_accuracy=cv_fold_acc,
    cv_classifier_only_fold_accuracy=cv_clf_acc,
    tolerance_sweep={str(k): v for k, v in tol_table.items()},
    selected_boundary_tolerance=best_tol,
)
with open(os.path.join(OUT_DIR, "metrics.json"), "w") as fh:
    json.dump(metrics, fh, indent=2)

pd.DataFrame(dict(
    language=test_df["language"], true_label=true_labels, classifier_label=clf_labels, final_label=pred_labels,
    true_score=s_test, predicted_score=np.round(score_t, 4), correct=correct,
)).to_csv(os.path.join(OUT_DIR, "test_predictions.csv"), index=False)

manifest = dict(
    created_utc=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    data_file=os.path.basename(DATA_PATH),
    data_sha256=sha256_file(DATA_PATH),
    load_info=load_info,
    development_rows=int(len(dev_df)),
    test_rows=int(len(test_df)),
    protocol=dict(
        seed=SEED, folds=N_FOLDS, near_duplicate_threshold=NEAR_DUPLICATE_THRESHOLD,
        tolerance_margin=TOLERANCE_MARGIN, splitter="StratifiedGroupKFold",
        test_set="first fold, used once, after tolerance selection",
        shipped_model_trained_on="development rows only",
    ),
    environment=dict(
        python=platform.python_version(), numpy=np.__version__, scikit_learn=sklearn.__version__,
        scipy=scipy.__version__, pandas=pd.__version__, joblib=joblib.__version__,
    ),
    artifacts={name: sha256_file(os.path.join(OUT_DIR, name)) for name in artifact_files},
    selected_boundary_tolerance=best_tol,
    test_accuracy=test_acc,
)
with open(os.path.join(OUT_DIR, "manifest.json"), "w") as fh:
    json.dump(manifest, fh, indent=2)

log("RELOAD CHECK PASSED")
log(f"outputs written to {OUT_DIR}: 12 artifacts, metrics.json, manifest.json, test_predictions.csv")
