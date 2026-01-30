"""API route handlers for patient management."""

from typing import Never

from fastapi import APIRouter, HTTPException, status

from .crud import create_patient, get_patient_by_id, update_patient
from .schemas import PatientCreate, PatientResponse

patient_router = APIRouter(prefix="/patients", tags=["patients"])


@patient_router.get("/{patient_id}", summary="Get patient by ID")
def get_patient_endpoint(patient_id: int) -> PatientResponse:
    """
    Retrieve a single patient by ID.
    Args:
        patient_id: The ID of the patient to retrieve
    Returns:
        PatientResponse object
    Raises:
        HTTPException: 404 if not found
    """
    from .crud import get_patient_by_id

    patient = get_patient_by_id(patient_id)
    if not patient:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )
    return patient


@patient_router.get("/", summary="List/search patients")
def list_patients_endpoint(
    name: str | None = None, phone: str | None = None
) -> list[PatientResponse]:
    """
    List or search patients by name and/or phone.
    Args:
        name: Optional name substring to search (matches first or last name)
        phone: Optional phone substring to search
    Returns:
        List of matching PatientResponse objects
    """
    from .crud import list_patients

    all_patients = list_patients()

    def matches(patient: PatientResponse) -> bool:
        name_match = (
            not name
            or name.lower() in patient.first_name.lower()
            or name.lower() in patient.last_name.lower()
        )
        phone_match = not phone or (patient.phone and phone in patient.phone)
        return bool(name_match) and bool(phone_match)

    return [p for p in all_patients if matches(p)]


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


@patient_router.put(
    "/{patient_id}",
    summary="Update a patient",
    description="Update an existing patient record",
)
def update_patient_endpoint(patient_id: int, patient: PatientCreate) -> PatientResponse:
    """
    Update an existing patient.

    Args:
        patient_id: The ID of the patient to update
        patient: Updated patient data validated against PatientCreate schema

    Returns:
        PatientResponse: The updated patient with timestamps

    Raises:
        HTTPException: 404 if patient not found, 400 if validation fails
    """
    try:
        # Check if patient exists
        existing_patient = get_patient_by_id(patient_id)
        if not existing_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found",
            )

        # Update the patient
        updated_by = "streamlit_user"  # Could be passed from UI or auth context
        success = update_patient(patient_id, patient, updated_by)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update patient",
            )

        # Fetch and return updated patient
        updated_patient = get_patient_by_id(patient_id)
        if not updated_patient:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Patient updated but could not be retrieved",
            )
        return updated_patient

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient: {e!s}",
        ) from e
