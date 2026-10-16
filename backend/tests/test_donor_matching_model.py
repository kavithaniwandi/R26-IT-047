from __future__ import annotations

import pytest

from app.services.donor_matching import (
    EXPECTED_FEATURES,
    load_pipeline,
    model_information,
    predict_compatibility,
    prepare_candidate_rows,
    proximity_score,
)


REQUEST = {
    "disasterType": "Flood",
    "severity": "Critical",
    "people_count": 500,
    "dsArea": "Kaduwela",
    "gnDivision": "Ranala",
    "items": [{
        "itemName": "Drinking Water",
        "requiredCategory": "Water",
        "remainingQuantity": 600,
    }],
}


def test_supplied_pipeline_and_evaluation_are_the_source_of_truth():
    pipeline = load_pipeline()
    assert list(pipeline.feature_names_in_) == EXPECTED_FEATURES
    assert pipeline.named_steps["model"].__class__.__name__ == "LinearRegression"

    info = model_information()
    assert info["selectedModel"] == "Linear Regression"
    assert info["metrics"]["r2"] == pytest.approx(0.8232131043570136)
    assert info["metrics"]["mae"] == pytest.approx(0.06384950031158106)
    assert info["metrics"]["rmse"] == pytest.approx(0.07978733583889859)


def test_live_feature_frame_matches_training_column_order():
    donor = {
        "donor_type": "NGO",
        "preferred_donation_category": "Water",
        "capacity_level": "High",
        "address": "Ranala, Kaduwela",
    }
    rows, details = prepare_candidate_rows(donor, [REQUEST])
    assert details["eligible"] is True
    assert list(rows[0]) == EXPECTED_FEATURES
    assert rows[0]["category_match_score"] == 1.0
    assert rows[0]["proximity_score"] == 1.0


def test_predictions_are_real_model_outputs_and_rank_a_better_match_higher():
    matching = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "capacity_level": "High",
        "address": "Ranala, Kaduwela",
    }
    mismatching = {
        "donor_type": "Individual",
        "preferred_category": "Blankets",
        "capacity_level": "Low",
        "address": "Galle",
    }
    matching_score, matching_details = predict_compatibility(matching, [REQUEST])
    mismatching_score, mismatching_details = predict_compatibility(mismatching, [REQUEST])

    assert 0 <= mismatching_score < matching_score <= 1
    assert matching_details["compatibilityScore"] == pytest.approx(matching_score * 100, abs=0.1)
    assert matching_details["priorityScore"] == pytest.approx(matching_score, abs=1e-6)
    assert "probability" not in "Compatibility Score"
    assert mismatching_details["categoryMatchScore"] == 0.0


def test_incomplete_donor_profile_is_not_scored():
    score, details = predict_compatibility({"address": "Ranala"}, [REQUEST])
    assert score is None
    assert details["eligible"] is False
    assert {"donor type", "preferred category", "capacity level"}.issubset(details["missing"])


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(5, 1.0), (15, 0.9), (30, 0.75), (60, 0.55), (100, 0.35), (101, 0.15)],
)
def test_workbook_proximity_bands(distance, expected):
    assert proximity_score(distance) == expected
