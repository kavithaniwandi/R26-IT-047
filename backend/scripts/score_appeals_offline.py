"""
Offline appeal scoring script.
Reads appeals from tests/data/offline_appeals.csv and scores each one using the
local ML model only. Makes NO API calls.

Prints per-language tables (English / Sinhala / Tamil) each with live and
template sub-groups, followed by per-language summary stats. No pooled means.

Usage (from the backend/ directory):
    backend/venv/Scripts/python.exe scripts/score_appeals_offline.py
    backend/venv/Scripts/python.exe scripts/score_appeals_offline.py --debug-text "some appeal"
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import numpy as np
from scipy.sparse import csr_matrix, hstack

from app.models.quality_service import _load_artifacts, _handcrafted, _normalise_language


DATA_FILE = Path(__file__).resolve().parent.parent / "tests" / "data" / "offline_appeals.csv"


# ---------------------------------------------------------------------------
# Internal diagnostic scorer — exposes intermediate pipeline values
# ---------------------------------------------------------------------------

def _score_debug(text: str, language: str = "English") -> dict:
    """Full internal diagnostics: raw probabilities, regressor, isotonic, predicted class."""
    art = _load_artifacts()
    lang = _normalise_language(language)
    lsa_cfg = art["cfg"]["lsa_components"]

    hand_raw = _handcrafted(text, lang, art)
    hand_scaled = art["scaler"].transform(hand_raw)

    if lang == "Sinhala":
        tfidf_feat = art["tfidf_si"].transform([text])
        lsa_en = np.zeros((1, lsa_cfg["en"]))
        lsa_si = art["svd_si"].transform(tfidf_feat)
        lsa_ta = np.zeros((1, lsa_cfg["ta"]))
        clf_tfidf_en, clf_tfidf_si, clf_tfidf_ta = art["ZERO_EN"], tfidf_feat, art["ZERO_TA"]
    elif lang == "Tamil":
        tfidf_feat = art["tfidf_ta"].transform([text])
        lsa_en = np.zeros((1, lsa_cfg["en"]))
        lsa_si = np.zeros((1, lsa_cfg["si"]))
        lsa_ta = art["svd_ta"].transform(tfidf_feat)
        clf_tfidf_en, clf_tfidf_si, clf_tfidf_ta = art["ZERO_EN"], art["ZERO_SI"], tfidf_feat
    else:
        tfidf_feat = art["tfidf_en"].transform([text])
        lsa_en = art["svd_en"].transform(tfidf_feat)
        lsa_si = np.zeros((1, lsa_cfg["si"]))
        lsa_ta = np.zeros((1, lsa_cfg["ta"]))
        clf_tfidf_en, clf_tfidf_si, clf_tfidf_ta = tfidf_feat, art["ZERO_SI"], art["ZERO_TA"]

    x_clf = hstack([csr_matrix(hand_scaled), clf_tfidf_en, clf_tfidf_si, clf_tfidf_ta])
    proba = art["clf"].predict_proba(x_clf)[0]
    classes = art["le"].classes_

    x_reg = np.hstack([proba.reshape(1, -1), hand_scaled, lsa_en, lsa_si, lsa_ta])
    raw_reg = float(np.clip(art["reg"].predict(x_reg)[0], 1.0, 5.0))
    final = float(np.clip(art["iso"].predict([raw_reg])[0], 1.0, 5.0))

    confidence = float(proba.max())
    pred_class = str(classes[int(np.argmax(proba))])

    return {
        "proba": {c: round(float(p), 4) for c, p in zip(classes, proba)},
        "raw_reg_score": round(raw_reg, 4),
        "final_score": round(final, 2),
        "pred_class": pred_class,
        "confidence": round(confidence, 4),
        "low_confidence": confidence < 0.50,
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

HDR = (
    f"  {'#':>3}  {'Type':8} {'FinalSc':>8} {'RawReg':>7} "
    f"{'ProbHigh':>9} {'ProbMed':>8} {'ProbLow':>8} "
    f"{'PredCls':>8} {'Conf':>6} {'LC':>2}  Preview"
)
SEP = "-" * 120


def _safe_preview(text: str, width: int = 55) -> str:
    enc = sys.stdout.encoding or "ascii"
    return text.encode(enc, errors="replace").decode(enc)[:width]


def _fmt_row(i: int, atype: str, d: dict, text: str) -> str:
    p = d["proba"]
    return (
        f"  {i:>3}  {atype:8} {d['final_score']:8.2f} {d['raw_reg_score']:7.4f} "
        f"{p.get('high', 0):9.4f} {p.get('medium', 0):8.4f} {p.get('low', 0):8.4f} "
        f"{d['pred_class']:>8} {d['confidence']:6.3f} {'*' if d['low_confidence'] else ' ':>2}  "
        f"{_safe_preview(text)}"
    )


# ---------------------------------------------------------------------------
# Per-language report
# ---------------------------------------------------------------------------

def _print_language_section(lang: str, rows: list[dict]) -> None:
    live_rows = [r for r in rows if r["type"] == "live"]
    tmpl_rows = [r for r in rows if r["type"] == "template"]

    print(f"\n{'=' * 120}")
    print(f"  LANGUAGE: {lang}   (live: {len(live_rows)}, template: {len(tmpl_rows)})")

    for group_name, group in [("live", live_rows), ("template", tmpl_rows)]:
        if not group:
            continue
        print(f"\n  -- {group_name.upper()} --")
        print(HDR)
        print(SEP)
        scores = []
        low_conf_n = 0
        for i, row in enumerate(group, 1):
            d = _score_debug(row["text"], lang)
            scores.append(d["final_score"])
            low_conf_n += int(d["low_confidence"])
            print(_fmt_row(i, group_name, d, row["text"]))
        print(SEP)
        if scores:
            mean = sum(scores) / len(scores)
            lo, hi = min(scores), max(scores)
            print(
                f"  {group_name.capitalize()} summary ({lang}): "
                f"n={len(scores)}  mean={mean:.3f}  min={lo:.2f}  max={hi:.2f}  "
                f"low_confidence={low_conf_n}/{len(scores)}"
            )


def debug_single(text: str, language: str = "English") -> None:
    print(f"\n{'=' * 80}")
    print(f"  DIAGNOSTIC — language: {language}")
    print(f"  Text: {text[:120]!r}")
    print(f"{'=' * 80}")
    d = _score_debug(text, language)
    p = d["proba"]
    print(f"  Class probabilities:  high={p.get('high', 0):.4f}  "
          f"medium={p.get('medium', 0):.4f}  low={p.get('low', 0):.4f}")
    print(f"  Raw regressor score:  {d['raw_reg_score']:.4f}")
    print(f"  Final (isotonic):     {d['final_score']:.2f}")
    print(f"  Predicted class:      {d['pred_class']}")
    print(f"  Confidence:           {d['confidence']:.4f}  "
          f"({'LOW' if d['low_confidence'] else 'OK'})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug-text", default=None)
    parser.add_argument("--debug-lang", default="English")
    args = parser.parse_args()

    if args.debug_text:
        debug_single(args.debug_text, args.debug_lang)
        sys.exit(0)

    # Diagnostic text from spec
    debug_single(
        "Families in Nawalapitiya urgently need water bottles and tents for 20 people. "
        "This flood relief campaign aims to Support Affected families and help the "
        "community in need. Our community is coming together to help. Please donate today.",
        "English",
    )

    # Load CSV
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    rows_by_lang: dict[str, list[dict]] = {}
    with open(DATA_FILE, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            lang = row["language"].strip()
            rows_by_lang.setdefault(lang, []).append({
                "type": row["type"].strip(),
                "text": row["text"].strip(),
            })

    for lang in ("English", "Sinhala", "Tamil"):
        if lang in rows_by_lang:
            _print_language_section(lang, rows_by_lang[lang])
