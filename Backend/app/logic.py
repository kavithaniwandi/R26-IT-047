"""
All the rule-based logic for the 3 non-ML components.
No training needed here -- these are plain formulas per the proposal spec.
"""
import math


def haversine_km(lat1, lng1, lat2, lng2):
    """Distance in km between two lat/lng points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def update_heatmap(base_risk_score: float, sos_count_last_hour: int, affected_people: int) -> float:
    """Component 2: heatmap optimization. Blends the trained model's base score
    with live SOS signal so the map updates in real time as requests come in."""
    sos_signal = min(sos_count_last_hour / 10, 1.0)
    people_signal = min(affected_people / 50, 1.0)
    live_score = 0.5 * base_risk_score + 0.3 * sos_signal + 0.2 * people_signal
    return round(min(live_score, 1.0), 3)


def should_recommend_camp(sos_count: int, injured_count: int, nearest_hospital_km: float, live_risk: float) -> bool:
    """Component 2: medical camp decision. Tune the 30 threshold against your
    seeded demo data once you see real-looking numbers."""
    score = (sos_count * 2) + (injured_count * 5) + (nearest_hospital_km * 1.5) + (live_risk * 20)
    return score >= 30


def priority_score(num_affected: int, has_children: bool, has_elderly: bool,
                    has_injured: bool, live_risk_at_location: float) -> float:
    """Component 3: priority scoring for one SOS request."""
    score = num_affected * 3
    score += 15 if has_injured else 0
    score += 10 if (has_children or has_elderly) else 0
    score += live_risk_at_location * 20
    return round(score, 1)


def match_donor(sos_lat, sos_lng, needed_item, donors):
    """Component 3: pick the best available donor for one SOS request.
    `donors` is a list of dict-like rows with lat, lng, item_type, quantity, available."""
    candidates = [d for d in donors if d.available and d.item_type == needed_item]
    if not candidates:
        return None
    best, best_score = None, -1
    for d in candidates:
        dist = haversine_km(sos_lat, sos_lng, d.lat, d.lng)
        match_score = d.quantity / (dist + 1)
        if match_score > best_score:
            best, best_score = d, match_score
    return best
