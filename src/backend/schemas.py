from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        question = value.strip()
        if len(question) < 3:
            raise ValueError("Pertanyaan harus memiliki minimal 3 karakter.")
        return question


class ChatSource(BaseModel):
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: float
    sex: float
    cp: float
    trestbps: float
    chol: float
    fbs: float
    restecg: float
    thalach: float
    exang: float
    oldpeak: float
    slope: float
    ca: float
    thal: float

    @field_validator("*", mode="before")
    @classmethod
    def reject_boolean_features(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("Fitur harus berupa angka, bukan boolean.")
        return value


class PredictionResponse(BaseModel):
    prediction: Literal[0, 1]
    label: Literal["absence", "presence"]
    probability_presence: float


class RiskFactorResponse(BaseModel):
    feature: str
    value: float
    points: int
    reason: str


class RiskPredictionResponse(BaseModel):
    risk_level: Literal["low", "moderate", "high"]
    score: int
    max_score: int
    factors: list[RiskFactorResponse]
    disclaimer: str
