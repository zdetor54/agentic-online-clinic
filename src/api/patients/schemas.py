"""Pydantic schemas for patient request/response validation."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, strip_whitespace=True)
    last_name: str = Field(..., min_length=1, strip_whitespace=True)
    date_of_birth: date
    gender: Literal["Male", "Female", "Other"]
    phone: str | None = Field(
        default=None, min_length=7, max_length=20, strip_whitespace=True
    )
    email: EmailStr | None = None
    address: str | None = None
    created_by: str | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, v: date) -> date:
        if v > datetime.now().date():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: str | None) -> str | None:
        return validate_phone_number(cls, v)


class PatientResponse(PatientCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    updated_by: str | None = None


def validate_phone_number(_ls: object, v: str | None) -> str | None:
    """Generic phone number validator: allows digits, spaces, dashes, parentheses, and plus sign."""
    if v is None:
        return v
    pattern = re.compile(r"^[\d\s\-\+\(\)]+$")
    if not pattern.match(v):
        raise ValueError("Phone number contains invalid characters")
    return v
