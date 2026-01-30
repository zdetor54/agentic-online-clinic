"""API route handlers for patient management."""

from typing import Never

from fastapi import APIRouter, HTTPException, status

from .crud import create_patient, get_patient_by_id
from .schemas import PatientCreate, PatientResponse

patient_router = APIRouter(prefix="/patients", tags=["patients"])


@patient_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient",
    description="Create a new patient record with validation",
)
def create_patient_endpoint(patient: PatientCreate) -> PatientResponse | None:
    """
    Create a new patient.

    Args:
        patient: Patient data validated against PatientCreate schema

    Returns:
        PatientResponse: The created patient with generated ID and timestamps

    Raises:
        HTTPException: 400 if validation fails, 500 if database operation fails
    """

    def _raise_patient_not_retrieved() -> Never:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient created but could not be retrieved",
        )

    try:
        patient_id = create_patient(patient)
        # Fetch the created patient to return complete data
        created_patient = get_patient_by_id(patient_id)
        if not created_patient:
            _raise_patient_not_retrieved()
        return created_patient
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {e!s}",
        ) from e
