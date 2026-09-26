"""The authentication guard used by every protected route."""

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.security import decode_access_token
from app.database import get_database


bearer_scheme = HTTPBearer()

async def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Returns the logged-in doctor's document.
    The route then uses doctor['_id'] to filter its database queries.
    """
    token = credentials.credentials
    doctor_id = decode_access_token(token)

    if doctor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    db = get_database()
    doctor = await db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor not found",
        )

    return doctor