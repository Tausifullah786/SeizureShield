"""Patient CRUD endpoints. Every query is scoped to the logged-in doctor."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from app.database import get_database
from app.auth.dependencies import get_current_doctor
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.patient_service import get_owned_patient, build_patient_response

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    doctor: dict = Depends(get_current_doctor),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    patient = {
        "doctorId": doctor["_id"],          #  stamped from the token, not the client
        "name": data.name,
        "age": data.age,
        "sex": data.sex,
        "city": data.city,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.patients.insert_one(patient)
    patient["_id"] = result.inserted_id
    return await build_patient_response(patient)


@router.get("", response_model=list[PatientResponse])
async def list_patients(doctor: dict = Depends(get_current_doctor)):
    db = get_database()
    cursor = db.patients.find({"doctorId": doctor["_id"]}).sort("createdAt", -1)
    return [await build_patient_response(p) async for p in cursor]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    doctor: dict = Depends(get_current_doctor),
):
    patient = await get_owned_patient(patient_id, doctor["_id"])
    return await build_patient_response(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    doctor: dict = Depends(get_current_doctor),
):
    db = get_database()
    patient = await get_owned_patient(patient_id, doctor["_id"])  # ownership check

    await db.patients.update_one(
        {"_id": patient["_id"]},
        {"$set": {
            "name": data.name, "age": data.age, "sex": data.sex,
            "city": data.city, "updatedAt": datetime.now(timezone.utc),
        }},
    )
    patient = await get_owned_patient(patient_id, doctor["_id"])
    return await build_patient_response(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    doctor: dict = Depends(get_current_doctor),
):
    db = get_database()
    patient = await get_owned_patient(patient_id, doctor["_id"])  # ownership check

    # Delete the patient AND their analyses (cascade), so no orphans remain.
    await db.analyses.delete_many({"patientId": patient["_id"]})
    await db.patients.delete_one({"_id": patient["_id"]})
    return None