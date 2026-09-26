"""Authentication endpoints: signup, login, Google login, profile."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.google import verify_google_token
from app.auth.dependencies import get_current_doctor
from app.schemas.auth import (
    SignupRequest, LoginRequest, GoogleLoginRequest,
    TokenResponse, DoctorResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _doctor_response(doctor: dict) -> DoctorResponse:
    return DoctorResponse(
        id=str(doctor["_id"]),
        name=doctor["name"],
        email=doctor["email"],
        specialty=doctor.get("specialty", "Neurology"),
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest):
    db = get_database()

    if await db.doctors.find_one({"email": data.email}):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    now = datetime.now(timezone.utc)
    doctor = {
        "name": data.name,
        "email": data.email,
        "passwordHash": hash_password(data.password),
        "googleId": None,
        "authProvider": "local",
        "specialty": data.specialty,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.doctors.insert_one(doctor)
    doctor["_id"] = result.inserted_id

    token = create_access_token(str(doctor["_id"]))
    return TokenResponse(access_token=token, doctor=_doctor_response(doctor))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    db = get_database()

    doctor = await db.doctors.find_one({"email": data.email})
    # Same error whether the email is unknown or the password is wrong —
    # never reveal which one, to avoid leaking valid emails.
    if not doctor or not doctor.get("passwordHash") \
            or not verify_password(data.password, doctor["passwordHash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token(str(doctor["_id"]))
    return TokenResponse(access_token=token, doctor=_doctor_response(doctor))


@router.post("/google", response_model=TokenResponse)
async def google_login(data: GoogleLoginRequest):
    db = get_database()

    info = verify_google_token(data.credential)
    if info is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token")

    # Find by Google ID, then by email (links a Google login to an existing
    # email account), otherwise create a new doctor.
    doctor = await db.doctors.find_one({"googleId": info["googleId"]}) \
        or await db.doctors.find_one({"email": info["email"]})

    if doctor is None:
        now = datetime.now(timezone.utc)
        doctor = {
            "name": info["name"],
            "email": info["email"],
            "passwordHash": None,
            "googleId": info["googleId"],
            "authProvider": "google",
            "specialty": "Neurology",
            "createdAt": now,
            "updatedAt": now,
        }
        result = await db.doctors.insert_one(doctor)
        doctor["_id"] = result.inserted_id
    elif not doctor.get("googleId"):
        await db.doctors.update_one(
            {"_id": doctor["_id"]}, {"$set": {"googleId": info["googleId"]}}
        )

    token = create_access_token(str(doctor["_id"]))
    return TokenResponse(access_token=token, doctor=_doctor_response(doctor))


@router.get("/me", response_model=DoctorResponse)
async def get_me(doctor: dict = Depends(get_current_doctor)):
    return _doctor_response(doctor)