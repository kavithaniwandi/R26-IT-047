"""
app/main.py
-----------
FastAPI application entry point registering all system routers.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db

# Routers
from app.routers import auth as auth_router
from app.routers import admin_stats as admin_router
from app.routers import users as users_router
from app.routers import sos as sos_router
from app.routers import camps as camps_router
from app.routers import heatmap as heatmap_router
from app.routers import donations as donations_router
from app.routers import notifications as notifications_router
from app.routers import victims as victims_router
from app.routers import sms as sms_router

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
        "priority-based smart donation matching, SMS gateway integration, and victim registration with full RBAC."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def health() -> dict:
    return {"status": "ok", "version": settings.APP_VERSION, "env": settings.APP_ENV}
