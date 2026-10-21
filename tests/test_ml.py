    
import pytest

from src.ml.predict import (
    HeartDiseasePredictor,
    PredictionError,
)


@pytest.fixture
def predictor():
    return HeartDiseasePredictor("models/heart_model.pkl")


@pytest.fixture
def valid_features():
    return {
        "age": 55,
        "sex": 1,
        "cp": 4,
        "trestbps": 130,
        "chol": 250,
        "fbs": 0,
        "restecg": 1,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 1.0,
        "slope": 2,
        "ca": 0,
        "thal": 3,
    }


def test_model_predicts(predictor, valid_features):
    result = predictor.predict(valid_features)

    assert result["prediction"] in (0, 1)
    assert result["label"] in ("absence", "presence")
    assert 0.0 <= result["probability_presence"] <= 1.0


def test_missing_feature_rejected(predictor, valid_features):
    valid_features.pop("age")

    with pytest.raises(PredictionError, match="Missing features"):
        predictor.predict(valid_features)


def test_invalid_category_rejected(predictor, valid_features):
    valid_features["cp"] = 0

    with pytest.raises(PredictionError, match="Feature 'cp'"):
        predictor.predict(valid_features)


def test_non_finite_value_rejected(predictor, valid_features):
    valid_features["chol"] = float("nan")

    with pytest.raises(PredictionError, match="must be finite"):
        predictor.predict(valid_features)


def test_extra_feature_rejected(predictor, valid_features):
    valid_features["extra_feature"] = 123

    with pytest.raises(PredictionError, match="Unexpected features"):
        predictor.predict(valid_features)


def test_boolean_value_rejected(predictor, valid_features):
    valid_features["age"] = True

    with pytest.raises(PredictionError):
        predictor.predict(valid_features)


def test_out_of_range_value_rejected(predictor, valid_features):
    valid_features["age"] = 150

    with pytest.raises(PredictionError):
        predictor.predict(valid_features)


def test_non_integer_category_rejected(predictor, valid_features):
    valid_features["cp"] = 2.5

    with pytest.raises(PredictionError):
        predictor.predict(valid_features)


def test_missing_model_file_rejected(tmp_path):
    missing_model = tmp_path / "missing_model.pkl"

    with pytest.raises(FileNotFoundError):
        HeartDiseasePredictor(missing_model)
