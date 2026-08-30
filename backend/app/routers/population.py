"""Lightweight crowd estimation endpoint for the relief-camp workflow.

The original component's custom YOLO weight files are not part of the merged
repository. This adapter keeps photo analysis operational with OpenCV's local
person detector and leaves the browser preview unchanged.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.security import TokenPayload, require_role


router = APIRouter(prefix="/population", tags=["Relief Camp Population"])


@router.post("/count")
async def estimate_crowd_population(
    file: UploadFile,
    _current_user: TokenPayload = Depends(require_role(["admin", "volunteer"])),
):
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Photo crowd estimation requires OpenCV.",
        ) from exc

    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    detector = cv2.HOGDescriptor()
    detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes, _weights = detector.detectMultiScale(
        image,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05,
    )
    count = len(boxes)
    return {
        "person_count": count,
        "detector": "opencv_hog",
        "annotated_image_url": None,
    }
