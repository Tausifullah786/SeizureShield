"""Verify a Google ID token and extract the user's identity."""

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config import settings


def verify_google_token(credential: str) -> dict | None:
    """
    Returns {googleId, email, name} if the token is valid and meant for us,
    otherwise None.
    """
    if not settings.google_client_id:
        return None
    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.google_client_id,   # rejects tokens issued for other apps
        )
        return {
            "googleId": info["sub"],
            "email": info["email"],
            "name": info.get("name", info["email"].split("@")[0]),
        }
    except ValueError:
        return None