import io
import os
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image
from ultralytics import YOLO

router = APIRouter(prefix="/population", tags=["Population Estimation"])

# Ensure directory for annotated image persistence exists
UPLOAD_DIR = os.path.join(os.getcwd(), "static", "annotated")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load YOLO model once during startup
model = YOLO('yolov8x.pt')

@router.post("/count", status_code=status.HTTP_200_OK)
async def count_population(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Uploaded file must be an image."
        )

    try:
        # Read uploaded image bytes and convert to PIL Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Run inference filtering for class 0 (person)
        results = model(image, classes=[0], verbose=False)
        person_count = len(results[0].boxes)

        # Generate annotated image with bounding boxes
        annotated_bgr = results[0].plot()  # numpy array (BGR format)
        annotated_image = Image.fromarray(annotated_bgr[..., ::-1])  # Convert BGR -> RGB

        # Save annotated image with unique filename
        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(UPLOAD_DIR, filename)
        annotated_image.save(save_path, "JPEG", quality=90)

        # URL to access the saved annotated image
        annotated_url = f"http://127.0.0.1:8000/static/annotated/{filename}"

        return {
            "status": "success",
            "filename": file.filename,
            "person_count": person_count,
            "annotated_image_url": annotated_url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image with YOLO: {str(e)}"
        )