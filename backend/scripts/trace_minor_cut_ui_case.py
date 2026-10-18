from __future__ import annotations

import json
import os

from app.models import severity_pipeline as sp
from app.models.schemas import SeverityClassifyRequest
from app.models.severity_ml_service import _clean_vitals, diagnose_complaint_mapping
from app.models.severity_service import classify_note
from app.models.specialty_service import _numeric_vital, suggest_specialty


FORM = {
    "age": "29",
    "symptoms": "Small cut on the hand, mild pain",
    "clinicalNote": (
        "Superficial 2 cm laceration from broken glass, bleeding controlled. "
        "Wound cleaned and dressed. Vitals stable."
    ),
    "vital_hr": "78",
    "vital_spo2": "99",
    "vital_sbp": "122",
    "vital_rr": "16",
    "vital_temp": "36.7",
    "pain_score": "2",
}
VITAL_FIELDS = [
    "vital_hr",
    "vital_spo2",
    "vital_sbp",
    "vital_rr",
    "vital_temp",
    "pain_score",
]


def main() -> None:
    frontend_vitals = {
        key: float(FORM[key])
        for key in VITAL_FIELDS
        if FORM[key] != ""
    }
    body = {
        "clinical_note": FORM["clinicalNote"],
        "age": int(FORM["age"]),
        "mode": "ml",
        "source": "TRIAGE",
        "condition_group": "Unknown",
        "has_red_flag": 0,
        "red_flag_count": 0,
        "rf_flags": {},
        "symptoms": FORM["symptoms"],
        "vitals": frontend_vitals,
    }
    parsed = SeverityClassifyRequest.model_validate(body)
    clean_vitals = _clean_vitals(parsed.vitals)
    mapping = diagnose_complaint_mapping(parsed.symptoms, parsed.clinical_note)
    row = sp.row_from_request(mapping["model_symptoms"], parsed.age, {}, clean_vitals)
    result = classify_note(
        parsed.clinical_note,
        parsed.age,
        parsed.mode,
        parsed.source,
        parsed.condition_group,
        parsed.vitals,
        parsed.has_red_flag,
        parsed.red_flag_count,
        parsed.rf_flags,
        parsed.symptoms,
    )
    specialty_probe = suggest_specialty(
        parsed.symptoms,
        parsed.clinical_note,
        parsed.rf_flags,
        parsed.age,
        result["severity"],
        result.get("mapped_complaints", []),
        parsed.vitals,
    )
    print(
        json.dumps(
            {
                "a_frontend_buildVitalsPayload": frontend_vitals,
                "b_json_body_vitals": body["vitals"],
                "c_pydantic_request_vitals": parsed.vitals,
                "d_ml_clean_vitals": clean_vitals,
                "d_ml_row_vitals": {
                    key: float(row.loc[0, key])
                    for key in sp.VITAL_COLS
                },
                "d_ml_row_vital_flags": {
                    "vf_hypox_severe": float(row.loc[0, "vital_spo2"]) < 90,
                    "vf_hypox_moderate": float(row.loc[0, "vital_spo2"]) < 94,
                    "vf_hypotension": float(row.loc[0, "vital_sbp"]) < 90,
                    "vf_tachypnea_severe": float(row.loc[0, "vital_rr"]) > 24,
                    "vf_pain_severe": float(row.loc[0, "pain_score"]) >= 8,
                },
                "d_suggest_specialty_numeric_spo2": _numeric_vital(parsed.vitals, "vital_spo2"),
                "d_suggest_specialty": specialty_probe,
                "final": {
                    "severity": result["severity"],
                    "score": result["priority_score"],
                    "matched_keywords": result["suggested_specialty"]["matched_keywords"],
                },
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    os._exit(0)


if __name__ == "__main__":
    main()
