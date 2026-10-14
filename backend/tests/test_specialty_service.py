from app.models.severity_service import classify_note
from app.models.specialty_service import suggest_specialty


def test_severe_breathlessness_critical_suggests_emergency_then_respiratory():
    result = suggest_specialty(
        "severe breathlessness SpO2 82 cyanosis",
        "Severe respiratory distress with cyanosis.",
        {"breathing_difficulty": 1},
        45,
        "CRITICAL",
        [],
    )

    assert result["primary"] == "Emergency Medicine"
    assert "Respiratory" in result["secondary"]
    assert not result["fallback"]


def test_crush_injury_critical_suggests_emergency_then_trauma_surgery():
    result = suggest_specialty(
        "crush injury, heavy bleeding, shock",
        "Crush injury with heavy bleeding and shock.",
        {"active_bleeding": 1},
        32,
        "CRITICAL",
        [],
    )

    assert result["primary"] == "Emergency Medicine"
    assert "Trauma & Surgery" in result["secondary"]


def test_stroke_features_critical_suggests_emergency_then_neurological():
    result = suggest_specialty(
        "facial droop, slurred speech, arm weakness",
        "Possible stroke.",
        {"focal_neurologic_deficit": 1},
        70,
        "CRITICAL",
        [],
    )

    assert result["primary"] == "Emergency Medicine"
    assert "Neurological" in result["secondary"]


def test_pregnancy_bleeding_suggests_obstetric_gynecologic():
    result = suggest_specialty(
        "34 weeks pregnant, vaginal bleeding",
        "Pregnancy with vaginal bleeding.",
        {},
        29,
        "HIGH",
        [],
    )

    assert result["primary"] == "Obstetric & Gynecologic"


def test_child_dehydration_suggests_pediatric():
    result = suggest_specialty(
        "diarrhoea, vomiting, dehydration",
        "Child with diarrhoea and vomiting.",
        {},
        4,
        "HIGH",
        [],
    )

    assert result["primary"] == "Pediatric"


def test_infected_wound_suggests_trauma_surgery():
    result = suggest_specialty(
        "infected foot wound with pus, fever",
        "Foot wound discharging pus.",
        {},
        50,
        "MEDIUM",
        [],
    )

    assert result["primary"] == "Trauma & Surgery"


def test_forearm_deformity_after_fall_suggests_orthopedic():
    result = suggest_specialty(
        "forearm deformity after fall",
        "Teenager with forearm deformity after a fall.",
        {},
        15,
        "MEDIUM",
        [],
    )

    assert result["primary"] == "Orthopedic"


def test_leptospirosis_exposure_suggests_infection_systemic():
    result = suggest_specialty(
        "fever, muscle pain, paddy fields, leptospirosis",
        "Fever and myalgia after working in paddy fields.",
        {},
        35,
        "MEDIUM",
        [],
    )

    assert result["primary"] == "Infection & Systemic"


def test_small_cut_suggests_general_practice():
    result = suggest_specialty(
        "small cut on hand",
        "Small superficial cut on hand.",
        {},
        28,
        "LOW",
        [],
    )

    assert result["primary"] == "General Practice"


def test_mild_headache_diabetes_medication_suggests_endocrine_or_gp():
    result = suggest_specialty(
        "mild headache, ran out of diabetes medication",
        "Needs diabetes medication refill.",
        {},
        47,
        "LOW",
        ["headache pain in head", "medication refill", "diabetes follow up"],
    )

    assert result["primary"] in {"Endocrine & Metabolic", "General Practice"}
    assert not result["fallback"]


def test_negated_chest_and_breathlessness_do_not_suggest_cardio_or_respiratory():
    result = suggest_specialty(
        "no chest pain, no shortness of breath, mild headache",
        "Denies cough and chest pain.",
        {},
        36,
        "LOW",
        ["headache pain in head"],
    )

    assert result["primary"] not in {"Cardiovascular", "Respiratory"}
    assert "Cardiovascular" not in result["secondary"]
    assert "Respiratory" not in result["secondary"]


def test_gibberish_falls_back_to_general_practice():
    result = suggest_specialty("xqzv blorp", "xqzv blorp", {}, 40, "MEDIUM", [])

    assert result["primary"] == "General Practice"
    assert result["fallback"] is True
    assert result["reason"] == "No specific specialty keywords found"


def test_classify_note_includes_advisory_specialty_without_changing_severity_shape():
    result = classify_note(
        clinical_note="Needs diabetes medication refill, vitals stable.",
        age=47,
        mode="ml",
        symptoms="Mild headache, ran out of diabetes medication",
        vitals={
            "vital_hr": 78,
            "vital_spo2": 98,
            "vital_sbp": 122,
            "vital_rr": 16,
        },
    )

    assert result["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert result["suggested_specialty"]["primary"] in {"Endocrine & Metabolic", "General Practice"}


def test_hypoxic_headache_suggests_emergency_or_respiratory_not_neurological():
    result = suggest_specialty(
        "headache",
        "headache",
        {},
        45,
        "HIGH",
        ["headache pain in head"],
        vitals={"vital_spo2": 88, "vital_hr": 130},
    )

    assert result["primary"] in {"Emergency Medicine", "Respiratory"}
    assert result["primary"] != "Neurological"


def test_insulin_with_confusion_prioritizes_emergency_then_endocrine():
    result = suggest_specialty(
        "ran out of insulin, confused and drowsy",
        "ran out of insulin, confused and drowsy",
        {},
        60,
        "HIGH",
        [],
        vitals={"vital_hr": 130, "vital_spo2": 88, "vital_rr": 26},
    )

    assert result["primary"] == "Emergency Medicine"
    assert result["secondary"][0] == "Endocrine & Metabolic"
    assert all(specialty in {"Endocrine & Metabolic", "Neurological"} for specialty in result["secondary"])


def test_low_severity_moves_clinical_specialty_to_secondary_except_obstetric_and_pediatric():
    result = suggest_specialty(
        "mild headache, ran out of diabetes medication",
        "Needs diabetes medication refill.",
        {},
        47,
        "LOW",
        ["headache pain in head", "medication refill", "diabetes follow up"],
    )
    assert result["primary"] == "General Practice"
    assert "Endocrine & Metabolic" in result["secondary"]

    pediatric = suggest_specialty("diarrhoea", "child diarrhoea", {}, 4, "LOW", [])
    assert pediatric["primary"] == "Pediatric"

    obstetric = suggest_specialty("pregnant vaginal bleeding", "pregnant vaginal bleeding", {}, 29, "LOW", [])
    assert obstetric["primary"] == "Obstetric & Gynecologic"


def _matched_keywords_for_vitals(vitals):
    result = suggest_specialty(
        "chest pain",
        "Chest pain reported.",
        {},
        45,
        "HIGH",
        ["chest pain"],
        vitals=vitals,
    )
    return result["matched_keywords"]


def test_missing_spo2_does_not_trigger_respiratory_vital_rule():
    for vitals in [
        {},
        {"vital_spo2": None},
        {"vital_spo2": ""},
        {"vital_spo2": "not recorded"},
        {"vital_spo2": float("nan")},
        {"vital_spo2": 0},
    ]:
        assert "SpO2 < 92" not in _matched_keywords_for_vitals(vitals)


def test_normal_spo2_does_not_trigger_respiratory_vital_rule():
    assert "SpO2 < 92" not in _matched_keywords_for_vitals({"vital_spo2": 95})
    assert "SpO2 < 92" not in _matched_keywords_for_vitals({"vital_spo2": 0.99})


def test_low_spo2_triggers_respiratory_vital_rule():
    assert "SpO2 < 92" in _matched_keywords_for_vitals({"vital_spo2": 88})


def test_missing_hr_and_sbp_do_not_trigger_emergency_vital_rules():
    for vitals in [
        {"vital_hr": None, "vital_sbp": None},
        {"vital_hr": "", "vital_sbp": ""},
        {"vital_hr": "unknown", "vital_sbp": "unknown"},
        {"vital_hr": float("nan"), "vital_sbp": float("nan")},
        {"vital_hr": 0, "vital_sbp": 0},
    ]:
        keywords = _matched_keywords_for_vitals(vitals)
        assert "HR > 120" not in keywords
        assert "SBP < 90" not in keywords


def test_four_of_six_vitals_are_enough_without_missing_spo2_threshold_hit():
    result = classify_note(
        clinical_note="Chest pain reported, stable and alert.",
        age=45,
        mode="ml",
        symptoms="chest pain",
        vitals={
            "vital_hr": 82,
            "vital_sbp": 126,
            "vital_rr": 16,
            "vital_temp": 36.9,
            "vital_spo2": "",
        },
    )

    assert result["incomplete_vitals"] is False
    assert "SpO2 < 92" not in result["suggested_specialty"]["matched_keywords"]
