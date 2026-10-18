from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import itertools

import pytest

from app.models import severity_ml_service, severity_service, specialty_service
from app.models.severity_service import classify_note


RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
ZERO_IS_MISSING = {"vital_spo2", "vital_hr", "vital_sbp"}
ML_KEYS = {"vital_hr", "vital_spo2", "vital_sbp", "vital_rr", "vital_temp", "pain_score"}


@dataclass
class OldVitalsSnapshot:
    values: dict[str, float]
    warnings: list[dict]

    def get(self, key: str):
        return self.values.get(key)

    def count_for_ml(self) -> int:
        count = 0
        for key in ML_KEYS:
            value = self.values.get(key)
            if value is None:
                continue
            if key in ZERO_IS_MISSING and value <= 0:
                continue
            count += 1
        return count


def _float_or_none(value):
    if value in (None, ""):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def old_normalize_for_scoring(vitals):
    values = {}
    for key, value in (vitals or {}).items():
        numeric = _float_or_none(value)
        if numeric is not None:
            if key in ZERO_IS_MISSING and numeric <= 0 and key != "vital_spo2":
                continue
            values[key] = numeric
    return OldVitalsSnapshot(values=values, warnings=[])


def old_specialty_numeric(vitals, key):
    numeric = _float_or_none((vitals or {}).get(key))
    if numeric is None:
        return None
    if key in ZERO_IS_MISSING and numeric <= 0:
        return None
    return numeric


@contextmanager
def old_vitals_logic(monkeypatch):
    with monkeypatch.context() as scoped:
        scoped.setattr(severity_service, "normalize_vitals_for_scoring", old_normalize_for_scoring)
        scoped.setattr(severity_ml_service, "normalize_vitals_for_scoring", old_normalize_for_scoring)
        scoped.setattr(specialty_service, "normalized_vital_value", old_specialty_numeric)
        yield


BASE_VITALS = {
    "vital_hr": 78,
    "vital_spo2": 99,
    "vital_sbp": 122,
    "vital_rr": 16,
    "vital_temp": 36.7,
    "pain_score": 2,
}

VALUE_GRID = {
    "vital_spo2": ["", 0, 0.5, 0.99, 1, 9.9, 49, 50, 91, 92, 99, 100, 150],
    "vital_hr": ["", 0, 19, 20, 120, 121, 250, 300],
    "vital_sbp": ["", 0, 40, 50, 89, 90, 300, 350],
    "vital_rr": ["", 0, 3, 4, 10, 24, 25, 80, 100],
    "vital_temp": ["", 0, 29, 30, 35, 38.5, 43, 50, 98.6],
}

COMPLAINTS = [
    ("minor cut", "Small cut on the hand, mild pain", "Superficial laceration, bleeding controlled and vitals stable."),
    ("headache", "Headache", "Headache reported, alert and walking."),
    ("refill", "Medication refill", "Needs diabetes medication refill, no acute distress."),
]


def _cases():
    for label, symptoms, note in COMPLAINTS:
        for field, values in VALUE_GRID.items():
            for value in values:
                vitals = dict(BASE_VITALS, **{field: value})
                yield f"{label}:{field}={value!r}", symptoms, note, vitals
        for other_field in ("vital_hr", "vital_sbp", "vital_rr", "vital_temp"):
            for spo2, other_value in itertools.product(VALUE_GRID["vital_spo2"], VALUE_GRID[other_field]):
                vitals = dict(BASE_VITALS, vital_spo2=spo2, **{other_field: other_value})
                yield f"{label}:spo2={spo2!r}:{other_field}={other_value!r}", symptoms, note, vitals


def _classify(symptoms, note, vitals):
    return classify_note(
        clinical_note=note,
        symptoms=symptoms,
        age=29,
        mode="ml",
        vitals=vitals,
    )


def _allowed_lowering_exception(vitals):
    spo2 = vitals.get("vital_spo2")
    try:
        numeric = float(spo2)
    except (TypeError, ValueError):
        return False
    return (0 < numeric <= 1) or numeric == 0


def test_new_vitals_logic_never_lowers_severity_except_documented_cases(monkeypatch):
    differences = []
    lowered = []
    for case_id, symptoms, note, vitals in _cases():
        with old_vitals_logic(monkeypatch):
            old = _classify(symptoms, note, vitals)
        new = _classify(symptoms, note, vitals)

        if old["severity"] != new["severity"]:
            differences.append(
                f"{case_id}: old={old['severity']}({old['priority_score']}) "
                f"new={new['severity']}({new['priority_score']}) warnings={new.get('vitals_warnings', [])}"
            )
        if RANK[new["severity"]] < RANK[old["severity"]] and not _allowed_lowering_exception(vitals):
            lowered.append(differences[-1] if differences else case_id)

    print("\nVITALS_NEVER_LOWER_DIFFERENCES")
    for line in differences:
        print(line)
    assert lowered == []
