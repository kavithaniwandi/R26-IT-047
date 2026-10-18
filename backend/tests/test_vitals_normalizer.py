from app.models.vitals_normalizer import normalize_vitals_for_scoring


def warning_codes(result):
    return [item["code"] for item in result.warnings]


def test_spo2_fraction_is_converted_with_warning():
    result = normalize_vitals_for_scoring({"vital_spo2": 0.99})

    assert result.values["vital_spo2"] == 99
    assert warning_codes(result) == ["spo2_fraction_converted"]


def test_spo2_percent_is_unchanged_without_warning():
    result = normalize_vitals_for_scoring({"vital_spo2": 99})

    assert result.values["vital_spo2"] == 99
    assert result.warnings == []


def test_spo2_zero_and_blank_are_missing():
    assert normalize_vitals_for_scoring({"vital_spo2": 0}).values == {}
    assert normalize_vitals_for_scoring({"vital_spo2": ""}).values == {}


def test_spo2_dangerous_low_is_used_with_warning():
    result = normalize_vitals_for_scoring({"vital_spo2": 9.9})

    assert result.values["vital_spo2"] == 9.9
    assert warning_codes(result) == ["implausible_dangerous_low"]


def test_spo2_harmless_high_is_excluded_with_warning():
    result = normalize_vitals_for_scoring({"vital_spo2": 150})

    assert "vital_spo2" not in result.values
    assert warning_codes(result) == ["invalid_harmless_high"]


def test_hr_sbp_dangerous_out_of_range_are_used_with_warning():
    result = normalize_vitals_for_scoring({"vital_hr": 300, "vital_sbp": 40})

    assert result.values["vital_hr"] == 300
    assert result.values["vital_sbp"] == 40
    assert warning_codes(result) == [
        "implausible_dangerous_high",
        "implausible_dangerous_low",
    ]


def test_pain_zero_is_valid():
    result = normalize_vitals_for_scoring({"pain_score": 0})

    assert result.values["pain_score"] == 0
    assert result.warnings == []


def test_temperature_fahrenheit_like_is_used_without_conversion():
    result = normalize_vitals_for_scoring({"vital_temp": 98.6})

    assert result.values["vital_temp"] == 98.6
    assert warning_codes(result) == ["temperature_fahrenheit_suspected"]
