"""
app/routers/triage.py
---------------------
Triage session and patient persistence endpoints.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/triage", tags=["Triage"])


@router.post("/session/start")
async def start_session(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a newly started camp triage session."""
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required.")

    try:
        from app.services.mongo_service import save_triage_session

        doc_id = await save_triage_session(payload)
        return {
            "status": "saved",
            "doc_id": doc_id,
            "session_id": session_id,
        }
    except Exception as exc:
        print(f"[triage] session start persist failed: {exc}")
        return {"status": "warning", "detail": str(exc), "session_id": session_id}


@router.post("/patient/save")
async def save_patient(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist one classified and routed patient record."""
    patient_id = payload.get("id")
    session_id = payload.get("session_id")
    if not patient_id:
        raise HTTPException(status_code=422, detail="id is required.")
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required.")

    try:
        from app.services.mongo_service import save_triage_patient

        doc_id = await save_triage_patient(payload)
        return {
            "status": "saved",
            "doc_id": doc_id,
            "patient_id": patient_id,
        }
    except Exception as exc:
        print(f"[triage] patient save failed: {exc}")
        return {"status": "warning", "detail": str(exc), "patient_id": patient_id}


@router.post("/session/end")
async def end_session(payload: dict[str, Any]) -> dict[str, Any]:
    """Archive a completed triage session and mark the active session ended."""
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required.")

    try:
        from app.services.mongo_service import archive_triage_session

        doc_id = await archive_triage_session(
            session_id=session_id,
            session_data=payload.get("session", {}),
            patients=payload.get("patients", []),
            summary=payload.get("summary", {}),
        )
        return {
            "status": "archived",
            "doc_id": doc_id,
            "session_id": session_id,
        }
    except Exception as exc:
        print(f"[triage] session end failed: {exc}")
        return {"status": "warning", "detail": str(exc), "session_id": session_id}


@router.get("/archives")
async def list_archives(limit: int = 50, skip: int = 0) -> dict[str, Any]:
    """Return archived session summaries without the full patient lists."""
    try:
        from app.services.mongo_service import _db

        if _db is None:
            return {"archives": [], "total": 0}

        cursor = (
            _db.triage_archives
            .find(
                {},
                {
                    "_id": 1,
                    "session_id": 1,
                    "camp": 1,
                    "mos": 1,
                    "started_at": 1,
                    "ended_at": 1,
                    "summary": 1,
                },
            )
            .sort("ended_at", -1)
            .skip(skip)
            .limit(limit)
        )
        archives = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            archives.append(doc)

        total = await _db.triage_archives.count_documents({})
        return {"archives": archives, "total": total}
    except Exception as exc:
        print(f"[triage] list_archives failed: {exc}")
        return {"archives": [], "total": 0}


@router.get("/archives/{session_id}")
async def get_archive(session_id: str) -> dict[str, Any]:
    """Return one full archived session, including patient records."""
    try:
        from app.services.mongo_service import _db

        if _db is None:
            raise HTTPException(status_code=503, detail="Database unavailable.")

        doc = await _db.triage_archives.find_one({"session_id": session_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found.")

        doc["_id"] = str(doc["_id"])
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
