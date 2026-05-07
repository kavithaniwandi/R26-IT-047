import joblib
import pandas as pd
import os

# Load trained model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "../../ml_model/medical_model.pkl")

model = joblib.load(MODEL_PATH)

def predict_demand(data: dict):
    df = pd.DataFrame([[
        data["Population_Density"],
        data["Emergency_Cases"],
        data["Nearby_Hospitals"],
        data["Donation_Requests"],
        data["Traffic_Level"],
        data["Risk_Level"]
    ]], columns=[
        'Population_Density',
        'Emergency_Cases',
        'Nearby_Hospitals',
        'Donation_Requests',
        'Traffic_Level',
        'Risk_Level'
    ])

    prediction = model.predict(df)[0]

    if prediction == 1:
        return {
            "prediction": 1,
            "result": "High demand → Medical camp recommended"
        }
    else:
        return {
            "prediction": 0,
            "result": "Low demand → No camp needed"
        }