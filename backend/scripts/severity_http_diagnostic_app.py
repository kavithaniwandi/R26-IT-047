from __future__ import annotations

from fastapi import FastAPI

from app.models.schemas import SeverityClassifyRequest
from app.models.severity_service import classify_note


app = FastAPI()


@app.post("/api/severity/classify")
async def classify_severity(request: SeverityClassifyRequest) -> dict:
    result = classify_note(
        clinical_note=request.clinical_note,
        age=request.age,
        mode=request.mode,
        source=request.source,
        condition_group=request.condition_group,
        vitals=request.vitals,
        has_red_flag=request.has_red_flag,
        red_flag_count=request.red_flag_count,
        rf_flags=request.rf_flags,
        symptoms=request.symptoms,
    )
    return {
        "parsed_request_vitals": request.vitals,
        **result,
    }
