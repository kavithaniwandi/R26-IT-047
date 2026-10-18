"""Shared local scoring, confidence metadata and optional evidence-based guidance."""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack

from app.models.config import settings
from app.models import quality_service as quality

logger = logging.getLogger(__name__)
GAP_PATH = Path(__file__).parent / "data/appeal_gap_statistics.json"
LEVELS = ["low", "borderline", "moderate", "high"]
RANK = {"low": 0, "medium": 1, "high": 2}


def load_gap_statistics():
    if not GAP_PATH.exists():
        return []
    try:
        data = json.loads(GAP_PATH.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError("Unsupported gap statistics schema")
        manifest = json.loads(settings.donation_appeal_model_path("manifest.json").read_text(encoding="utf-8"))
        provenance = data["provenance"]
        if provenance["dataset_sha256"] != manifest["data_sha256"] or provenance["development_rows"] != manifest["development_rows"]:
            raise ValueError("Gap evidence does not match the selected model's development corpus")
        checks = data["checks"]
        if not isinstance(checks, list):
            raise ValueError("Invalid checks")
        for check in checks:
            if not isinstance(check["check"], str) or not isinstance(check["rule"], dict):
                raise ValueError("Invalid rule")
            rule = check["rule"]
            patterns = [rule.get("common_pattern"), *rule.get("patterns", {}).values()]
            patterns.extend(p for values in rule.get("all_patterns", {}).values() for p in values)
            for pattern in patterns:
                if pattern:
                    re.compile(pattern)
            for language in check["enabled_languages"]:
                stat = check["per_language"][language]
                if not stat["selected"] or stat["high_minus_low"] < 0.15:
                    raise ValueError("Unselected gap rule")
                if language == "English" and not all(stat["views"][view]["selected"] for view in ("all_development", "human_written")):
                    raise ValueError("English evidence must pass both robustness views")
        return checks
    except (ValueError, KeyError, OSError, TypeError, re.error):
        logger.warning("Gap statistics unavailable or invalid; using length guidance")
        return []


GAP_CHECKS = load_gap_statistics()


# Shared with the Generator dropdown; ship this component config with the backend.
LENGTH_CONFIG = json.loads((Path(__file__).resolve().parents[3] /
    "frontend/src/config/appealLengths.json").read_text(encoding="utf-8"))


def length_config(category="short"):
    name = str(category).lower().strip().replace(" ", "_")
    return next((value for key, value in LENGTH_CONFIG.items() if name.startswith(key)), LENGTH_CONFIG["short"])


def length_band(category="short"):
    band = length_config(category)
    return band["minimum"], band["maximum"]


def length_prompt(category="short"):
    band = length_config(category)
    return (f"Target {band['target_minimum']}-{band['target_maximum']} words. "
            f"Write at least {band['minimum']} words; maximum {band['maximum']}. "
            "Count whitespace-delimited words before responding.")


def confidence_metadata(result):
    probabilities = result.get("class_probs", result.get("probabilities", {})) or {}
    top = sorted(({"class": k, "probability": float(v)} for k, v in probabilities.items()),
                 key=lambda item: (-item["probability"], item["class"]))
    classifier = top[0]["class"] if top else result.get("predicted_class")
    confidence = top[0]["probability"] if top else float(result.get("confidence", 0))
    final = result.get("final_label", result.get("quality_label", result.get("label", result.get("status"))))
    agreement = classifier is not None and final == classifier
    level = (3 if confidence >= settings.CONFIDENCE_HIGH else
             2 if confidence >= settings.CONFIDENCE_MODERATE else
             1 if confidence >= settings.CONFIDENCE_BORDERLINE else 0)
    if not agreement:
        level = max(0, level - 1)
    return {"classifier_top_class": classifier, "classifier_confidence": confidence,
            "label_agreement": agreement, "confidence_level": LEVELS[level], "top_classes": top[:2],
            "agreement_note": "Rating and classifier disagree" if classifier is not None and not agreement else None}


def batch_score(texts, language="English"):
    """One classifier/regressor batch; same artifacts and formulas as quality_service."""
    if not texts:
        return []
    a = quality._load_artifacts()
    language = quality._normalise_language(language)
    texts = [quality._validate_input(text) for text in texts]
    n = len(texts)
    hand = a["scaler"].transform(np.vstack([quality._handcrafted(t, language, a) for t in texts]))
    tf, lsa = [], []
    for key, name in (("en", "English"), ("si", "Sinhala"), ("ta", "Tamil")):
        if language == name:
            features = a["tfidf_" + key].transform(texts)
            tf.append(features)
            lsa.append(a["svd_" + key].transform(features))
        else:
            tf.append(csr_matrix((n, a["N_" + key.upper()])))
            lsa.append(np.zeros((n, a["cfg"]["lsa_components"][key])))
    proba = a["clf"].predict_proba(hstack([csr_matrix(hand), *tf]))
    raw = np.clip(a["reg"].predict(np.hstack([proba, hand, *lsa])), 1, 5)
    scores = np.clip(a["iso"].predict(raw), 1, 5)
    results = []
    for score, probabilities in zip(scores, proba):
        label = str(quality._resolve_label(score, probabilities, a))
        conf = round(float(probabilities.max()), 3)
        result = {"quality_label": label, "final_label": label,
                  "quality_score": round(float(score), 2),
                  "raw_quality_score": round(float(score), 2), "confidence": conf,
                  "confidence_normalised": conf, "confidence_display": f"{round(conf * 100)}%",
                  "predicted_class": str(a["le"].classes_[int(np.argmax(probabilities))]),
                  "class_probs": {str(c): round(float(p), 3) for c, p in zip(a["le"].classes_, probabilities)}}
        result.update(confidence_metadata(result))
        results.append(result)
    return results


def length_warning(text, category):
    minimum, maximum = length_band(category)
    words = len(text.split())
    return (f"Generated {words} words; requested band is {minimum}–{maximum} words."
            if words < minimum or words > maximum else None)


def _rule_matches(text, language, rule):
    flags = re.I | re.S
    if "word_count" in rule:
        return rule["word_count"]["min"] <= len(text.split()) and (rule["word_count"]["max"] is None or len(text.split()) <= rule["word_count"]["max"])
    if "all_patterns" in rule:
        return all(re.search(p, text, flags) for p in rule["all_patterns"].get(language, []))
    return any(re.search(p, text, flags) for p in
               [rule.get("common_pattern"), rule.get("patterns", {}).get(language)] if p)


SUGGESTION_MESSAGES = {
    "fund_use": "Say how the donation will be used.",
    "human_detail": "Mention who is affected.",
    "specific_call_to_action": "End with a specific action.",
    "amount_mentioned": "Mention an amount.",
}


def dataset_evidence(check, language="English"):
    stats = check["per_language"][language]
    values = stats.get("views", {}).get("all_development", stats)
    shares = values["classes"]
    return (f"Appears in {shares['high']['share']:.1%} of high-rated "
            f"and {shares['low']['share']:.1%} of low-rated English appeals.")


def guidance(text, language, result, category="short"):
    """Direct text checks only; suggestions never run model inference."""
    started = time.monotonic()
    language = quality._normalise_language(language)
    metadata = confidence_metadata(result)
    final_label = result.get("final_label", result.get("quality_label", result.get("status", result.get("label"))))
    eligible = final_label != "high" or metadata["confidence_level"] == "low" or bool(metadata["agreement_note"])
    minimum = 60 if category is None else length_band(category)[0]
    word_count = len(text.split())
    available = sorted((check for check in GAP_CHECKS
                        if language == "English" and check["check"] in SUGGESTION_MESSAGES
                        and "English" in check.get("enabled_languages", [])),
                       key=lambda check: check["per_language"]["English"]["high_minus_low"], reverse=True)
    suggestions = []
    if eligible:
        if word_count < minimum:
            suggestions.append({"check": "length", "message":
                                (f"This appeal has {word_count} words. High-rated appeals in the data are usually about 60 or more."
                                 if category is None else f"This appeal has {word_count} words. Appeals under about {minimum} words tend to rate lower."),
                                "evidence": ""})
        gaps = [check for check in available if not _rule_matches(text, language, check["rule"])][:2]
        suggestions.extend({"check": check["check"], "message": SUGGESTION_MESSAGES[check["check"]],
                            "evidence": dataset_evidence(check)} for check in gaps)
    elapsed = round((time.monotonic() - started) * 1000, 1)
    logger.info("Appeal stage=suggestions elapsed_ms=%.1f checks=%d", elapsed, len(suggestions))
    return {**metadata, "suggestions": suggestions[:3], "gap_statistics_available": bool(available),
            "suggestions_ms": elapsed, "word_count": word_count, "length_warning": length_warning(text, category) if category is not None else None,
            "dataset_gap_status": "not surfaced: likely augmentation artifact" if language != "English" else "available" if available else "unavailable"}


def guidance_many(texts, language, scores, category="short"):
    return [guidance(text, language, score, category) for text, score in zip(texts, scores)]


def ordered_variants(variants, category="short"):
    """Selected word band, agreement, label, classifier confidence, then score."""
    def key(variant):
        metadata = confidence_metadata(variant)
        minimum, maximum = length_band(category)
        words = variant.get("word_count", len(variant.get("appeal_text", "").split()))
        return (minimum <= words <= maximum, variant.get("label_agreement", metadata["label_agreement"]) is True,
                RANK.get(variant["final_label"], -1),
                float(variant.get("classifier_confidence", metadata["classifier_confidence"])),
                float(variant["quality_score"]))
    return sorted(variants, key=key, reverse=True)


def recommended(variants, category="short"):
    return next(iter(ordered_variants(variants, category)), None)
