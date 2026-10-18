"""
app/main.py
-----------
FastAPI application entry point registering all system routers and local ML endpoints.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

_startup_log = logging.getLogger("app.startup")
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database import init_db
from app.models.quality_service import QualityModelLoadError
from app.routers import admin_stats as admin_router
from app.routers import auth as auth_router
from app.routers import camps as camps_router
from app.routers import divisions as divisions_router
from app.routers import donation_items as donation_items_router
from app.routers import donation_history as donation_history_router
from app.routers import donations as donations_router
from app.routers import heatmap as heatmap_router
from app.routers import notifications as notifications_router
try:
    from app.routers import population as population_router
except ImportError as exc:
    population_router = None
    __import__("logging").getLogger(__name__).warning(
        "population router disabled (missing dependency): %s", exc
    )
from app.routers import relief_camps as relief_camps_router
from app.routers import sms as sms_router
from app.routers import sos as sos_router
from app.routers import triage as triage_router
from app.routers import users as users_router
from app.routers import victims as victims_router
from app.routers import disaster_officer
from app.routers import donors as donors_router
from app.routers import component_users as component_users_router
from app.models.schemas import (
    ExtractRequest,
    ExtractResponse,
    GenerateAppealRequest,
    GenerateAppealResponse,
    GenerateAppealVariantsResponse,
    GenerateNextAppealVariantRequest,
    QualityScoreRequest,
    QualityScoreResponse,
    SeverityClassifyRequest,
    SeverityClassifyResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.models import appeal_guidance_service
    appeal_guidance_service.GAP_CHECKS = appeal_guidance_service.load_gap_statistics()
    # ------------------------------------------------------------------ #
    # Venv / import guard — logs ERROR immediately if the wrong venv is   #
    # active so the missing-module root cause is obvious on startup.       #
    # ------------------------------------------------------------------ #
    _required = {
        "google.genai":    "google-genai  (Gemini generation)",
        "huggingface_hub": "huggingface_hub (HF fallback)",
    }
    for _mod, _desc in _required.items():
        try:
            importlib.import_module(_mod)
        except ImportError as _exc:
            _startup_log.error(
                "MISSING IMPORT '%s' (%s) in Python %s. "
                "Run the server from backend/venv, not .venv-sev. Detail: %s",
                _mod, _desc, sys.executable, _exc,
            )

    init_db()
    expiry_task = None
    try:
        from app.models.quality_service import warm_up

        warm_up()
    except Exception as exc:
        _startup_log.error(
            "Quality model warmup failed: %s. Appeal scoring will return errors until fixed.",
            exc,
        )
    try:
        from app.services.mongo_service import connect_mongo
        from app.services.pledge_expiry import pledge_expiry_worker

        await connect_mongo()
        expiry_task = asyncio.create_task(pledge_expiry_worker())
    except Exception as exc:
        _startup_log.error("MongoDB connection failed: %s", exc)
    try:
        yield
    finally:
        if expiry_task:
            expiry_task.cancel()
            try:
                await expiry_task
            except asyncio.CancelledError:
                pass
        from app.services.mongo_service import close_mongo

        await close_mongo()


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
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https?://(?:localhost|127\.0\.0\.1|(?:\d{1,3}\.){3}\d{1,3}):(?:517[3-9]|5180)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


API_V1_PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=API_V1_PREFIX)
app.include_router(admin_router.router, prefix=API_V1_PREFIX)
app.include_router(users_router.router, prefix=API_V1_PREFIX)
app.include_router(sos_router.router, prefix=API_V1_PREFIX)
app.include_router(camps_router.router, prefix=API_V1_PREFIX)
app.include_router(divisions_router.router, prefix=API_V1_PREFIX)
app.include_router(relief_camps_router.router, prefix=API_V1_PREFIX)
if population_router is not None:
    app.include_router(population_router.router, prefix=API_V1_PREFIX)
app.include_router(heatmap_router.router, prefix=API_V1_PREFIX)
app.include_router(donations_router.router, prefix=API_V1_PREFIX)
app.include_router(donation_items_router.router, prefix=API_V1_PREFIX)
app.include_router(donation_history_router.router, prefix=API_V1_PREFIX)
app.include_router(notifications_router.router, prefix=API_V1_PREFIX)
app.include_router(victims_router.router, prefix=API_V1_PREFIX)
app.include_router(sms_router.router, prefix=API_V1_PREFIX)
app.include_router(triage_router.router, prefix=API_V1_PREFIX)
app.include_router(disaster_officer.router, prefix=API_V1_PREFIX)
app.include_router(donors_router.router, prefix=API_V1_PREFIX)
app.include_router(component_users_router.router, prefix=API_V1_PREFIX)


@app.get("/", tags=["Health"], summary="API landing")
def api_landing() -> dict[str, object]:
    return {
        "message": "Disaster Relief Medical Donation Module API is running.",
        "health": "/health",
        "docs": "/api/docs",
        "api_prefix": API_V1_PREFIX,
        "frontend_ports": [5173, 5174, 5175, 5176, 5177],
    }


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health() -> dict:
    from app.models.gemini_service import gemini_health_check
    gemini = gemini_health_check()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "gemini": {
            "status": gemini["status"],
            "message": gemini["message"],
        },
    }


@app.post("/api/quality/evaluate", response_model=QualityScoreResponse)
async def evaluate_quality(request: QualityScoreRequest) -> QualityScoreResponse:
    """Evaluate donation appeal quality using the trained local ML model."""
    try:
        from app.models.quality_service import get_quality_score

        result = get_quality_score(request.appeal_text, language=request.language)
        from app.models.appeal_guidance_service import guidance
        metadata = await asyncio.to_thread(guidance, request.appeal_text, request.language, result,
                                         request.length_category)
        return QualityScoreResponse(
            **metadata,
            score=result["score"],
            raw_quality_score=result.get("raw_quality_score", result["score"]),
            status=result["status"],
            final_label=result["status"],
            predicted_class=result.get("predicted_class"),
            class_probs=result.get("class_probs", {}),
            method=result["method"],
            confidence=result["confidence"],
            confidence_normalised=result["confidence_normalised"],
            confidence_display=result["confidence_display"],
            low_confidence=result["low_confidence"],
        )
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quality evaluation failed.",
        ) from exc


def _appeal_client(request):
    # Forwarded headers are intentionally ignored: only trust the ASGI peer IP.
    return request.client.host if request is not None and request.client else "local"


def _appeal_response(variants, request, payload=None):
    from app.models.appeal_guidance_service import recommended
    from app.services.appeal_budget import improvement_uses, session
    all_variants = variants
    if payload is not None:
        state = session(payload, _appeal_client(request))
        all_variants = [v for group in state["results"].values() for v in group] or variants
    partial = any(v.get("partial", False) for v in all_variants)
    calls = max((v.get("gemini_calls_used", 0) for v in all_variants), default=0)
    if payload is not None:
        partial = partial or state.get("partial", False)
        calls = state["budget"].calls + state["remaining_budget"].calls
    errors = list(state.get("errors", {}).values()) if payload is not None else []
    retry_at = max(state.get("retry_at", {}).values(), default=0) if payload is not None else 0
    return GenerateAppealVariantsResponse(
        variants=variants, recommended=recommended(all_variants, (payload or {}).get("length_category", "short")),
        remaining_improve_uses=improvement_uses(_appeal_client(request))[1],
        gemini_calls_used=calls, partial=partial,
        generation_error="; ".join(errors) or None,
        retry_after_seconds=max(0, int(retry_at - time.monotonic()) + 1))


@app.post("/api/generate-appeal-variants/improve")
async def improve_generated_appeal(payload: dict, http_request: Request):
    return await improve_appeal(payload, http_request)


@app.post("/api/quality/analyse")
async def analyse_appeal(payload: dict, http_request: Request = None) -> dict:
    """Pure ML quality evaluation plus structured issue diagnosis."""
    appeal_text = (payload.get("appeal_text") or "").strip()
    language = payload.get("language") or "English"

    if not appeal_text:
        raise HTTPException(status_code=422, detail="appeal_text is required.")

    try:
        from app.models.gemini_service import _diagnose_weaknesses
        from app.models.quality_service import get_quality_score

        quality = get_quality_score(appeal_text, language=language)
        from app.models.appeal_guidance_service import guidance
        from app.services.appeal_budget import improvement_uses
        metadata = await asyncio.to_thread(guidance, appeal_text, language, quality, None)
        result = {
            **metadata,
            "original_appeal": payload.get("appeal_text", ""),
            "remaining_improve_uses": improvement_uses(_appeal_client(http_request))[1],
            "score": quality["score"],
            "raw_quality_score": quality.get("raw_quality_score", quality["score"]),
            "label": quality["status"],
            "final_label": quality["status"],
            "predicted_class": quality.get("predicted_class"),
            "class_probs": quality.get("class_probs", {}),
            "confidence": quality["confidence"],
            "low_confidence": quality["low_confidence"],
            "method": quality["method"],
            "issues": [],
        }
        from app.services.mongo_service import log_appeal_analysis

        asyncio.create_task(
            log_appeal_analysis(appeal_text, language, result, source="analyser")
        )
        return result
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal analysis failed.") from exc


_APPEAL_LOG_TASKS: set[asyncio.Task] = set()


def _schedule_appeal_log(log_function, *args, **kwargs) -> None:
    async def guarded_log():
        try:
            await log_function(*args, **kwargs)
        except Exception as exc:
            logger.warning("MongoDB logging failed (non-fatal): %s", type(exc).__name__)

    task = asyncio.create_task(guarded_log())
    _APPEAL_LOG_TASKS.add(task)
    task.add_done_callback(_APPEAL_LOG_TASKS.discard)


@app.post("/api/quality/improve")
async def improve_appeal(payload: dict, http_request: Request = None) -> dict:
    """Generate an improved donation appeal after ML issue diagnosis."""
    appeal_text = payload.get("appeal_text") or ""
    language = payload.get("language") or "English"

    if not appeal_text.strip():
        raise HTTPException(status_code=422, detail="appeal_text is required.")

    try:
        from app.models.appeal_generation_service import repair
        result = await repair(appeal_text, {**payload, "language": language}, _appeal_client(http_request))
        from app.services.mongo_service import log_appeal_analysis

        _schedule_appeal_log(
            log_appeal_analysis, appeal_text,
            language,
            result,
            event_type="improvement",
        )
        return result
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except Exception as exc:
        logger.error("Appeal improve unexpected_error=%s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Appeal improvement failed. Check the backend log for the error type.") from exc


@app.post("/api/generate-appeal", response_model=GenerateAppealResponse)
async def generate_appeal(request: GenerateAppealRequest) -> GenerateAppealResponse:
    """Generate a donation appeal from campaign details."""
    try:
        from app.models.gemini_service import generate_donation_appeal

        campaign_data = request.model_dump()
        appeal_text = await asyncio.to_thread(generate_donation_appeal, campaign_data)
        try:
            from app.services.mongo_service import log_appeal_generation
            _schedule_appeal_log(
                log_appeal_generation, campaign_data,
                [
                    {
                        "appeal_text": appeal_text,
                        "quality_score": None,
                        "quality_label": None,
                        "provider": None,
                        "style": "single",
                    }
                ],
            )
        except Exception as log_exc:
            logger.warning("MongoDB logging failed (non-fatal): %s", type(log_exc).__name__)
        return GenerateAppealResponse(appeal_text=appeal_text)
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal generation failed.") from exc


@app.post("/api/generate-appeal-variants/remaining", response_model=GenerateAppealVariantsResponse)
async def generate_remaining_appeal_variants_endpoint(
    request: GenerateAppealRequest,
    http_request: Request = None,
) -> GenerateAppealVariantsResponse:
    """Generate the remaining donation appeal variants from campaign details."""
    try:
        from app.models.gemini_service import generate_remaining_appeal_variants

        campaign_data = request.model_dump()
        variants = await generate_remaining_appeal_variants(campaign_data, skip_styles=1, client=_appeal_client(http_request))
        if not variants:
            return JSONResponse(status_code=200, content={"variants": [], "partial": True})
        return _appeal_response(variants, http_request, campaign_data)
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Remaining appeal variant generation failed.",
        ) from exc


@app.post("/api/generate-appeal-variants/next", response_model=GenerateAppealVariantsResponse)
async def generate_next_appeal_variant_endpoint(
    request: GenerateNextAppealVariantRequest,
) -> GenerateAppealVariantsResponse:
    from app.models.gemini_service import generate_appeal_variant, AppealVariantGenerationError

    campaign_data = request.model_dump(exclude={"style_index"})
    try:
        variant = await generate_appeal_variant(campaign_data, request.style_index)
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
    except AppealVariantGenerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Appeal variant generation failed.") from exc
    return GenerateAppealVariantsResponse(variants=[variant])


@app.post("/api/generate-appeal-variants", response_model=GenerateAppealVariantsResponse)
async def generate_appeal_variants_endpoint(
    request: GenerateAppealRequest,
    http_request: Request = None,
) -> GenerateAppealVariantsResponse:
    """Generate the first donation appeal variant from campaign details."""
    try:
        from app.models.gemini_service import generate_first_appeal_variant

        campaign_data = request.model_dump()
        variants = await generate_first_appeal_variant(campaign_data, client=_appeal_client(http_request))
        try:
            from app.services.mongo_service import log_appeal_generation
            _schedule_appeal_log(log_appeal_generation, campaign_data, variants)
        except Exception as log_exc:
            logger.warning("MongoDB logging failed (non-fatal): %s", type(log_exc).__name__)
        return _appeal_response(variants, http_request, campaign_data)
    except QualityModelLoadError as exc:
        return JSONResponse(
            status_code=503, content={"status": "failed", "detail": str(exc)}
        )
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
            age=request.age,
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


@app.get("/api/severity/unmapped-terms")
async def severity_unmapped_terms(limit: int = 50) -> dict:
    """Return the most frequent unmapped complaint terms from saved triage patients."""
    try:
        from app.services.mongo_service import get_unmapped_terms

        return {"terms": await get_unmapped_terms(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unmapped terms aggregation failed.") from exc


@app.get("/api/system/credit-status", tags=["System"])
async def credit_status() -> dict:
    """Return recorded provider outcomes; this does not probe live quota."""
    from app.services.credit_monitor import get_status
    return get_status()


@app.post("/api/system/credit-reset", tags=["System"])
async def credit_reset(payload: dict | None = None) -> dict:
    """Reset one provider or all provider credit state."""
    from app.services.credit_monitor import get_status, reset_all, reset_provider
    from app.models.appeal_generation_service import reset_key_cooldowns

    payload = payload or {}
    provider = payload.get("provider")
    if provider:
        reset_provider(provider)
        reset_key_cooldowns(provider)
        return {"reset": provider, "status": get_status()}

    reset_all()
    reset_key_cooldowns()
    return {"reset": "all", "status": get_status()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.models.main:app", host="0.0.0.0", port=8000, reload=True)
