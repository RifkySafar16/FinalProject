from fastapi import APIRouter, HTTPException

from src.backend.schemas import PredictionRequest, RiskPredictionResponse
from src.ml.risk import RiskInputError, classify_heart_disease_risk

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=RiskPredictionResponse)
def predict_endpoint(request: PredictionRequest) -> RiskPredictionResponse:
    try:
        result = classify_heart_disease_risk(request.model_dump())
    except RiskInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskPredictionResponse(**result)
