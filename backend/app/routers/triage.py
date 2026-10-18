"""
app/routers/triage.py
---------------------
Triage session and patient persistence endpoints.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.severity_service import COMPLAINT_MAPPING_REVIEW_REASON
from app.services.mongo_service import TriageSessionStateError

router = APIRouter(prefix="/triage", tags=["Triage"])


def _require_id(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise HTTPException(status_code=422, detail=f"{name} must be a non-empty string (maximum 200 characters).")
    return value


def _normalise_patient_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Return patient documents with stable UI-friendly field names."""
    doc["_id"] = str(doc["_id"])
    doc["id"] = doc.get("patient_id") or doc["_id"]
    doc["submittedAt"] = doc.get("submitted_at")

    symptoms = doc.get("symptoms") or doc.get("original_symptoms_text") or doc.get("model_symptoms")
    if not doc.get("complaint_text") and symptoms:
        doc["complaint_text"] = symptoms
    if not doc.get("original_symptoms_text") and symptoms:
        doc["original_symptoms_text"] = symptoms

    normalised_rules = []
    for rule in doc.get("matched_rules") or []:
        text = str(rule).replace("â", "-").replace("—", "-")
        normalised_rules.append(text)
    doc["matched_rules"] = normalised_rules

    if not doc.get("mapping_review_reason") and any(
        "complaint not recognised" in rule for rule in normalised_rules
    ):
        doc["mapping_review_reason"] = COMPLAINT_MAPPING_REVIEW_REASON

    return doc


@router.post("/session/start")
async def start_session(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a newly started camp triage session."""
    session_id = _require_id(payload, "session_id")

    try:
        from app.services.mongo_service import save_triage_session

        doc_id = await save_triage_session(payload)
        if doc_id is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "failed",
                    "detail": "Triage session could not be persisted.",
                    "session_id": session_id,
                },
            )
        return {
            "status": "saved",
            "doc_id": doc_id,
            "session_id": session_id,
        }
    except TriageSessionStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[triage] session start persist failed: {exc}")
        raise HTTPException(status_code=503, detail="Session save failed. Please retry.") from exc


@router.post("/patient/save")
async def save_patient(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist one classified and routed patient record."""
    patient_id = _require_id(payload, "id")
    session_id = _require_id(payload, "session_id")
    if payload.get("severity") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise HTTPException(status_code=422, detail="A valid severity classification is required.")
    if "should_queue" in payload and not isinstance(payload["should_queue"], bool):
        raise HTTPException(status_code=422, detail="should_queue must be a boolean.")
    if "vitals" in payload and not isinstance(payload["vitals"], dict):
        raise HTTPException(status_code=422, detail="vitals must be an object.")

    try:
        from app.services.mongo_service import save_triage_patient

        doc_id = await save_triage_patient(payload)
        if not doc_id:
            raise RuntimeError("No acknowledged patient document.")
        return {
            "status": "saved",
            "doc_id": doc_id,
            "patient_id": patient_id,
        }
    except TriageSessionStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[triage] patient save failed: {exc}")
        raise HTTPException(status_code=503, detail="Patient save failed. Your submission is not confirmed. Please retry.") from exc


@router.post("/session/end")
async def end_session(payload: dict[str, Any]) -> dict[str, Any]:
    """Archive a completed triage session and mark the active session ended."""
    session_id = _require_id(payload, "session_id")

    try:
        from app.services.mongo_service import archive_triage_session

        doc_id = await archive_triage_session(
            session_id=session_id,
            session_data=payload.get("session", {}),
            patients=payload.get("patients", []),
            summary=payload.get("summary", {}),
        )
        if not doc_id:
            raise RuntimeError("No acknowledged archive document.")
        return {
            "status": "archived",
            "doc_id": doc_id,
            "session_id": session_id,
        }
    except Exception as exc:
        print(f"[triage] session end failed: {exc}")
        raise HTTPException(status_code=503, detail="Session archive failed. Keep the session active and retry.") from exc


@router.get("/archives")
async def list_archives(limit: int = 50, skip: int = 0) -> dict[str, Any]:
    """Return archived session summaries without the full patient lists."""
    try:
        from app.services.mongo_service import get_mongo_collection
        collection = get_mongo_collection("triage_archives")

        cursor = (
            collection
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

        total = await collection.count_documents({})
        return {"archives": archives, "total": total}
    except Exception as exc:
        print(f"[triage] list_archives failed: {exc}")
        raise HTTPException(status_code=503, detail="Unable to load session archives. Please retry.") from exc


@router.get("/patients")
async def list_patients(
    limit: int = 200,
    skip: int = 0,
    session_id: str | None = None,
    camp_id: str | None = None,
) -> dict[str, Any]:
    """Return persisted triage patient records from MongoDB."""
    try:
        from app.services.mongo_service import get_mongo_collection
        collection = get_mongo_collection("triage_patients")

        query: dict[str, Any] = {}
        if session_id:
            query["session_id"] = session_id
        if camp_id:
            query["camp.id"] = camp_id

        cursor = (
            collection
            .find(query)
            .sort("submitted_at", -1)
            .skip(skip)
            .limit(min(max(limit, 1), 500))
        )
        patients = []
        async for doc in cursor:
            patients.append(_normalise_patient_doc(doc))

        total = await collection.count_documents(query)
        return {"patients": patients, "total": total}
    except Exception as exc:
        print(f"[triage] list_patients failed: {exc}")
        raise HTTPException(status_code=503, detail="Unable to load patients. Please retry.") from exc


@router.get("/archives/{session_id}")
async def get_archive(session_id: str) -> dict[str, Any]:
    """Return one full archived session, including patient records."""
    try:
        from app.services.mongo_service import get_mongo_collection
        doc = await get_mongo_collection("triage_archives").find_one({"session_id": session_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found.")

        doc["_id"] = str(doc["_id"])
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to load this archive. Please retry.") from exc
