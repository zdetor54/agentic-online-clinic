"""FastAPI main application."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from .agent_routes import agent_router
from .patients.routes import patient_router

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI(
    title="Patient Management API",
    description="API for managing patient records in an online clinic",
    version="1.0.0",
)

# Include routers
app.include_router(patient_router)
app.include_router(agent_router)


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "Patient Management API", "status": "healthy"}
