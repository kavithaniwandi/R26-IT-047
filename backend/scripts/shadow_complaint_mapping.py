from __future__ import annotations

import json
import os
from pathlib import Path

from app.models.config import settings
from app.models.severity_service import classify_note


EXTRAS = [
    {
        "id": "extra_crushing_chest_pain",
        "age": 45,
        "symptoms": "Crushing chest pain spreading to the left arm for 30 minutes, sweating. No fever, no cough.",
        "clinical_note": "Crushing chest pain spreading to the left arm for 30 minutes, sweating. No fever, no cough.",
        "vitals": {
            "vital_hr": 88,
            "vital_spo2": 98,
            "vital_sbp": 128,
            "vital_rr": 18,
            "vital_temp": 36.8,
            "pain_score": 7,
        },
        "red_flags": {},
    },
    {
        "id": "extra_insulin_confused_drowsy",
        "age": 45,
        "symptoms": "Ran out of insulin 3 days ago, now confused and very drowsy",
        "clinical_note": "Ran out of insulin 3 days ago, now confused and very drowsy",
        "vitals": {
            "vital_hr": 88,
            "vital_spo2": 98,
            "vital_sbp": 128,
            "vital_rr": 18,
            "vital_temp": 36.8,
            "pain_score": 1,
        },
        "red_flags": {},
    },
]


CONFIGS = [
    ("legacy", "legacy", False, [], False),
    ("clinical", "clinical", False, [], False),
    ("clinical+approved", "clinical", True, [], False),
    (
        "clinical+approved+conditional+danger",
        "clinical",
        True,
        ["infected_wound", "insulin"],
        True,
    ),
]


def classify_case(case: dict, mode: str, approved: bool, conditional: list[str], danger: bool) -> dict:
    settings.COMPLAINT_COVERAGE_MODE = mode
    settings.COMPLAINT_APPROVED_SYNONYMS_ENABLED = approved
    settings.COMPLAINT_CONDITIONAL_SYNONYMS_ENABLED = conditional
    settings.COMPLAINT_DANGER_TERM_FLOOR_ENABLED = danger
    red_flags = case.get("red_flags") or {}
    result = classify_note(
        clinical_note=case["clinical_note"],
        age=case.get("age"),
        mode="ml",
        symptoms=case.get("symptoms", ""),
        vitals=case.get("vitals"),
        has_red_flag=1 if red_flags else 0,
        red_flag_count=len(red_flags),
        rf_flags=red_flags,
    )
    mapping = result["complaint_mapping"]
    return {
        "mapped_terms": mapping.get("mapped_terms") or [],
        "unmapped_terms": mapping.get("unmapped_terms") or [],
        "coverage": float(mapping.get("coverage") or 0.0),
        "floor_applied": bool(mapping.get("floor_applied")),
        "reason_code": mapping.get("reason_code"),
        "danger_terms": mapping.get("danger_terms") or [],
        "severity": result["severity"],
        "score": float(result["priority_score"]),
    }


def _list_cell(values: list[str]) -> str:
    return ",".join(values) if values else "-"


def main() -> None:
    cases = json.loads(
        Path("backend/tests/fixtures/triage_sample_cases.json").read_text(encoding="utf-8")
    )
    print(
        "id|config|mapped_terms|unmapped_terms|coverage|floor_applied|reason_code|danger_term_hit|severity|score",
        flush=True,
    )
    for case in [*cases, *EXTRAS]:
        for label, mode, approved, conditional, danger in CONFIGS:
            output = classify_case(case, mode, approved, conditional, danger)
            print(
                "|".join(
                    [
                        case["id"],
                        label,
                        _list_cell(output["mapped_terms"]),
                        _list_cell(output["unmapped_terms"]),
                        f"{output['coverage']:.4f}",
                        str(output["floor_applied"]),
                        str(output["reason_code"]),
                        _list_cell(output["danger_terms"]),
                        output["severity"],
                        f"{output['score']:.4f}",
                    ]
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
    os._exit(0)
