"""Orchestrates CSV -> preprocessing -> prediction -> MongoDB."""
import io
from datetime import datetime, timezone
import pandas as pd
from fastapi import HTTPException, status
from app.database import get_database
from ml_service.preprocessing import preprocess_dataframe
from ml_service.prediction_service import predict_windows
from ml_service.explainability_service import explain_window
from ml_service.model_loader import get_config

def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File could not be read as CSV")


async def run_analysis(file_bytes: bytes, filename: str,patient: dict, doctor_id) -> dict:
    """Full pipeline for one uploaded CSV."""
    df = _read_csv(file_bytes)

    try:
        windows = preprocess_dataframe(df)
    except ValueError as e:
        # Channel/shape problems are the user's mistake -> 400 with a clear message
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    prediction = predict_windows(windows)

    # --- Integrated Gradients on the highest-risk window ---
    cfg = get_config()
    target_class = 1 if prediction["predictedClass"] == cfg["class_names"][1] else 0
    explainability = explain_window(
        windows[prediction["worstWindowIndex"]], target_class
    )

    db = get_database()
    doc = {
        "doctorId": doctor_id,
        "patientId": patient["_id"],
        "csvFileName": filename,
        "windowsAnalysed": prediction["windowsAnalysed"],
        "prediction": {
            "predictedClass": prediction["predictedClass"],
            "status": prediction["status"],
            "probability": prediction["probability"],
            "confidence": prediction["confidence"],
            "threshold": prediction["threshold"],
        },
        "explainability": explainability,
        "windowProbabilities": prediction["windowProbabilities"],
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db.analyses.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "patientId": str(patient["_id"]),
        "patientName": patient["name"],
        "csvFileName": filename,
        "windowsAnalysed": doc["windowsAnalysed"],
        "prediction": doc["prediction"],
         "explainability": explainability,
        "createdAt": doc["createdAt"].isoformat(),
    }