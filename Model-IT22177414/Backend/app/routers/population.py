import io
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image
from ultralytics import YOLO

router = APIRouter(prefix="/population", tags=["Population Estimation"])

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

        return {
            "status": "success",
            "filename": file.filename,
            "person_count": person_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )