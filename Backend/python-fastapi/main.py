import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from database import ping_db
from routes.medical_requests  import router as medical_router
# from routes.donations          import router as donations_router    # coming soon
# from routes.ml_recommendations import router as ml_router          # coming soon

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = await ping_db()
    print("✅ MongoDB connected" if db_ok else "❌ MongoDB unreachable")
    yield

app = FastAPI(
    title="Disaster Medical System API",
    description="Offline-first PWA backend for Sri Lanka disaster response",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medical_router, prefix="/api/medical-requests", tags=["Medical Requests"])
# app.include_router(donations_router, prefix="/api/donations",    tags=["Donations"])
# app.include_router(ml_router,        prefix="/api/ml",           tags=["ML Recommendations"])

@app.get("/api/health", tags=["Health"])
async def health():
    db_ok = await ping_db()
    return {
        "status":   "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)