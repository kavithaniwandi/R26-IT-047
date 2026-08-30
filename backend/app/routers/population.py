import os
import uuid
import numpy as np
import cv2
from PIL import Image
from fastapi import APIRouter, UploadFile, HTTPException
from ultralytics import YOLO

router = APIRouter(prefix="/population", tags=["Population Estimation"])

# Model configuration: (name, weight file path, BGR color for OpenCV)
MODEL_CONFIGS = [
    {"key": "yolo8", "name": "YOLOv8", "path": "yolo-8-best.pt", "color": (255, 0, 0)},     # Blue (BGR)
    {"key": "yolo11", "name": "YOLOv11", "path": "yolo-11-best.pt", "color": (0, 255, 0)},   # Green (BGR)
    {"key": "yolo26", "name": "YOLO26", "path": "yolo-26-best.pt", "color": (0, 0, 255)},   # Red (BGR)
]

loaded_models = {}
for cfg in MODEL_CONFIGS:
    if os.path.exists(cfg["path"]):
        try:
            loaded_models[cfg["key"]] = YOLO(cfg["path"])
            print(f"Loaded {cfg['name']} from {cfg['path']}")
        except Exception as e:
            print(f"Failed to load {cfg['name']} ({cfg['path']}): {e}")
    else:
        print(f"Warning: Model weight file '{cfg['path']}' not found in root directory.")

def draw_boxes_and_legend(image_cv: np.ndarray, model_counts: dict) -> np.ndarray:
    annotated = image_cv.copy()
    
    # Legend overlay in top-left corner
    legend_x1, legend_y1 = 15, 15
    legend_w, legend_h = 240, 115
    
    overlay = annotated.copy()
    cv2.rectangle(overlay, (legend_x1, legend_y1), (legend_x1 + legend_w, legend_y1 + legend_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)
    cv2.rectangle(annotated, (legend_x1, legend_y1), (legend_x1 + legend_w, legend_y1 + legend_h), (200, 200, 200), 1)

    cv2.putText(annotated, "Model Comparison", (legend_x1 + 10, legend_y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    y_offset = legend_y1 + 45
    for cfg in MODEL_CONFIGS:
        color = cfg["color"]
        count = model_counts.get(cfg["key"], 0)
        label = f"{cfg['name']}: {count} detected"
        
        cv2.rectangle(annotated, (legend_x1 + 10, y_offset - 10), (legend_x1 + 22, y_offset + 2), color, -1)
        cv2.putText(annotated, label, (legend_x1 + 30, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1, cv2.LINE_AA)
        y_offset += 24

    return annotated

@router.post("/count")
async def estimate_crowd_population(file: UploadFile):
    try:
        image_pil = Image.open(file.file).convert("RGB")
        image_np = np.array(image_pil)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        counts = {}
        annotated_bgr = image_bgr.copy()

        # Run inference across all 3 YOLO models with dense crowd tuning
        for cfg in MODEL_CONFIGS:
            key = cfg["key"]
            name = cfg["name"]
            color = cfg["color"]
            model = loaded_models.get(key)

            if model is None:
                counts[key] = 0
                continue

            # Dense crowd parameters:
            # - conf=0.05: Captures back-of-head and shadowed silhouettes
            # - iou=0.65: Prevents dense adjacent heads from deleting each other
            # - imgsz=1280: High-fidelity scale for small distant heads
            # - max_det=1000: Ensures large crowds are not capped
            try:
                results = model(
                    image_pil, 
                    conf=0.05, 
                    iou=0.65, 
                    imgsz=1280, 
                    max_det=1000,
                    classes=[0], 
                    verbose=False
                )
            except Exception:
                results = model(
                    image_pil, 
                    conf=0.05, 
                    iou=0.65, 
                    imgsz=1280, 
                    max_det=1000,
                    verbose=False
                )

            boxes = results[0].boxes
            detected_count = len(boxes) if boxes is not None else 0
            counts[key] = detected_count

            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])
                    
                    # Draw thinner box (thickness=1) to prevent clutter in dense packs
                    cv2.rectangle(annotated_bgr, (x1, y1), (x2, y2), color, 1)
                    
                    # Tag
                    tag = f"{name} {conf:.2f}"
                    (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
                    cv2.rectangle(annotated_bgr, (x1, y1 - th - 3), (x1 + tw + 3, y1), color, -1)
                    cv2.putText(annotated_bgr, tag, (x1 + 1, y1 - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

        final_annotated = draw_boxes_and_legend(annotated_bgr, counts)

        representative_count = max(counts.values()) if counts else 0

        os.makedirs("static/annotated", exist_ok=True)
        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join("static/annotated", filename)
        cv2.imwrite(save_path, final_annotated)

        return {
            "person_count": representative_count,
            "yolo_v8_count": counts.get("yolo8", 0),
            "yolo_11_count": counts.get("yolo11", 0),
            "yolo_26_count": counts.get("yolo26", 0),
            "annotated_image_url": f"http://127.0.0.1:8000/static/annotated/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
