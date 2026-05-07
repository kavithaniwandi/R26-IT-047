from fastapi import APIRouter
from models.ml_model import predict_demand

router = APIRouter()

@router.post("/predict")
def predict(data: dict):
    return predict_demand(data)