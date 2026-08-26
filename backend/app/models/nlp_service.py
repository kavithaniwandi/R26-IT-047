"""
Clinical NLP extraction service using scispaCy en_core_sci_sm.

Extracts medical entities from clinical notes and maps them to:
- condition_group: one of the specialty buckets used by the ML model
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
MIN_WORD_LENGTH_AVG = 3.5
MIN_REAL_WORD_RATIO = 0.4
MIN_TEXT_LENGTH = 10


@lru_cache(maxsize=1)
def _load_model():
    return spacy.load("en_core_sci_sm")


def _is_valid_clinical_text(text: str) -> bool:
    """
    Lightweight gibberish detector.
    Rejects input that has no plausible natural language structure.
    """
    text = text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        return False

    words = re.findall(r"[a-zA-Z]+", text)
    if not words:
        return False

    avg_len = sum(len(word) for word in words) / len(words)
    if avg_len < MIN_WORD_LENGTH_AVG:
        return False

    vowels = set("aeiouAEIOU")
    real_word_count = sum(
        1
        for word in words
        if any(char in vowels for char in word) and len(word) >= 3
    )
    real_word_ratio = real_word_count / len(words)
    if real_word_ratio < MIN_REAL_WORD_RATIO:
        return False

    return True


def _map_to_specialty(entities: list[str]) -> tuple[str, float]:
    combined = " ".join(entities).lower()
    if not combined.strip():
        return DEFAULT_GROUP, 0.0

    scores: dict[str, int] = {}
    for keywords, group in SPECIALTY_MAP:
        hit = sum(1 for keyword in keywords if keyword in combined)
        if hit:
            scores[group] = scores.get(group, 0) + hit

    if not scores:
        return DEFAULT_GROUP, 0.0

    best_group = max(scores, key=lambda group: scores[group])
    total_hits = sum(scores.values())
    confidence = round(scores[best_group] / total_hits, 4)
    return best_group, confidence


def extract_clinical_entities(clinical_note: str, symptoms: str = "") -> dict:
    combined_text = f"{symptoms} {clinical_note}".strip()

    if not _is_valid_clinical_text(combined_text):
        return {
            "condition_group": DEFAULT_GROUP,
            "specialty": DEFAULT_GROUP,
            "extracted_symptoms": [],
            "confidence": 0.0,
            "valid": False,
        }

    nlp = _load_model()
    doc = nlp(combined_text)

    seen: set[str] = set()
    entities: list[str] = []
    for ent in doc.ents:
        text = ent.text.strip()
        if len(text) < 3 or text.isdigit():
            continue
        lower = text.lower()
        if lower not in seen:
            seen.add(lower)
            entities.append(text)

    condition_group, confidence = _map_to_specialty(entities)

    return {
        "condition_group": condition_group,
        "specialty": condition_group,
        "extracted_symptoms": entities,
        "confidence": confidence,
        "valid": True,
    }
