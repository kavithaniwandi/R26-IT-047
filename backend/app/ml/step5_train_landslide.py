"""
STEP 5 (v2 - with model comparison): Train and compare several models,
pick the best one, and save it. Also saves a chart your panel will like.
Run: python step5_train_landslide.py
Input:  data/landslide_training_data.csv
Output: models/landslide_model.pkl, models/model_comparison.png
"""
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

df = pd.read_csv("data/landslide_training_data.csv")
features = ["elevation", "slope", "avg_rainfall", "rainfall_7d"]
X, y = df[features], df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

candidates = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
    "Decision Tree":       DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced"),
    "Random Forest":       RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, class_weight="balanced"),
}

results = {}
print(f"{'Model':<22}{'Test Accuracy':<16}{'5-fold CV Accuracy':<20}")
print("-" * 58)
for name, model in candidates.items():
    model.fit(X_train, y_train)
    test_acc = accuracy_score(y_test, model.predict(X_test))
    cv_scores = cross_val_score(model, X, y, cv=5)
    results[name] = {"model": model, "test_acc": test_acc, "cv_mean": cv_scores.mean(), "cv_std": cv_scores.std()}
    print(f"{name:<22}{test_acc:<16.3f}{cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

best_name = max(results, key=lambda n: results[n]["cv_mean"])
best_model = results[best_name]["model"]
print(f"\nBest model: {best_name}")
print(f"\n--- Detailed report for {best_name} ---")
print(classification_report(y_test, best_model.predict(X_test)))

# Save a bar chart comparing the models -- put this in your slides
fig, ax = plt.subplots(figsize=(6, 4))
names = list(results.keys())
cv_means = [results[n]["cv_mean"] for n in names]
cv_stds = [results[n]["cv_std"] for n in names]
ax.bar(names, cv_means, yerr=cv_stds, capsize=5, color=["#888", "#888", "#d32f2f"])
ax.set_ylabel("5-fold Cross-Validation Accuracy")
ax.set_title("Landslide Risk Model Comparison")
ax.set_ylim(0, 1)
plt.tight_layout()
plt.savefig("models/model_comparison.png", dpi=150)
print("Saved chart -> models/model_comparison.png")

# Feature importance chart (only meaningful for the tree-based models)
if best_name in ("Random Forest", "Decision Tree"):
    importances = best_model.feature_importances_
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(features, importances, color="#d32f2f")
    ax.set_xlabel("Importance")
    ax.set_title(f"Feature Importance ({best_name})")
    plt.tight_layout()
    plt.savefig("models/feature_importance.png", dpi=150)
    print("Saved chart -> models/feature_importance.png")

joblib.dump({"model": best_model, "features": features, "model_name": best_name},
            "models/landslide_model.pkl")
print(f"\nSaved best model ({best_name}) -> models/landslide_model.pkl")