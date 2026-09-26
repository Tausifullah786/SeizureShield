"""SeizureShield — FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from app.routes import auth
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import auth, patients
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, patients, analyses
from ml_service.model_loader import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once at startup 
    await connect_to_mongo()
    load_model()          # loads the BiLSTM once, into memory
    yield
    #  runs once at shutdown 
    await close_mongo_connection()


app = FastAPI(
    title="SeizureShield API",
    description="EEG seizure prediction with explainable AI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health")
async def health_check():
    """Quick way to confirm the server is alive."""
    return {"status": "ok", "service": "SeizureShield"}

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(analyses.router)
# Serve the frontend from the same origin as the API.
# This avoids CORS configuration entirely and lets Google OAuth work.
# Serve the frontend from the same origin as the API.
# Search upward so this works regardless of where main.py sits.
_here = Path(__file__).resolve()
FRONTEND_DIR = next(
    (p / "frontend" for p in _here.parents if (p / "frontend").is_dir()),
    None,
)

if FRONTEND_DIR:
    print(f"Serving frontend from: {FRONTEND_DIR}")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print("WARNING: frontend directory not found — static files not served")