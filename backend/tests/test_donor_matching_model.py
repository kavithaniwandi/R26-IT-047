from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.donor_matching import (
    EXPECTED_FEATURES,
    HYBRID_WEIGHTS,
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


def test_explainable_hybrid_score_metadata_is_the_source_of_truth():
    info = model_information()
    assert info["selectedModel"] == "Explainable Hybrid Match Score"
    assert info["method"] == "weighted_rule_based"
    assert sum(HYBRID_WEIGHTS.values()) == pytest.approx(1.0)
    assert info["weights"] == {
        "category": 30,
        "proximity": 25,
        "capacity": 20,
        "reliability": 15,
        "recency": 10,
    }


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


def test_explainable_score_ranks_a_better_profile_higher():
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
    assert mismatching_details["categoryMatchScore"] == 0.0
    assert matching_details["factorScores"]["category"] == 100.0


def test_real_completion_history_changes_ranking_and_confidence():
    donor = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "capacity_level": "High",
        "latitude": 6.9339,
        "longitude": 79.9835,
        "address": "Ranala, Kaduwela",
    }
    successful_history = [
        {
            "status": "received",
            "acceptedAt": datetime.now(timezone.utc) - timedelta(days=10),
        }
        for _ in range(5)
    ]
    cancelled_history = [{"status": "cancelled"} for _ in range(5)]

    located_request = {**REQUEST, "latitude": 6.93, "longitude": 79.98}
    successful_score, successful = predict_compatibility(donor, [located_request], successful_history)
    cancelled_score, cancelled = predict_compatibility(donor, [located_request], cancelled_history)

    assert successful_score > cancelled_score
    assert successful["reliabilityScore"] == 1.0
    assert successful["recencyScore"] == 1.0
    assert successful["confidence"] == "High"
    assert cancelled["reliabilityScore"] == 0.0


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
