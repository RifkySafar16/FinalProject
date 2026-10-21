
"""Load the trained heart-disease pipeline and run inference."""

from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "heart_model.pkl"

FEATURE_COLUMNS = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]

ALLOWED_CATEGORIES = {
    "sex": {0, 1},
    "cp": {1, 2, 3, 4},
    "fbs": {0, 1},
    "restecg": {0, 1, 2},
    "exang": {0, 1},
    "slope": {1, 2, 3},
    "ca": {0, 1, 2, 3},
    "thal": {3, 6, 7},
}

NUMERIC_BOUNDS = {
    "age": (0, 120),
    "trestbps": (0, 400),
    "chol": (0, 1000),
    "thalach": (0, 300),
    "oldpeak": (-10, 20),
}


class PredictionError(ValueError):
    """Raised when prediction input is invalid."""


class HeartDiseasePredictor:
    """Run predictions using the saved, fitted sklearn pipeline."""

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
    ) -> None:
        self.model_path = Path(model_path)

        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        with self.model_path.open("rb") as file:
            self.model = pickle.load(file)

        if not hasattr(self.model, "predict"):
            raise TypeError("Loaded artifact does not support predict().")

        if not hasattr(self.model, "predict_proba"):
            raise TypeError(
                "Loaded model does not support predict_proba()."
            )

    @staticmethod
    def validate_features(
        features: dict[str, Any],
    ) -> dict[str, float]:
        if not isinstance(features, dict):
            raise PredictionError("Input must be a dictionary.")

        missing = set(FEATURE_COLUMNS) - set(features)
        unexpected = set(features) - set(FEATURE_COLUMNS)

        if missing:
            raise PredictionError(
                f"Missing features: {sorted(missing)}"
            )

        if unexpected:
            raise PredictionError(
                f"Unexpected features: {sorted(unexpected)}"
            )

        validated: dict[str, float] = {}

        for column in FEATURE_COLUMNS:
            value = features[column]

            if value is None or isinstance(value, bool):
                raise PredictionError(
                    f"Feature '{column}' must be a numeric value."
                )

            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise PredictionError(
                    f"Feature '{column}' must be numeric."
                ) from exc

            if not math.isfinite(number):
                raise PredictionError(
                    f"Feature '{column}' must be finite."
                )

            if column in ALLOWED_CATEGORIES:
                allowed = ALLOWED_CATEGORIES[column]

                if not number.is_integer() or int(number) not in allowed:
                    raise PredictionError(
                        f"Feature '{column}' must be one of "
                        f"{sorted(allowed)}."
                    )

            if column in NUMERIC_BOUNDS:
                minimum, maximum = NUMERIC_BOUNDS[column]

                if not minimum <= number <= maximum:
                    raise PredictionError(
                        f"Feature '{column}' must be between "
                        f"{minimum} and {maximum}."
                    )

            validated[column] = number

        return validated

    def predict(
        self,
        features: dict[str, Any],
    ) -> dict[str, Any]:
        validated = self.validate_features(features)

        sample = pd.DataFrame(
            [validated],
            columns=FEATURE_COLUMNS,
        )

        prediction = int(self.model.predict(sample)[0])

        classes = list(self.model.classes_)
        if prediction not in (0, 1):
            raise RuntimeError(
                f"Unexpected model prediction: {prediction}"
            )

        positive_index = classes.index(1)
        probabilities = self.model.predict_proba(sample)[0]
        probability = float(probabilities[positive_index])

        return {
            "prediction": prediction,
            "label": "presence" if prediction == 1 else "absence",
            "probability_presence": probability,
        }
