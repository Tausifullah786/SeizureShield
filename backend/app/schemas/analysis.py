"""Response shapes for analyses."""

from pydantic import BaseModel


class PredictionOut(BaseModel):
    predictedClass: str
    status: str
    probability: float
    confidence: float
    threshold: float


class AnalysisResponse(BaseModel):
    id: str
    patientId: str
    patientName: str
    csvFileName: str
    windowsAnalysed: int
    prediction: PredictionOut
    explainability: dict
    createdAt: str