"""API route handlers for patient management."""

from typing import Never

from fastapi import APIRouter, HTTPException, status

from .crud import (
    create_appointment,
    delete_appointment,
    get_appointment_by_id,
    list_appointments,
    update_appointment,
)
from .schemas import AppointmentCreate, AppointmentResponse

appointment_router = APIRouter(prefix="/appointments", tags=["appointments"])


@appointment_router.get("/{appointment_id}", summary="Get appointment by ID")
def get_appointment_endpoint(appointment_id: int) -> AppointmentResponse:
    """
    Retrieve a single appointment by ID.
    Args:
        appointment_id: The ID of the appointment to retrieve
    Returns:
        AppointmentResponse object
    Raises:
        HTTPException: 404 if not found
    """
    appointment = get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )
    return appointment


@appointment_router.get("/", summary="List/search appointments")
def list_appointments_endpoint(
    appointment_date: str | None = None, patient_id: int | None = None
) -> list[AppointmentResponse]:
    """
    List or search appointments by date and/or patient ID.
    Args:
        appointment_date: Optional appointment date to filter
        patient_id: Optional patient ID to filter
    Returns:
        List of matching AppointmentResponse objects
    """
    return list_appointments(appointment_date=appointment_date, patient_id=patient_id)


@appointment_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new appointment",
    description="Create a new appointment record with validation",
)
def create_appointment_endpoint(
    appointment: AppointmentCreate,
) -> AppointmentResponse | None:
    """
    Create a new appointment.

    Args:
        appointment: Appointment data validated against AppointmentCreate schema

    Returns:
        AppointmentResponse: The created appointment with generated ID and timestamps

    Raises:
        HTTPException: 400 if validation fails, 500 if database operation fails
    """

    def _raise_appointment_not_retrieved() -> Never:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Appointment created but could not be retrieved",
        )

    try:
        appointment_id = create_appointment(appointment)
        # Fetch the created appointment to return complete data
        created_appointment = get_appointment_by_id(appointment_id)
        if not created_appointment:
            _raise_appointment_not_retrieved()
        return created_appointment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {e!s}",
        ) from e


@appointment_router.put(
    "/{appointment_id}",
    summary="Update an appointment",
    description="Update an existing appointment record",
)
def update_appointment_endpoint(
    appointment_id: int, appointment: AppointmentCreate
) -> AppointmentResponse:
    """
    Update an existing appointment.

    Args:
        appointment_id: The ID of the appointment to update
        appointment: Updated appointment data validated against AppointmentCreate schema

    Returns:
        AppointmentResponse: The updated appointment with timestamps

    Raises:
        HTTPException: 404 if appointment not found, 400 if validation fails
    """
    try:
        # Check if appointment exists
        existing_appointment = get_appointment_by_id(appointment_id)
        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found",
            )

        # Update the appointment
        updated_by = "streamlit_user"  # Could be passed from UI or auth context
        success = update_appointment(appointment_id, appointment, updated_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update appointment",
            )

        # Fetch and return updated appointment
        updated_appointment = get_appointment_by_id(appointment_id)
        if not updated_appointment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Appointment updated but could not be retrieved",
            )
        return updated_appointment

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


# --- DELETE endpoint ---
@appointment_router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an appointment",
    description="Delete an appointment by ID. Returns 204 if successful, 404 if not found.",
)
def delete_appointment_endpoint(appointment_id: int) -> None:
    """
    Delete an appointment by ID.

    Args:
        appointment_id: The ID of the appointment to delete

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if not found, 500 if deletion fails
    """

    # Check if appointment exists
    appointment = get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found",
        )
    try:
        success = delete_appointment(appointment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete appointment",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appointment: {e!s}",
        ) from e
