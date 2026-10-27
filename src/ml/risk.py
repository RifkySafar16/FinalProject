"""Transparent, educational rule-based heart-disease risk scoring.

This heuristic is not a clinically validated risk calculator or diagnosis.
"""

from __future__ import annotations

import math
from typing import Any, TypedDict

from src.ml.predict import FEATURE_COLUMNS


class RiskInputError(ValueError):
    """Raised when risk-classification input is incomplete or invalid."""


class RiskFactor(TypedDict):
    feature: str
    value: float
    points: int
    reason: str


RISK_THRESHOLDS = {
    "age": {"moderate_min": 45, "high_min": 65},
    "trestbps": {"moderate_min": 120, "high_min": 130},
    "chol": {"moderate_min": 200, "high_min": 240},
    "thalach": {
        "moderate_below_max_fraction": 0.85,
        "high_below_max_fraction": 0.70,
    },
    "oldpeak": {"moderate_min": 0.1, "high_min": 1.0},
}

INPUT_NUMERIC_BOUNDS = {
    "age": (0, 120),
    "trestbps": (70, 250),
    "chol": (0, 1000),
    "thalach": (0, 300),
    "oldpeak": (-10, 20),
}

FEATURE_WEIGHTS = {
    "age": 2,
    "sex": 1,
    "cp": 2,
    "trestbps": 3,
    "chol": 1,
    "fbs": 1,
    "restecg": 1,
    "thalach": 1,
    "exang": 2,
    "oldpeak": 2,
    "slope": 2,
    "ca": 2,
    "thal": 2,
}

# Category scores represent meanings in the Cleveland dataset, not ordinal
# encodings. Each value is a heuristic severity level from 0 to 2.
CATEGORY_RISK_LEVELS = {
    "sex": {0: 0, 1: 1},
    "cp": {1: 2, 2: 1, 3: 0, 4: 1},
    "fbs": {0: 0, 1: 1},
    "restecg": {0: 0, 1: 1, 2: 1},
    "exang": {0: 0, 1: 2},
    "slope": {1: 0, 2: 1, 3: 2},
    "ca": {0: 0, 1: 1, 2: 2, 3: 2},
    "thal": {3: 0, 6: 1, 7: 2},
}

CATEGORY_MEANINGS = {
    "sex": {0: "perempuan", 1: "laki-laki"},
    "cp": {
        1: "angina tipikal",
        2: "angina atipikal",
        3: "nyeri non-angina",
        4: "asimtomatik",
    },
    "fbs": {0: "gula darah puasa <=120 mg/dL", 1: "gula darah puasa >120 mg/dL"},
    "restecg": {
        0: "EKG istirahat normal",
        1: "abnormalitas ST-T",
        2: "kemungkinan/definitif hipertrofi ventrikel kiri",
    },
    "exang": {0: "tidak ada angina saat olahraga", 1: "ada angina saat olahraga"},
    "slope": {1: "segmen ST menanjak", 2: "segmen ST datar", 3: "segmen ST menurun"},
    "ca": {
        0: "0 pembuluh utama terwarnai",
        1: "1 pembuluh utama terwarnai",
        2: "2 pembuluh utama terwarnai",
        3: "3 pembuluh utama terwarnai",
    },
    "thal": {3: "normal", 6: "defek tetap", 7: "defek reversibel"},
}

RISK_SCORE_THRESHOLDS = {
    "low": (0, 10),
    "moderate": (11, 22),
    "high": (23, None),
}

MAX_RISK_SCORE = sum(
    FEATURE_WEIGHTS[feature]
    * (
        2
        if feature in RISK_THRESHOLDS
        else max(CATEGORY_RISK_LEVELS[feature].values())
    )
    for feature in FEATURE_COLUMNS
)

DISCLAIMER = (
    "Skor ini adalah heuristik edukasi, bukan diagnosis atau kalkulator risiko "
    "klinis tervalidasi. Konsultasikan hasil kesehatan dengan tenaga medis."
)


def validate_risk_input(input_data: dict[str, Any]) -> dict[str, float]:
    if not isinstance(input_data, dict):
        raise RiskInputError("Input harus berupa objek.")

    missing = set(FEATURE_COLUMNS) - set(input_data)
    unexpected = set(input_data) - set(FEATURE_COLUMNS)
    if missing:
        raise RiskInputError(f"Fitur wajib belum diisi: {sorted(missing)}")
    if unexpected:
        raise RiskInputError(f"Fitur tidak dikenal: {sorted(unexpected)}")

    validated: dict[str, float] = {}
    for feature in FEATURE_COLUMNS:
        value = input_data[feature]
        if value is None or isinstance(value, bool):
            raise RiskInputError(f"Fitur '{feature}' harus berupa angka.")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise RiskInputError(
                f"Fitur '{feature}' harus berupa angka.") from exc
        if not math.isfinite(number):
            raise RiskInputError(
                f"Fitur '{feature}' harus berupa angka finite.")

        if feature in INPUT_NUMERIC_BOUNDS:
            minimum, maximum = INPUT_NUMERIC_BOUNDS[feature]
            if not minimum <= number <= maximum:
                raise RiskInputError(
                    f"Fitur '{feature}' harus berada di antara {minimum} dan "
                    f"{maximum}; nilai {number:g} di luar rentang input yang "
                    "diterima."
                )
        elif not number.is_integer() or int(number) not in CATEGORY_RISK_LEVELS[feature]:
            allowed = sorted(CATEGORY_RISK_LEVELS[feature])
            raise RiskInputError(
                f"Fitur '{feature}' harus salah satu dari {allowed}."
            )

        validated[feature] = number

    return validated


def _numeric_risk_level(
    feature: str,
    value: float,
    age: float,
) -> tuple[int, str]:
    thresholds = RISK_THRESHOLDS[feature]

    if feature == "age":
        if value >= thresholds["high_min"]:
            return 2, "usia >=65 tahun (ambang heuristik)"
        if value >= thresholds["moderate_min"]:
            return 1, "usia 45-64 tahun (ambang heuristik)"
        return 0, ""

    if feature == "trestbps":
        if value >= thresholds["high_min"]:
            return 2, "tekanan sistolik istirahat >=130 mmHg"
        if value >= thresholds["moderate_min"]:
            return 1, "tekanan sistolik istirahat 120-129 mmHg"
        return 0, ""

    if feature == "chol":
        if value >= thresholds["high_min"]:
            return 2, "kolesterol total >=240 mg/dL"
        if value >= thresholds["moderate_min"]:
            return 1, "kolesterol total 200-239 mg/dL"
        return 0, ""

    if feature == "thalach":
        estimated_max = 220 - age
        fraction = value / estimated_max
        if fraction < thresholds["high_below_max_fraction"]:
            return 2, "denyut maksimum <70% perkiraan 220 - usia"
        if fraction < thresholds["moderate_below_max_fraction"]:
            return 1, "denyut maksimum <85% perkiraan 220 - usia"
        return 0, ""

    if feature == "oldpeak":
        if value >= thresholds["high_min"]:
            return 2, "ST depression >=1 mm (ambang heuristik)"
        if value >= thresholds["moderate_min"]:
            return 1, "ST depression >0 dan <1 mm (ambang heuristik)"
        return 0, ""

    raise ValueError(f"No numeric scoring rule configured for '{feature}'.")


def score_risk_features(
    validated: dict[str, float],
) -> tuple[int, list[RiskFactor]]:
    score = 0
    factors: list[RiskFactor] = []
    numeric_features = set(RISK_THRESHOLDS)

    for feature in FEATURE_COLUMNS:
        value = validated[feature]
        if feature in numeric_features:
            level, reason = _numeric_risk_level(
                feature,
                value,
                validated["age"],
            )
        else:
            category = int(value)
            level = CATEGORY_RISK_LEVELS[feature][category]
            reason = CATEGORY_MEANINGS[feature][category] if level else ""

        points = level * FEATURE_WEIGHTS[feature]
        if points:
            score += points
            factors.append(
                {
                    "feature": feature,
                    "value": value,
                    "points": points,
                    "reason": reason,
                }
            )

    return score, factors


def classify_heart_disease_risk(input_data: dict[str, Any]) -> dict[str, Any]:
    validated = validate_risk_input(input_data)
    score, factors = score_risk_features(validated)

    for level, (minimum, maximum) in RISK_SCORE_THRESHOLDS.items():
        if score >= minimum and (maximum is None or score <= maximum):
            return {
                "risk_level": level,
                "score": score,
                "max_score": MAX_RISK_SCORE,
                "factors": factors,
                "disclaimer": DISCLAIMER,
            }

    raise RuntimeError(
        f"Risk score {score} is not covered by configured thresholds.")
