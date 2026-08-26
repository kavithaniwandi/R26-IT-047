import json
import traceback

notebooks = [
    "notebooks/01_model_evaluation_and_testing.ipynb",
    "notebooks/02_disaster_risk_heatmaps_and_spatial_viz.ipynb",
    "notebooks/03_end_to_end_ml_analytics_and_inference.ipynb"
]

for nb_path in notebooks:
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    print(f"Validated {nb_path}: {len(nb['cells'])} cells, nbformat {nb['nbformat']}.{nb['nbformat_minor']}")
    
print("All notebooks verified as valid JSON format.")
