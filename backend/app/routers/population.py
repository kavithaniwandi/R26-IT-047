"""YOLOv8 population estimation for relief-camp crowd images."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.security import TokenPayload, require_role


router = APIRouter(prefix="/population", tags=["Population Estimation (YOLO)"])
BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BACKEND_DIR / "ml_models" / "population"
ANNOTATED_DIR = BACKEND_DIR / "static" / "annotated"
MODEL_CONFIG = {
    "key": "yolo8",
    "name": "YOLOv8",
    "file": "yolo-8-best.pt",
    "color": (255, 0, 0),
}
_inference_lock = Lock()


@lru_cache(maxsize=1)
def _load_model():
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Ultralytics is not installed. Install backend requirements first.") from exc

    model_path = MODEL_DIR / MODEL_CONFIG["file"]
    if not model_path.is_file():
        raise RuntimeError(f"Missing YOLO weight file: {MODEL_CONFIG['file']}")
    return YOLO(str(model_path))


def _draw_legend(image, person_count, cv2):
    annotated = image.copy()
    x1, y1, width, height = 15, 15, 240, 72
    overlay = annotated.copy()
    cv2.rectangle(overlay, (x1, y1), (x1 + width, y1 + height), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)
    cv2.rectangle(annotated, (x1, y1), (x1 + width, y1 + height), (200, 200, 200), 1)
    cv2.putText(annotated, "Population Detection", (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    color = MODEL_CONFIG["color"]
    cv2.rectangle(annotated, (x1 + 10, y1 + 37), (x1 + 22, y1 + 49), color, -1)
    label = f'{MODEL_CONFIG["name"]}: {person_count} detected'
    cv2.putText(annotated, label, (x1 + 30, y1 + 49), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1, cv2.LINE_AA)
    return annotated


def _run_yolo8(image_bytes: bytes) -> dict:
    try:
        import cv2
        import numpy as np
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError("YOLO image dependencies are not installed.") from exc

    try:
        image_pil = Image.open(BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    image_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    annotated = image_bgr.copy()
    with _inference_lock:
        model = _load_model()
        inference_args = {"conf": 0.05, "iou": 0.65, "imgsz": 1280, "max_det": 1000, "verbose": False}
        try:
            results = model(image_pil, classes=[0], **inference_args)
        except Exception:
            results = model(image_pil, **inference_args)

        boxes = results[0].boxes
        person_count = len(boxes) if boxes is not None else 0
        if boxes is not None:
            for box in boxes:
                bx1, by1, bx2, by2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                color = MODEL_CONFIG["color"]
                cv2.rectangle(annotated, (bx1, by1), (bx2, by2), color, 1)
                tag = f'{MODEL_CONFIG["name"]} {confidence:.2f}'
                (text_width, text_height), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
                cv2.rectangle(annotated, (bx1, by1 - text_height - 3), (bx1 + text_width + 3, by1), color, -1)
                cv2.putText(annotated, tag, (bx1 + 1, by1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.jpg"
    final_image = _draw_legend(annotated, person_count, cv2)
    if not cv2.imwrite(str(ANNOTATED_DIR / filename), final_image):
        raise RuntimeError("Could not save the annotated population image.")
    return {
        "person_count": person_count,
        "yolo_v8_count": person_count,
        "detector": "yolo8",
        "model": MODEL_CONFIG["file"],
        "annotated_image_url": f"/static/annotated/{filename}",
    }


@router.post("/count")
async def estimate_crowd_population(
    file: UploadFile,
    _user: TokenPayload = Depends(require_role(["admin", "volunteer"])),
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="An image file is required.")
    try:
        return await run_in_threadpool(_run_yolo8, image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}") from exc
