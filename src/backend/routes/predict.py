from functools import lru_cache

from fastapi import APIRouter, HTTPException

from src.backend.schemas import PredictionRequest, PredictionResponse
from src.ml.predict import HeartDiseasePredictor, PredictionError

router = APIRouter(tags=["prediction"])


@lru_cache(maxsize=1)
def get_predictor() -> HeartDiseasePredictor:
    return HeartDiseasePredictor()


@router.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    try:
        result = get_predictor().predict(request.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Model prediksi belum tersedia. Jalankan proses training model.",
        ) from exc
    except PredictionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PredictionResponse(**result)
