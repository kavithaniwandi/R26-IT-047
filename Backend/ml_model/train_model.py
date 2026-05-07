import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Load dataset
data = pd.read_csv("medical_demand_dataset.csv")
print("Dataset loaded successfully")

# Encode categorical columns
le_traffic = LabelEncoder()
le_risk = LabelEncoder()
le_target = LabelEncoder()

data['Traffic_Level'] = le_traffic.fit_transform(data['Traffic_Level'])
data['Risk_Level'] = le_risk.fit_transform(data['Risk_Level'])
data['Recommended_Camp'] = le_target.fit_transform(data['Recommended_Camp'])

# Features
X = data[[
    'Population_Density',
    'Emergency_Cases',
    'Nearby_Hospitals',
    'Donation_Requests',
    'Traffic_Level',
    'Risk_Level'
]]

# Target
y = data['Recommended_Camp']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

# Predictions
predictions = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)
print("Training completed successfully")

# -------------------------------
# SAVE MODEL (IMPORTANT FOR NEXT STEP)
# -------------------------------
joblib.dump(model, "medical_model.pkl")
print("Model saved as medical_model.pkl")

# -------------------------------
# TEST PREDICTION (FIXED VERSION)
# -------------------------------
sample = pd.DataFrame([[5000, 120, 3, 80, 1, 1]], columns=[
    'Population_Density',
    'Emergency_Cases',
    'Nearby_Hospitals',
    'Donation_Requests',
    'Traffic_Level',
    'Risk_Level'
])

prediction = model.predict(sample)

print("Prediction result:", prediction)

if prediction[0] == 1:
    print("High demand → Medical camp recommended")
else:
    print("Low demand → No camp needed")