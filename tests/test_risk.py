import pytest

from src.ml import risk
from src.ml.risk import (
    RiskInputError,
    classify_heart_disease_risk,
    score_risk_features,
    validate_risk_input,
)


@pytest.fixture
def low_risk_features():
    return {
        "age": 40,
        "sex": 0,
        "cp": 3,
        "trestbps": 110,
        "chol": 180,
        "fbs": 0,
        "restecg": 0,
        "thalach": 170,
        "exang": 0,
        "oldpeak": 0,
        "slope": 1,
        "ca": 0,
        "thal": 3,
    }


def test_low_risk_classification(low_risk_features):
    result = classify_heart_disease_risk(low_risk_features)

    assert result["risk_level"] == "low"
    assert result["score"] <= 7


def test_moderate_risk_classification(low_risk_features):
    features = {
        **low_risk_features,
        "age": 60,
        "sex": 1,
        "cp": 2,
        "trestbps": 125,
        "chol": 210,
        "oldpeak": 0.5,
    }

    result = classify_heart_disease_risk(features)

    assert result["risk_level"] == "moderate"
    assert 8 <= result["score"] <= 17


def test_high_risk_classification_from_multiple_risk_features(low_risk_features):
    features = {
        **low_risk_features,
        "age": 70,
        "sex": 1,
        "cp": 1,
        "trestbps": 180,
        "chol": 400,
        "fbs": 1,
        "restecg": 1,
        "thalach": 90,
        "exang": 1,
        "oldpeak": 2,
        "slope": 3,
        "ca": 3,
        "thal": 7,
    }

    result = classify_heart_disease_risk(features)

    assert result["risk_level"] == "high"
    assert result["score"] >= 18
    assert len(result["factors"]) >= 8


def test_three_categories_are_reachable(low_risk_features):
    examples = [
        low_risk_features,
        {
            **low_risk_features,
            "age": 60,
            "sex": 1,
            "cp": 2,
            "trestbps": 125,
            "chol": 210,
            "oldpeak": 0.5,
        },
        {
            **low_risk_features,
            "age": 70,
            "sex": 1,
            "cp": 1,
            "trestbps": 180,
            "chol": 400,
            "fbs": 1,
            "restecg": 1,
            "thalach": 90,
            "exang": 1,
            "oldpeak": 2,
            "slope": 3,
            "ca": 3,
            "thal": 7,
        },
    ]

    assert {
        classify_heart_disease_risk(example)["risk_level"]
        for example in examples
    } == {"low", "moderate", "high"}


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (10, "low"),
        (11, "moderate"),
        (22, "moderate"),
        (23, "high"),
    ],
)
def test_risk_classification_score_boundaries(
    monkeypatch, low_risk_features, score, expected_level
):
    monkeypatch.setattr(risk, "score_risk_features", lambda _: (score, []))

    result = classify_heart_disease_risk(low_risk_features)

    assert result["risk_level"] == expected_level
    assert result["score"] == score


def test_age_70_with_trestbps_400_is_invalid_not_scored(low_risk_features):
    features = {**low_risk_features, "age": 70, "trestbps": 400}

    with pytest.raises(RiskInputError, match="trestbps"):
        classify_heart_disease_risk(features)


def test_invalid_category_is_rejected(low_risk_features):
    features = {**low_risk_features, "cp": 5}

    with pytest.raises(RiskInputError, match="cp"):
        classify_heart_disease_risk(features)


def test_incomplete_input_is_rejected(low_risk_features):
    features = dict(low_risk_features)
    del features["age"]

    with pytest.raises(RiskInputError, match="age"):
        classify_heart_disease_risk(features)


def test_scoring_error_is_not_converted_to_moderate(monkeypatch, low_risk_features):
    def fail_scoring(_):
        raise RuntimeError("scoring failure")

    monkeypatch.setattr(risk, "score_risk_features", fail_scoring)

    with pytest.raises(RuntimeError, match="scoring failure"):
        classify_heart_disease_risk(low_risk_features)


def test_lower_risk_features_do_not_subtract_other_points(low_risk_features):
    validated = validate_risk_input(
        {
            **low_risk_features,
            "age": 70,
            "trestbps": 180,
            "cp": 1,
        }
    )
    score_with_risk = score_risk_features(validated)[0]
    lower_features = {
        **validated,
        "age": 40,
        "trestbps": 110,
        "cp": 3,
    }
    score_after_lowering_some_features = score_risk_features(lower_features)[0]

    assert score_with_risk > score_after_lowering_some_features
    assert score_after_lowering_some_features >= 0
