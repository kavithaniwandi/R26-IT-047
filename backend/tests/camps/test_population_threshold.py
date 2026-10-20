from app.routers.population import PERSON_CONFIDENCE_THRESHOLD


def test_yolo_person_confidence_threshold_is_35_percent():
    assert PERSON_CONFIDENCE_THRESHOLD == 0.35
