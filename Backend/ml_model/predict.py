import joblib
import pandas as pd

# Load trained model
model = joblib.load("medical_model.pkl")

# Test input (Kandy / Kaduwela type area)
sample = pd.DataFrame([[5000, 120, 3, 80, 1, 1]], columns=[
    'Population_Density',
    'Emergency_Cases',
    'Nearby_Hospitals',
    'Donation_Requests',
    'Traffic_Level',
    'Risk_Level'
])

# Predict
prediction = model.predict(sample)

print("Prediction:", prediction)

if prediction[0] == 1:
    print("High demand → Medical camp recommended")
else:
    print("Low demand → No camp needed")