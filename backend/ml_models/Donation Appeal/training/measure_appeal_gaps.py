"""Measure lexical gap checks on the v3 DEVELOPMENT partition only.

Run with backend/venv/Scripts/python.exe -B <this-file> --dataset <csv>.
The original split is reconstructed without importing/running the training script.
No model is trained or changed. Held-out texts are never passed to gap checks.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BASE.parents[1] / "app/models/data/appeal_gap_statistics.json"
CLASSES = ("low", "medium", "high")
MIN_DIFFERENCE = 0.15
MIN_CLASS_ROWS = 30

# These are transparent lexical proxies, not semantic/factual verification.
# In particular the amount rule is independent of the model's has_currency flag.
RULES = {
    "deadline": {
        "description": "Explicit by/before/within time expression; generic 'today' alone is not a deadline.",
        "patterns": {
            "English": r"\b(?:by|before|until)\s+(?:the\s+)?(?:\d|monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|noon|midnight|end\s+of)|\bwithin\s+\d+\s*(?:hours?|days?|weeks?)\b",
            "Sinhala": r"(?:\d+\s*(?:දින|පැය|සති)|(?:අද|හෙට|සඳුදා|සිකුරාදා)).{0,25}(?:පෙර|ඇතුළත|වන විට)|(?:පෙර|ඇතුළත).{0,15}\d+",
            "Tamil": r"(?:\d+\s*(?:நாட்|மணி|வார)|இன்று|நாளை).{0,25}(?:முன்|க்குள்)|(?:முன்|க்குள்).{0,15}\d+",
        },
    },
    "fund_use": {
        "description": "Explicit statement linking donations/funds to buying, providing or a stated use.",
        "patterns": {
            "English": r"\b(?:donations?|funds?|contributions?|money|proceeds)\b.{0,65}\b(?:provid\w*|buy\w*|purchas\w*|used?\s+(?:for|to)|go\s+towards?|cover\w*|fund\w*)\b|\b(?:used?\s+(?:for|to)|go\s+towards?)\b",
            "Sinhala": r"(?:පරිත්‍යාග|අරමුදල්|ආධාර|මුදල්).{0,70}(?:මිලදී|ලබා ද|සපය|භාවිත|වැය)",
            "Tamil": r"(?:நன்கொடை|நிதி|பங்களிப்|பணம்).{0,70}(?:வாங்க|வழங்க|பயன்படு|செலவ|உதவ)",
        },
    },
    "contact_or_verified_organization": {
        "description": "Email/phone/contact instruction or an explicit verified/registered organization claim; does not verify that claim.",
        "common_pattern": r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)",
        "patterns": {
            "English": r"\b(?:contact|call|email|whatsapp|hotline)\b|\b(?:verified|registered|recognized|recognised|accredited)\s+(?:local\s+)?(?:organi[sz]ation|charity|foundation|group)\b|\bred\s+cross\b",
            "Sinhala": r"අමතන්න|සම්බන්ධ වන්න|දුරකථන|විද්‍යුත් තැපැල්|(?:ලියාපදිංචි|තහවුරු කළ).{0,20}(?:සංවිධාන|පදනම)",
            "Tamil": r"தொடர்பு|அழைக்க|தொலைபேசி|மின்னஞ்சல்|(?:பதிவு செய்யப்பட்ட|சரிபார்க்கப்பட்ட).{0,25}(?:அமைப்பு|நிறுவனம்)",
        },
    },
    "concrete_people_or_items": {
        "description": "Numeric quantity directly followed by a people, household or relief-item unit.",
        "patterns": {
            "English": r"\b\d[\d,]*(?:\.\d+)?\s*(?:affected\s+|displaced\s+)?(?:people|persons?|families|households?|children|individuals?|patients?|tents?|bottles?|water\s+bottles?|food\s+packs?|meals?|kits?|packs?|blankets?|litres?|liters?|kg|kilograms?)\b",
            "Sinhala": r"\d[\d,]*\s*(?:දෙනෙකු|දෙනෙක්|පුද්ගල|පවුල්|ළමුන්|ළමයි|දරුවන්|කූඩාරම්|බෝතල්|ආහාර|කිලෝ)|(?:පවුල්|පුද්ගලයින්|දරුවන්|කූඩාරම්|බෝතල්)\s*\d+",
            "Tamil": r"\d[\d,]*\s*(?:பேர்|நபர்|குடும்ப|குழந்தை|கூடார|பாட்டில்|உணவு|லிட்டர்|கிலோ)|(?:குடும்பங்கள்|நபர்கள்|கூடாரங்கள்)\s*\d+",
        },
    },
    "human_detail": {
        "description": "Affected beneficiary group plus an explicit affected/displaced/loss/need expression; not a measure of emotional quality.",
        "all_patterns": {
            "English": [r"\b(?:families|households?|children|parents?|elderly|residents?|people|patients?|community)\b", r"\b(?:affected|displaced|lost|loss|flood\w*|disaster|without|need\w*|struggl\w*)\b"],
            "Sinhala": [r"පවුල්|දරුවන්|ළමුන්|ජනතාව|පුද්ගල|ප්‍රජාව", r"විපත|අවතැන්|අහිමි|අවශ්‍ය|ගංවතුර|පීඩාව"],
            "Tamil": [r"குடும்ப|குழந்தை|மக்கள்|நபர்|சமூக", r"பாதிக்க|இடம்பெயர்|இழந்|தேவை|வெள்ள|பேரிடர்"],
        },
    },
    "specific_call_to_action": {
        "description": "Donation/contribution imperative and a named relief item or service in the text.",
        "all_patterns": {
            "English": [r"\b(?:donate|contribute|give|send|provide|bring|support)\b", r"\b(?:water|tents?|food|rations?|medicine|medical|shelter|clothes|clothing|blankets?|supplies|kits?|meals?|hygiene|bottles?)\b"],
            "Sinhala": [r"පරිත්‍යාග කරන්න|දායක වන්න|ලබා දෙන්න|සහය වන්න|ආධාර කරන්න", r"ජලය|වතුර|කූඩාරම්|ආහාර|ඖෂධ|ඇඳුම්|සනීපාරක්ෂක|බෝතල්"],
            "Tamil": [r"நன்கொடை|வழங்குங்கள்|பங்களியுங்கள்|உதவுங்கள்|அனுப்புங்கள்", r"தண்ணீர்|நீர்|கூடார|உணவு|மருந்து|உடை|போர்வை|சுகாதார|பாட்டில்"],
        },
    },
    "urgency": {
        "description": "Urgency wording; descriptive evidence must not encourage inventing urgency.",
        "patterns": {
            "English": r"\b(?:urgent\w*|immediate\w*|critical\w*|emergency|today|now|without\s+delay|as\s+soon\s+as\s+possible)\b",
            "Sinhala": r"හදිසි|වහාම|කඩිනම්|අදම|දැන්ම|ඉක්මනින්",
            "Tamil": r"அவசர|உடனடி|உடனே|இன்றே|இப்போதே|விரைவாக",
        },
    },
    "length_band": {
        "description": "60 to 250 whitespace-delimited words, inclusive; band fixed before measuring.",
        "word_count": {"min": 60, "max": 250},
    },
    "length_at_least_60": {
        "description": "At least 60 whitespace-delimited words; no upper bound.",
        "word_count": {"min": 60, "max": None},
        "post_hoc_revision": True,
        "revision_reason": "User-requested one-sided revision after the 60-250 band failed English monotonicity; removes the upper-bound confound. Not an independent confirmatory finding.",
    },
    "length_under_60": {
        "description": "Under 60 whitespace-delimited words; complement reported under unchanged criteria.",
        "word_count": {"min": 0, "max": 59},
        "post_hoc_revision": True,
        "revision_reason": "User-requested complementary report for the post-hoc at-least-60 check.",
    },
    "amount_mentioned": {
        "description": "Explicit currency marker next to a number; independent of has_currency. No bare-number match.",
        "common_pattern": r"(?:(?<!\w)(?:LKR|USD|Rs\.?|රු\.?|ரூ\.?)\s*\d[\d,]*(?:\.\d+)?|[$€£]\s*\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s*(?:rupees|dollars|රුපියල්|ரூபாய்)(?!\w))",
    },
}


def matches(text: str, language: str, rule: dict) -> bool:
    flags = re.IGNORECASE | re.DOTALL
    if "word_count" in rule:
        bounds = rule["word_count"]
        return bounds["min"] <= len(text.split()) and (bounds["max"] is None or len(text.split()) <= bounds["max"])
    if "all_patterns" in rule:
        return all(re.search(p, text, flags) for p in rule["all_patterns"][language])
    patterns = [rule.get("common_pattern"), rule.get("patterns", {}).get(language)]
    return any(re.search(p, text, flags) is not None for p in patterns if p)


def development_partition(dataset: Path, manifest: dict) -> tuple[pd.DataFrame, dict]:
    """Reuse only original pure split helpers, never training's top-level code."""
    source_path = BASE / "training/train_quality_v3.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = {"LANGUAGES", "LABELS", "LANG_SPEC", "NEAR_DUPLICATE_THRESHOLD"}
    nodes = [node for node in tree.body if
             (isinstance(node, ast.FunctionDef) and node.name in {"load_corpus", "build_groups"}) or
             (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets))]
    namespace = {"pd": pd, "np": np, "TfidfVectorizer": TfidfVectorizer,
                 "coo_matrix": coo_matrix, "connected_components": connected_components}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)
    if hashlib.sha256(dataset.read_bytes()).hexdigest() != manifest["data_sha256"]:
        raise RuntimeError("Dataset SHA-256 differs from the shipped manifest")
    if sklearn.__version__ != manifest["environment"]["scikit_learn"]:
        raise RuntimeError("Use the manifest scikit-learn version to reproduce the split")
    frame, info = namespace["load_corpus"](dataset)
    if info != manifest["load_info"]:
        raise RuntimeError("Cleaned corpus counts differ from the training manifest")
    groups = namespace["build_groups"](frame)
    protocol = manifest["protocol"]
    splitter = StratifiedGroupKFold(n_splits=protocol["folds"], shuffle=True, random_state=protocol["seed"])
    dev, held_out = next(iter(splitter.split(np.zeros(len(frame)),
                           (frame["language"] + "_" + frame["quality_label"]).values, groups)))
    if set(groups[dev]) & set(groups[held_out]):
        raise RuntimeError("Development/held-out groups overlap")
    if len(dev) != manifest["development_rows"] or len(held_out) != manifest["test_rows"]:
        raise RuntimeError("Split counts differ from the training manifest")
    metadata = {"dataset_sha256": manifest["data_sha256"], "training_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "development_rows": len(dev), "held_out_rows_excluded": len(held_out),
                "development_indices_sha256": hashlib.sha256(np.asarray(dev, dtype="<i8").tobytes()).hexdigest(),
                "protocol": protocol}
    # Held-out rows participate only in reconstructing the ORIGINAL frozen split.
    # No held-out row is measured, inspected for rule design, or written out.
    return frame.iloc[dev].copy(), metadata


def view_statistics(rows, language, rule):
    shares = {}
    for label in CLASSES:
        texts = rows.loc[rows["quality_label"] == label, "appeal_text"]
        count = sum(matches(text, language, rule) for text in texts)
        shares[label] = {"matched": int(count), "total": len(texts), "share": count / len(texts) if len(texts) else None}
    low, medium, high = (shares[c]["share"] for c in CLASSES)
    reasons = []
    if min(shares[c]["total"] for c in CLASSES) < MIN_CLASS_ROWS:
        reasons.append("fewer than 30 rows in a class")
    difference = high - low if high is not None and low is not None else None
    if difference is None or difference < MIN_DIFFERENCE:
        reasons.append("high-low below 15 percentage points")
    if None in (low, medium, high) or not low <= medium <= high:
        reasons.append("not monotonic")
    return {"classes": shares, "high_minus_low": difference, "selected": not reasons,
            "reason": "; ".join(reasons) if reasons else "retained"}


def measure(frame: pd.DataFrame) -> tuple[list, list]:
    kept, dropped = [], []
    human = frame["source"].astype(str).str.upper().isin({
        "MDCC_HUMAN_WRITTEN", "GOFUNDME_PUBLIC_RESEARCH_CORPUS_HUMAN_WRITTEN",
        "PROSOCIAL_HUMAN_WRITTEN", "WEB_SOURCED_HUMAN_WRITTEN"})
    for name, rule in RULES.items():
        statistics, enabled = {}, []
        for language in ("English", "Sinhala", "Tamil"):
            lang = frame[frame["language"] == language]
            stats = view_statistics(lang, language, rule)
            views = {"all_development": dict(stats)}
            if language == "English":
                views["human_written"] = view_statistics(frame[(frame["language"] == language) & human], language, rule)
                stats["selected"] = all(v["selected"] for v in views.values())
                stats["reason"] = "; ".join(f"{view}: {v['reason']}" for view,v in views.items() if not v["selected"]) or "passes both views"
            stats["views"] = views
            stats["evidence_note"] = "English all-development and human-written views" if language == "English" else "not surfaced: likely augmentation artifact"
            stats["surfaced"] = bool(stats["selected"] and language == "English")
            statistics[language] = stats
            if stats["surfaced"]:
                enabled.append(language)
        entry = {"check": name, "rule": rule, "enabled_languages": enabled, "per_language": statistics}
        (kept if any(stat["selected"] for stat in statistics.values()) else dropped).append(entry)
    return kept, dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit-regex", action="store_true", help="Print up to ten development-only English High near-misses per requested rule")
    args = parser.parse_args()
    output = args.output.resolve()
    repository = BASE.parents[2]
    if output != DEFAULT_OUTPUT.resolve():
        raise RuntimeError("Only the dedicated gap-statistics output path is allowed")
    manifest = json.loads((BASE / "v3_retrained/manifest.json").read_text(encoding="utf-8"))
    frame, provenance = development_partition(args.dataset, manifest)
    kept, dropped = measure(frame)
    report = {"schema_version": 1, "provenance": provenance,
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "scipy": scipy.__version__},
              "selection": {"min_class_rows": MIN_CLASS_ROWS, "min_high_minus_low": MIN_DIFFERENCE,
                            "require_monotonic_low_medium_high": True, "selection_scope": "per language; English must pass all-development and human-written views",
                            "english_human_sources": ["MDCC_HUMAN_WRITTEN", "GOFUNDME_PUBLIC_RESEARCH_CORPUS_HUMAN_WRITTEN", "PROSOCIAL_HUMAN_WRITTEN", "WEB_SOURCED_HUMAN_WRITTEN"],
                            "interpretation": "Descriptive lexical associations, not causal gains or factual verification; correlated near-duplicate rows are not independent samples."},
              "checks": kept, "dropped_checks": dropped}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Development rows:", len(frame), "Held-out rows excluded:", provenance["held_out_rows_excluded"])
    print("check | language | view | low | medium | high | high-low | final decision | reason")
    for entry in kept + dropped:
        for language, stats in entry["per_language"].items():
            for view, values in stats["views"].items():
                percentages = [f"{values['classes'][c]['share']:.1%}" if values['classes'][c]['share'] is not None else "n/a" for c in CLASSES]
                delta = f"{values['high_minus_low']:+.1%}" if values['high_minus_low'] is not None else "n/a"
                print(" | ".join([entry["check"], language, view, *percentages, delta,
                                  "KEEP" if stats["selected"] else "DROP", stats["reason"]]))
    print("Saved", output.relative_to(repository))
    if args.audit_regex:
        loose = {
            "deadline": r"\b(?:deadline|today|tomorrow|days?|weeks?|months?|hours?|before|until|within|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|\d{1,2}[/-]\d{1,2}",
            "contact_or_verified_organization": r"\b(?:contact|call|email|phone|organi[sz]ation|charity|foundation|trust|society|association|team|registered|verified|nonprofit|ngo|church|school|hospital)\b|https?://|www\.|@",
            "concrete_people_or_items": r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million)\b",
        }
        high = frame[(frame["language"] == "English") & (frame["quality_label"] == "high")]
        for check, pattern in loose.items():
            print("AUDIT", check)
            shown = 0
            for index, row in high.iterrows():
                text = row["appeal_text"]
                if re.search(pattern, text, re.I) and not matches(text, "English", RULES[check]):
                    excerpt = text[:200]
                    excerpt = re.sub(r"AIza[\w-]+|sk-[A-Za-z0-9_-]{20,}", "[REDACTED]", excerpt)
                    terms = list(dict.fromkeys(re.findall(pattern, text, re.I)))[:5]
                    print(json.dumps({"corpus_row_index": int(index), "source": str(row["source"]), "loose_terms": terms, "excerpt": excerpt}, ensure_ascii=False))
                    shown += 1
                    if shown == 10:
                        break
            print("AUDIT_ROWS_PRINTED", shown)


if __name__ == "__main__":
    main()
