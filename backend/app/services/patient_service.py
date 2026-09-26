"""Patient database logic, with ownership always enforced."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from app.database import get_database


async def get_owned_patient(patient_id: str, doctor_id: ObjectId) -> dict:
    """
    Return the patient ONLY if it belongs to this doctor.
    Raises 404 otherwise — we never reveal that a patient exists
    but belongs to someone else.
    """
    db = get_database()
    try:
        oid = ObjectId(patient_id)
    except InvalidId:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")

    patient = await db.patients.find_one({"_id": oid, "doctorId": doctor_id})
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return patient


async def build_patient_response(patient: dict) -> dict:
    """Attach the latest analysis status and a count for the UI."""
    db = get_database()
    pid = patient["_id"]

    count = await db.analyses.count_documents({"patientId": pid})

    latest = await db.analyses.find_one(
        {"patientId": pid}, sort=[("createdAt", -1)]
    )
    status_text = latest["prediction"]["status"] if latest else "No analysis yet"

    return {
        "id": str(pid),
        "name": patient["name"],
        "age": patient["age"],
        "sex": patient["sex"],
        "city": patient["city"],
        "latestStatus": status_text,
        "analysesCount": count,
    }