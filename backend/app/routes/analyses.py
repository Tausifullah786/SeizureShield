"""Analysis endpoints: upload a CSV, list history, fetch one result."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.database import get_database
from app.auth.dependencies import get_current_doctor
from app.services.patient_service import get_owned_patient
from app.services.analysis_service import run_analysis
from app.schemas.analysis import AnalysisResponse
from ml_service.model_loader import get_config

router = APIRouter(prefix="/api", tags=["analyses"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024      # 20 MB


@router.post("/patients/{patient_id}/analyses", response_model=AnalysisResponse)
async def upload_analysis(
    patient_id: str,
    file: UploadFile = File(...),
    doctor: dict = Depends(get_current_doctor),
):
    # Ownership check first — a doctor can only upload for their own patient
    patient = await get_owned_patient(patient_id, doctor["_id"])

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be a .csv")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File too large (max 20 MB)")

    return await run_analysis(content, file.filename, patient, doctor["_id"])


@router.get("/analyses")
async def list_analyses(
    patient_id: str | None = None,
    limit: int = 50,
    doctor: dict = Depends(get_current_doctor),
):
    db = get_database()
    query = {"doctorId": doctor["_id"]}

    if patient_id:
        await get_owned_patient(patient_id, doctor["_id"])   # ownership check
        query["patientId"] = ObjectId(patient_id)

    cursor = db.analyses.find(query).sort("createdAt", -1).limit(limit)

    results = []
    async for a in cursor:
        patient = await db.patients.find_one({"_id": a["patientId"]})
        results.append({
            "id": str(a["_id"]),
            "patientId": str(a["patientId"]),
            "patientName": patient["name"] if patient else "Unknown",
            "csvFileName": a["csvFileName"],
            "windowsAnalysed": a.get("windowsAnalysed", 1),
            "prediction": a["prediction"],
            "createdAt": a["createdAt"].isoformat(),
        })
    return results


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    doctor: dict = Depends(get_current_doctor),
):
    db = get_database()
    try:
        oid = ObjectId(analysis_id)
    except InvalidId:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")

    a = await db.analyses.find_one({"_id": oid, "doctorId": doctor["_id"]})
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")

    patient = await db.patients.find_one({"_id": a["patientId"]})
    a["id"] = str(a.pop("_id"))
    a["doctorId"] = str(a["doctorId"])
    a["patientId"] = str(a["patientId"])
    a["patientName"] = patient["name"] if patient else "Unknown"
    a["createdAt"] = a["createdAt"].isoformat()
    return a


@router.get("/model/info")
async def model_info():
    """Architecture and test metrics, for display in the UI."""
    cfg = get_config()
    return {
        "architecture": cfg["architecture"],
        "timesteps": cfg["timesteps"],
        "windowSize": cfg["window_size"],
        "samplingRate": cfg["fs"],
        "threshold": cfg["threshold"],
        "classNames": cfg["class_names"],
        "testMetrics": cfg["test_metrics"],
    }