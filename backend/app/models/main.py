"""
app/main.py
-----------
FastAPI application entry point registering all system routers and local ML endpoints.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db
from app.routers import admin_stats as admin_router
from app.routers import auth as auth_router
from app.routers import camps as camps_router
from app.routers import donations as donations_router
from app.routers import heatmap as heatmap_router
from app.routers import notifications as notifications_router
from app.routers import sms as sms_router
from app.routers import sos as sos_router
from app.routers import users as users_router
from app.routers import victims as victims_router
from app.models.schemas import (
    ExtractRequest,
    ExtractResponse,
    GenerateAppealRequest,
    GenerateAppealResponse,
    GenerateAppealVariantsResponse,
    QualityScoreRequest,
    QualityScoreResponse,
    SeverityClassifyRequest,
    SeverityClassifyResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "Backend API for Disaster Relief Medical Donation Module (R26-IT-047). "
        "Covers SOS alerting, risk heatmap optimization, medical camp planning, "
        "priority-based smart donation matching, SMS gateway integration, "
        "victim registration, donation appeal quality scoring, and severity triage."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_V1_PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=API_V1_PREFIX)
app.include_router(admin_router.router, prefix=API_V1_PREFIX)
app.include_router(users_router.router, prefix=API_V1_PREFIX)
app.include_router(sos_router.router, prefix=API_V1_PREFIX)
app.include_router(camps_router.router, prefix=API_V1_PREFIX)
app.include_router(heatmap_router.router, prefix=API_V1_PREFIX)
app.include_router(donations_router.router, prefix=API_V1_PREFIX)
app.include_router(notifications_router.router, prefix=API_V1_PREFIX)
app.include_router(victims_router.router, prefix=API_V1_PREFIX)
app.include_router(sms_router.router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.post("/api/quality/evaluate", response_model=QualityScoreResponse)
async def evaluate_quality(request: QualityScoreRequest) -> QualityScoreResponse:
    """Evaluate donation appeal quality using the trained local ML model."""
    try:
        from app.models.quality_service import get_quality_score

        result = get_quality_score(request.appeal_text, language=request.language)
        return QualityScoreResponse(
            score=result["score"],
            status=result["status"],
            method=result["method"],
            confidence=result["confidence"],
            confidence_normalised=result["confidence_normalised"],
            confidence_display=result["confidence_display"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quality evaluation failed.",
        ) from exc


@app.post("/api/quality/analyse")
async def analyse_appeal(payload: dict) -> dict:
    """Pure ML quality evaluation plus structured issue diagnosis."""
    appeal_text = (payload.get("appeal_text") or "").strip()
    language = payload.get("language") or "English"

    if not appeal_text:
        raise HTTPException(status_code=422, detail="appeal_text is required.")

    try:
        from app.models.gemini_service import _diagnose_weaknesses
        from app.models.quality_service import get_quality_score

        quality = get_quality_score(appeal_text, language=language)
        return {
            "score": quality["score"],
            "label": quality["status"],
            "confidence": quality["confidence"],
            "method": quality["method"],
            "issues": _diagnose_weaknesses(appeal_text, language),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal analysis failed.") from exc


@app.post("/api/quality/improve")
async def improve_appeal(payload: dict) -> dict:
    """Generate an improved donation appeal after ML issue diagnosis."""
    appeal_text = (payload.get("appeal_text") or "").strip()
    language = payload.get("language") or "English"

    if not appeal_text:
        raise HTTPException(status_code=422, detail="appeal_text is required.")

    try:
        from app.models.gemini_service import improve_appeal_text

        return await improve_appeal_text(appeal_text, language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal improvement failed.") from exc


@app.post("/api/generate-appeal", response_model=GenerateAppealResponse)
async def generate_appeal(request: GenerateAppealRequest) -> GenerateAppealResponse:
    """Generate a donation appeal from campaign details."""
    try:
        from app.models.gemini_service import generate_donation_appeal

        appeal_text = generate_donation_appeal(request.model_dump())
        return GenerateAppealResponse(appeal_text=appeal_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal generation failed.") from exc


@app.post("/api/generate-appeal-variants", response_model=GenerateAppealVariantsResponse)
async def generate_appeal_variants_endpoint(
    request: GenerateAppealRequest,
) -> GenerateAppealVariantsResponse:
    """Generate multiple donation appeal variants from campaign details."""
    try:
        from app.models.gemini_service import generate_appeal_variants

        variants = await generate_appeal_variants(request.model_dump(), top_n=3)
        return GenerateAppealVariantsResponse(variants=variants)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal variant generation failed.") from exc


@app.post("/api/log-copy")
async def log_copy(payload: dict) -> dict[str, str]:
    from app.models.feedback_logger import log_copy_event

    log_copy_event(
        appeal_text=payload.get("appeal_text", ""),
        language=payload.get("language", "English"),
        quality_score=payload.get("quality_score", 0.0),
        quality_label=payload.get("quality_label", ""),
        confidence=payload.get("confidence", 0.0),
        confidence_normalised=payload.get("confidence_normalised"),
        confidence_display=payload.get("confidence_display"),
        style=payload.get("style"),
    )
    return {"status": "logged"}


@app.post("/api/log-edit")
async def log_edit(payload: dict) -> dict[str, str]:
    from app.models.feedback_logger import log_edit_event

    log_edit_event(
        original_text=payload.get("original_text", ""),
        edited_text=payload.get("edited_text", ""),
        language=payload.get("language", "English"),
        quality_score=payload.get("quality_score", 0.0),
        quality_label=payload.get("quality_label", ""),
        confidence=payload.get("confidence", 0.0),
        confidence_normalised=payload.get("confidence_normalised"),
        confidence_display=payload.get("confidence_display"),
        style=payload.get("style"),
    )
    return {"status": "logged"}


@app.post("/api/severity/extract", response_model=ExtractResponse)
async def extract_severity_entities(request: ExtractRequest) -> ExtractResponse:
    """
    Extract medical entities from a clinical note.
    Returns condition_group and specialty for ML classification and MO routing.
    """
    try:
        from app.models.nlp_service import extract_clinical_entities

        return extract_clinical_entities(
            clinical_note=request.clinical_note,
            symptoms=request.symptoms,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Clinical NLP extraction failed.") from exc


@app.post("/api/severity/classify", response_model=SeverityClassifyResponse)
async def classify_severity(request: SeverityClassifyRequest) -> SeverityClassifyResponse:
    """
    Classify clinical note severity.
    Modes: rule_based (keyword/rule engine) | ml (stacking ensemble).
    """
    try:
        from app.models.severity_service import classify_note

        return classify_note(
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Severity classification failed.") from exc


@app.get("/api/system/credit-status", tags=["System"])
async def credit_status() -> dict:
    """Return real-time in-memory status of all LLM API providers."""
    from app.services.credit_monitor import get_status
    return get_status()


@app.post("/api/system/credit-reset", tags=["System"])
async def credit_reset(payload: dict | None = None) -> dict:
    """Reset one provider or all provider credit state."""
    from app.services.credit_monitor import get_status, reset_all, reset_provider

    payload = payload or {}
    provider = payload.get("provider")
    if provider:
        reset_provider(provider)
        return {"reset": provider, "status": get_status()}

    reset_all()
    return {"reset": "all", "status": get_status()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.models.main:app", host="0.0.0.0", port=8000, reload=True)
