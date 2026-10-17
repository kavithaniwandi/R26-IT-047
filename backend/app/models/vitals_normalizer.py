from __future__ import annotations

from dataclasses import dataclass, field
import logging
import math
from typing import Any

from app.models.config import settings


logger = logging.getLogger(__name__)

VITAL_KEYS = (
    "vital_hr",
    "vital_spo2",
    "vital_sbp",
    "vital_dbp",
    "vital_rr",
    "vital_temp",
    "pain_score",
    "gcs",
)

ML_VITAL_KEYS = {
    "vital_hr",
    "vital_spo2",
    "vital_sbp",
    "vital_rr",
    "vital_temp",
    "pain_score",
}

ZERO_IS_MISSING_VITAL_KEYS = {"vital_spo2", "vital_hr", "vital_sbp"}


@dataclass(frozen=True)
class VitalSpec:
    label: str
    unit: str
    low: float
    high: float
    low_side: str
    high_side: str


# Direction table:
# - dangerous: keep current scoring behavior, but warn.
# - harmless: exclude from scoring, but warn.
VITAL_SPECS: dict[str, VitalSpec] = {
    "vital_spo2": VitalSpec("SpO2", "%", 50.0, 100.0, "dangerous", "harmless"),
    "vital_hr": VitalSpec("Heart rate", "bpm", 20.0, 250.0, "dangerous", "dangerous"),
    "vital_sbp": VitalSpec("Systolic BP", "mmHg", 50.0, 300.0, "dangerous", "dangerous"),
    "vital_dbp": VitalSpec("Diastolic BP", "mmHg", 30.0, 200.0, "harmless", "harmless"),
    "vital_rr": VitalSpec("Respiratory rate", "/min", 4.0, 80.0, "dangerous", "dangerous"),
    "vital_temp": VitalSpec("Temperature", "C", 30.0, 43.0, "dangerous", "dangerous"),
    "pain_score": VitalSpec("Pain", "0-10", 0.0, 10.0, "harmless", "dangerous"),
    "gcs": VitalSpec("GCS", "3-15", 3.0, 15.0, "harmless", "harmless"),
}


@dataclass
class NormalizedVitals:
    values: dict[str, float] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def get(self, key: str) -> float | None:
        return self.values.get(key)

    def count_for_ml(self) -> int:
        return sum(1 for key in ML_VITAL_KEYS if key in self.values)


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _warning(
    field: str,
    raw_value: Any,
    used_value: float | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "field": field,
        "raw_value": raw_value,
        "used_value": used_value,
        "code": code,
        "message": message,
    }


def _as_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def normalize_vitals_for_scoring(vitals: dict | None) -> NormalizedVitals:
    normalized = NormalizedVitals()
    raw_vitals = vitals or {}

    for key in VITAL_KEYS:
        raw_value = raw_vitals.get(key)
        if _is_missing(raw_value):
            continue

        numeric = _as_float(raw_value)
        spec = VITAL_SPECS[key]
        if numeric is None:
            normalized.warnings.append(
                _warning(
                    key,
                    raw_value,
                    None,
                    "non_numeric",
                    f"{spec.label} is not numeric and was not used.",
                )
            )
            continue

        if key in ZERO_IS_MISSING_VITAL_KEYS and numeric <= 0:
            continue

        if key == "vital_spo2" and 0 < numeric <= 1:
            used = round(numeric * 100, 4)
            normalized.values[key] = used
            normalized.warnings.append(
                _warning(
                    key,
                    raw_value,
                    used,
                    "spo2_fraction_converted",
                    f"SpO2 {raw_value} was read as {used:g}%. Please confirm.",
                )
            )
            continue

        if key == "vital_temp" and 86 <= numeric <= 110:
            normalized.values[key] = numeric
            normalized.warnings.append(
                _warning(
                    key,
                    raw_value,
                    numeric,
                    "temperature_fahrenheit_suspected",
                    f"Temperature {raw_value} looks like Fahrenheit; it was not converted. Please confirm Celsius entry.",
                )
            )
            continue

        if numeric < spec.low:
            if spec.low_side == "dangerous":
                normalized.values[key] = numeric
                normalized.warnings.append(
                    _warning(
                        key,
                        raw_value,
                        numeric,
                        "implausible_dangerous_low",
                        f"{spec.label} {raw_value} is not plausible, please confirm.",
                    )
                )
            else:
                normalized.warnings.append(
                    _warning(
                        key,
                        raw_value,
                        None,
                        "invalid_harmless_low",
                        f"{spec.label} {raw_value} is outside the valid range and was not used.",
                    )
                )
            continue

        if numeric > spec.high:
            if spec.high_side == "dangerous":
                normalized.values[key] = numeric
                normalized.warnings.append(
                    _warning(
                        key,
                        raw_value,
                        numeric,
                        "implausible_dangerous_high",
                        f"{spec.label} {raw_value} is not plausible, please confirm.",
                    )
                )
            else:
                normalized.warnings.append(
                    _warning(
                        key,
                        raw_value,
                        None,
                        "invalid_harmless_high",
                        f"{spec.label} {raw_value} is outside the valid range and was not used.",
                    )
                )
            continue

        normalized.values[key] = numeric

    if getattr(settings, "TRIAGE_DEBUG_VITALS", False):
        logger.info(
            "triage vitals normalized fields=%s warnings=%s",
            sorted(normalized.values),
            [
                {"field": item["field"], "code": item["code"], "used_value": item["used_value"]}
                for item in normalized.warnings
            ],
        )

    return normalized


def normalized_vital_value(vitals: dict | None, key: str) -> float | None:
    return normalize_vitals_for_scoring(vitals).get(key)
