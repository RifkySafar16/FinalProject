from fastapi.testclient import TestClient

from src.backend import main
from src.backend.routes import predict


client = TestClient(main.app)
VALID_FEATURES = {
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


def test_predict_returns_rule_based_result():
    response = client.post(
        "/predict",
        json=VALID_FEATURES,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert "score" in result
    assert "factors" in result
    assert "diagnosis" not in result


def test_predict_rejects_missing_and_extra_features():
    response = client.post("/predict", json={"age": 55, "extra": 1})

    assert response.status_code == 422


def test_predict_rejects_extreme_resting_blood_pressure():
    features = {**VALID_FEATURES, "age": 70, "trestbps": 400}

    response = client.post("/predict", json=features)

    assert response.status_code == 422
    assert "trestbps" in response.json()["detail"]


def test_predict_does_not_return_moderate_when_scoring_fails(monkeypatch):
    def fail_scoring(_):
        raise RuntimeError("scoring failure")

    monkeypatch.setattr(predict, "classify_heart_disease_risk", fail_scoring)
    error_client = TestClient(main.app, raise_server_exceptions=False)

    response = error_client.post("/predict", json=VALID_FEATURES)

    assert response.status_code == 500
    assert "moderate" not in response.text


def test_openapi_contains_chat_and_predict_routes():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/chat" in response.json()["paths"]
    assert "/predict" in response.json()["paths"]
