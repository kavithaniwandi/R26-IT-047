"""
FLOOD STEP 3 (with model comparison): Train and compare models, save the best.
Run: python flood_step3_train.py
Input:  data/flood_training_data.csv
Output: models/flood_model.pkl, models/flood_model_comparison.png

NOTE: this dataset is small (68 rows) since Kaduwela only has 34 confirmed
flood-affected divisions. That's expected and fine to state plainly in
your report -- it's real data, just a small area.
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
from sklearn.metrics import classification_report, accuracy_score

df = pd.read_csv("data/flood_training_data.csv")
features = ["elevation", "avg_rainfall", "rainfall_7d", "dist_to_river_km"]
X, y = df[features], df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

candidates = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
    "Decision Tree":       DecisionTreeClassifier(max_depth=5, random_state=42, class_weight="balanced"),
    "Random Forest":       RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42, class_weight="balanced"),
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

fig, ax = plt.subplots(figsize=(6, 4))
names = list(results.keys())
cv_means = [results[n]["cv_mean"] for n in names]
cv_stds = [results[n]["cv_std"] for n in names]
ax.bar(names, cv_means, yerr=cv_stds, capsize=5, color=["#888", "#888", "#1565c0"])
ax.set_ylabel("5-fold Cross-Validation Accuracy")
ax.set_title("Flood Risk Model Comparison")
ax.set_ylim(0, 1)
plt.tight_layout()
plt.savefig("models/flood_model_comparison.png", dpi=150)
print("Saved chart -> models/flood_model_comparison.png")

if best_name in ("Random Forest", "Decision Tree"):
    importances = best_model.feature_importances_
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(features, importances, color="#1565c0")
    ax.set_xlabel("Importance")
    ax.set_title(f"Feature Importance ({best_name})")
    plt.tight_layout()
    plt.savefig("models/flood_feature_importance.png", dpi=150)
    print("Saved chart -> models/flood_feature_importance.png")

joblib.dump({"model": best_model, "features": features, "model_name": best_name},
            "models/flood_model.pkl")
print(f"\nSaved best model ({best_name}) -> models/flood_model.pkl")