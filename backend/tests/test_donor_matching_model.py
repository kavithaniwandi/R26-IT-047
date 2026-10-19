from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.donor_matching import (
    EXPECTED_FEATURES,
    HYBRID_WEIGHTS,
    capacity_match_score,
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


def test_same_donor_and_request_features_produce_the_same_score():
    """Scoring must be deterministic; live inference must not add random noise."""
    donor = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "capacity_level": "High",
        "address": "Galle",
    }
    equivalent_request = {
        **REQUEST,
        "gnDivision": "A different unmatched division",
        "dsArea": "A different unmatched area",
    }

    first_score, first_details = predict_compatibility(donor, [REQUEST])
    second_score, second_details = predict_compatibility(donor, [equivalent_request])

    assert first_score == pytest.approx(second_score)
    assert first_details["compatibilityScore"] == second_details["compatibilityScore"]
    assert first_details["distanceSource"] == "registered-address estimate"
    assert second_details["distanceSource"] == "registered-address estimate"


def test_precise_coordinates_rank_a_nearby_request_above_a_distant_request():
    donor = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "capacity_level": "High",
        "latitude": 6.93,
        "longitude": 79.98,
    }
    nearby_request = {**REQUEST, "latitude": 6.94, "longitude": 79.98}
    distant_request = {**REQUEST, "latitude": 7.80, "longitude": 80.80}

    nearby_score, nearby_details = predict_compatibility(donor, [nearby_request])
    distant_score, distant_details = predict_compatibility(donor, [distant_request])

    assert nearby_score > distant_score
    assert nearby_details["proximityScore"] == 1.0
    assert distant_details["proximityScore"] == 0.15
    assert nearby_details["distanceKm"] < distant_details["distanceKm"]


def test_capacity_changes_the_score_for_a_large_request():
    large_request = {
        **REQUEST,
        "items": [{
            "itemName": "Drinking Water",
            "requiredCategory": "Water",
            "remainingQuantity": 1500,
        }],
    }
    common_profile = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "address": "Ranala, Kaduwela",
    }

    high_score, high_details = predict_compatibility(
        {**common_profile, "capacity_level": "High"},
        [large_request],
    )
    low_score, low_details = predict_compatibility(
        {**common_profile, "capacity_level": "Low"},
        [large_request],
    )

    assert high_score > low_score
    assert high_details["capacityMatchScore"] == 0.9
    assert low_details["capacityMatchScore"] == 0.3


def test_score_output_is_bounded_and_rounded_to_one_decimal_place():
    donor = {
        "donor_type": "NGO",
        "preferred_category": "Water",
        "capacity_level": "High",
        "address": "Ranala, Kaduwela",
    }

    score, details = predict_compatibility(donor, [REQUEST])

    assert 0.0 <= score <= 1.0
    assert 0.0 <= details["compatibilityScore"] <= 100.0
    assert details["compatibilityScore"] == round(score * 100, 1)


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(5, 1.0), (15, 0.9), (30, 0.75), (60, 0.55), (100, 0.35), (101, 0.15)],
)
def test_workbook_proximity_bands(distance, expected):
    assert proximity_score(distance) == expected


@pytest.mark.parametrize(
    ("capacity", "quantity", "expected"),
    [
        ("Low", 250, 0.9),
        ("Low", 251, 0.55),
        ("Medium", 1000, 0.9),
        ("Medium", 1001, 0.6),
        ("High", 1001, 0.9),
    ],
)
def test_capacity_band_boundaries(capacity, quantity, expected):
    assert capacity_match_score(capacity, quantity) == expected
