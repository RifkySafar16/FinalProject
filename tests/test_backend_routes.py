from fastapi.testclient import TestClient

from src.backend import main
from src.backend.routes import predict


client = TestClient(main.app)


def test_predict_returns_model_result(monkeypatch):
    class FakePredictor:
        def predict(self, features):
            assert features["age"] == 55
            return {
                "prediction": 1,
                "label": "presence",
                "probability_presence": 0.75,
            }

    monkeypatch.setattr(predict, "get_predictor", lambda: FakePredictor())

    response = client.post(
        "/predict",
        json={
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
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "prediction": 1,
        "label": "presence",
        "probability_presence": 0.75,
    }


def test_predict_returns_service_unavailable_without_model(monkeypatch):
    def missing_model():
        raise FileNotFoundError("model missing")

    monkeypatch.setattr(predict, "get_predictor", missing_model)

    response = client.post(
        "/predict",
        json={
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
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Model prediksi belum tersedia. Jalankan proses training model."
    )


def test_predict_rejects_missing_and_extra_features():
    response = client.post("/predict", json={"age": 55, "extra": 1})

    assert response.status_code == 422


def test_openapi_contains_chat_and_predict_routes():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/chat" in response.json()["paths"]
    assert "/predict" in response.json()["paths"]
