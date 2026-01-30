"""FastAPI main application."""

from fastapi import FastAPI

from .patients.routes import patient_router

app = FastAPI(
    title="Patient Management API",
    description="API for managing patient records in an online clinic",
    version="1.0.0",
)

# Include patient routes
app.include_router(patient_router)


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "Patient Management API", "status": "healthy"}
