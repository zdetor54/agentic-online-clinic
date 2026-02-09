"""Pydantic schemas for patient request/response validation."""

from datetime import date, datetime

from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_date: date
    appointment_start_time: str | None = None
    appointment_end_time: str | None = None
    appointment_reason: str | None = None
    created_by: str | None = None


class AppointmentResponse(AppointmentCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    updated_by: str | None = None
