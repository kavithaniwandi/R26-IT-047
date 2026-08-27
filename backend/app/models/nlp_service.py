"""
Clinical NLP extraction service using scispaCy en_core_sci_sm.

Extracts medical entities from clinical notes and maps them to:
- condition_group: ML-model-compatible label (e.g. "CARDIOVASCULAR")
- specialty: human-readable specialty label for MO routing
- extracted_symptoms: list of identified medical concepts
- confidence: match strength of specialty assignment
"""

from __future__ import annotations

from functools import lru_cache
import re

import spacy


SPECIALTY_MAP: list[tuple[list[str], str]] = [
    (
        [
            "cardiac",
            "heart",
            "coronary",
            "arrhythmia",
            "myocard",
            "angina",
            "palpitation",
            "tachycardia",
            "bradycardia",
            "atrial",
            "ventricular",
            "chest pain",
            "hypertension",
            "hypotension",
        ],
        "Cardiovascular",
    ),
    (
        [
            "respiratory",
            "lung",
            "pulmonary",
            "bronch",
            "airway",
            "breath",
            "dyspnea",
            "wheez",
            "asthma",
            "pneumon",
            "pleural",
            "spo2",
            "oxygen",
            "hypox",
            "cough",
            "stridor",
            "trachea",
        ],
        "Respiratory",
    ),
    (
        [
            "neuro",
            "brain",
            "seizure",
            "stroke",
            "cerebr",
            "cortex",
            "cranial",
            "headache",
            "migraine",
            "vertigo",
            "syncope",
            "paralysis",
            "weakness",
            "confusion",
            "altered mental",
            "consciousness",
            "deficit",
            "meningit",
            "encephal",
        ],
        "Neurological",
    ),
    (
        [
            "abdomen",
            "abdominal",
            "gastro",
            "intestin",
            "bowel",
            "colon",
            "liver",
            "hepat",
            "pancrea",
            "nausea",
            "vomit",
            "diarrhea",
            "constipation",
            "appendix",
            "stomach",
            "gastric",
            "rectal",
            "bile",
            "gallbladder",
        ],
        "Gastrointestinal",
    ),
    (
        [
            "trauma",
            "fracture",
            "laceration",
            "wound",
            "injury",
            "burn",
            "crush",
            "hemorrhage",
            "bleeding",
            "surgical",
            "operative",
            "post-op",
            "incision",
            "stab",
            "gunshot",
            "blunt",
        ],
        "Trauma & Surgery",
    ),
    (
        [
            "infection",
            "sepsis",
            "fever",
            "bacterial",
            "viral",
            "fungal",
            "malaria",
            "dengue",
            "typhoid",
            "cellulitis",
            "abscess",
            "inflam",
            "systemic",
            "bacteremia",
            "meningit",
        ],
        "Infection & Systemic",
    ),
    (
        [
            "renal",
            "kidney",
            "nephro",
            "urin",
            "bladder",
            "ureter",
            "dysuria",
            "hematuria",
            "creatinine",
            "dialysis",
            "urinary tract",
            "prostate",
            "uti",
        ],
        "Renal & Urinary",
    ),
    (
        [
            "psych",
            "mental",
            "behav",
            "depress",
            "anxiety",
            "panic",
            "hallucin",
            "delusion",
            "schizo",
            "bipolar",
            "suicid",
            "aggress",
            "agitat",
            "psychiatric",
        ],
        "Mental & Behavioral",
    ),
    (
        [
            "pregnan",
            "obstetric",
            "labour",
            "labor",
            "fetal",
            "uterine",
            "placenta",
            "trimester",
            "eclampsia",
            "gynec",
            "menstrual",
            "vaginal",
            "cervical",
            "ovarian",
        ],
        "Obstetric & Gynecologic",
    ),
    (
        [
            "diabet",
            "glucose",
            "insulin",
            "thyroid",
            "endocrine",
            "metabol",
            "ketoacid",
            "hormone",
            "adrenal",
            "hyperglycemia",
            "hypoglycemia",
            "electrolyte",
        ],
        "Endocrine & Metabolic",
    ),
    (
        [
            "allerg",
            "anaphyl",
            "hives",
            "urticaria",
            "eosinophil",
            "immunolog",
            "autoimmune",
            "lupus",
            "rheumat",
            "hypersensitiv",
        ],
        "Allergy & Immunology",
    ),
    (
        [
            "emergency",
            "critical",
            "resuscit",
            "intubat",
            "shock",
            "cardiac arrest",
            "trauma",
        ],
        "Emergency Medicine",
    ),
]

DEFAULT_GROUP = "General Practice"
DEFAULT_ML_GROUP = "OTHER_EMERGENCY"
MIN_WORD_LENGTH_AVG = 3.5
MIN_REAL_WORD_RATIO = 0.4
MIN_TEXT_LENGTH = 10

# Maps human-readable specialty labels to ML model condition_group identifiers.
# The ML model was trained with these uppercase keys (see ml_models/severity_ml/model_config.json).
SPECIALTY_TO_ML_GROUP: dict[str, str] = {
    "Cardiovascular":       "CARDIOVASCULAR",
    "Respiratory":          "RESPIRATORY",
    "Neurological":         "NEUROLOGIC",
    "Gastrointestinal":     "GASTROINTESTINAL",
    "Trauma & Surgery":     "TRAUMA",
    "Infection & Systemic": "INFECTION_SYSTEMIC",
    "Renal & Urinary":      "RENAL_URINARY",
    "Mental & Behavioral":  "OTHER_EMERGENCY",
    "Obstetric & Gynecologic": "OBSTETRIC_GYNECOLOGIC",
    "Endocrine & Metabolic": "ENDOCRINE_METABOLIC",
    "Allergy & Immunology": "OTHER_EMERGENCY",
    "Emergency Medicine":   "OTHER_EMERGENCY",
    "General Practice":     "OTHER_EMERGENCY",
}

# Common clinical abbreviations counted as valid words by the gibberish detector.
# Without this, abbreviation-heavy notes (e.g. "SOB c/o CP") would be rejected.
MEDICAL_ABBREVIATIONS: frozenset[str] = frozenset({
    "sob", "abd", "abdo", "cp", "htn", "dm", "cva", "tia", "gi", "gu", "uti",
    "mi", "pe", "dvt", "chf", "ards", "copd", "gcs", "hr", "bp", "rr",
    "spo2", "bmi", "ecg", "ekg", "cbc", "cmp", "bnp", "lft",
    "prn", "po", "iv", "im", "sc", "npo", "bid", "tid", "qid",
    "dx", "hx", "px", "fx", "rx", "sx", "mx", "cxr", "ct", "mri",
    "afib", "vt", "vf", "svt", "ace", "arb", "ph", "cr", "bun",
    "wbc", "rbc", "plt", "loc", "lac", "ms", "od", "os", "ou",
    "cvp", "map", "ppe", "rbs", "fbs", "hb", "hba1c", "na", "k",
})


@lru_cache(maxsize=1)
def _load_model():
    try:
        return spacy.load("en_core_sci_sm")
    except OSError:
        return None


def _is_valid_clinical_text(text: str) -> bool:
    """
    Lightweight gibberish detector. Accepts both full prose notes and
    abbreviation-heavy clinical shorthand (e.g. "SOB c/o CP, diaphoresis").
    """
    text = text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        return False

    words = re.findall(r"[a-zA-Z]+", text)
    if not words:
        return False

    vowels = set("aeiouAEIOU")
    abbrev_count = sum(1 for w in words if w.lower() in MEDICAL_ABBREVIATIONS)
    real_word_count = sum(
        1
        for w in words
        if w.lower() not in MEDICAL_ABBREVIATIONS
        and any(char in vowels for char in w)
        and len(w) >= 3
    )

    if (abbrev_count + real_word_count) / len(words) < MIN_REAL_WORD_RATIO:
        return False

    # avg-length check only applies when there are no medical abbreviations present,
    # since abbreviations legitimately shorten the average word length.
    if abbrev_count == 0:
        avg_len = sum(len(w) for w in words) / len(words)
        if avg_len < MIN_WORD_LENGTH_AVG:
            return False

    return True


def _map_to_specialty(entities: list[str]) -> tuple[str, str, float]:
    """
    Returns (specialty_label, ml_condition_group, confidence).
    specialty_label is human-readable; ml_condition_group matches model_config.json keys.
    """
    combined = " ".join(entities).lower()
    if not combined.strip():
        return DEFAULT_GROUP, DEFAULT_ML_GROUP, 0.0

    scores: dict[str, int] = {}
    for keywords, group in SPECIALTY_MAP:
        hit = sum(1 for keyword in keywords if keyword in combined)
        if hit:
            scores[group] = scores.get(group, 0) + hit

    if not scores:
        return DEFAULT_GROUP, DEFAULT_ML_GROUP, 0.0

    best_group = max(scores, key=lambda g: scores[g])
    total_hits = sum(scores.values())
    confidence = round(scores[best_group] / total_hits, 4)
    ml_group = SPECIALTY_TO_ML_GROUP.get(best_group, DEFAULT_ML_GROUP)
    return best_group, ml_group, confidence


def extract_clinical_entities(clinical_note: str, symptoms: str = "") -> dict:
    combined_text = f"{symptoms} {clinical_note}".strip()

    if not _is_valid_clinical_text(combined_text):
        return {
            "condition_group": DEFAULT_ML_GROUP,
            "specialty": DEFAULT_GROUP,
            "extracted_symptoms": [],
            "confidence": 0.0,
            "valid": False,
        }

    nlp = _load_model()
    entities: list[str] = []
    seen: set[str] = set()

    if nlp is not None:
        doc = nlp(combined_text)
        for ent in doc.ents:
            text = ent.text.strip()
            if len(text) < 3 or text.isdigit():
                continue
            lower = text.lower()
            if lower not in seen:
                seen.add(lower)
                entities.append(text)
        # Keyword matching runs on the extracted entities
        mapping_source = entities
    else:
        # spaCy model not installed: fall back to simple tokenization.
        # Run keyword matching on the full text so abbreviations don't break routing.
        for token in re.split(r"[\s,;:.()\[\]]+", combined_text):
            token = token.strip()
            if len(token) < 3 or token.isdigit():
                continue
            lower = token.lower()
            if lower not in seen:
                seen.add(lower)
                entities.append(token)
        mapping_source = [combined_text]

    specialty, condition_group, confidence = _map_to_specialty(mapping_source)

    return {
        "condition_group": condition_group,
        "specialty": specialty,
        "extracted_symptoms": entities,
        "confidence": confidence,
        "valid": True,
    }
