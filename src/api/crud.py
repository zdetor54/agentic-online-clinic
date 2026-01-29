"""CRUD operations for patient management."""

from .database import get_connection
from .models import PatientCreate, PatientResponse


def create_patient(patient: PatientCreate) -> int:
    """Insert a new patient and return the new patient ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all fields from the model as a dictionary
    data = patient.model_dump(exclude_none=False)

    # Handle date serialization
    if data.get("date_of_birth"):
        data["date_of_birth"] = data["date_of_birth"].isoformat()

    # Dynamically build SQL from dictionary keys
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())

    cursor.execute(
        f"INSERT INTO patients ({columns}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    if new_id is None:
        raise RuntimeError("Failed to insert patient")
    return new_id


def get_patient_by_id(patient_id: int) -> PatientResponse | None:
    """Fetch a patient by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # Convert sqlite3.Row to dict, then to PatientResponse
        return PatientResponse(**dict(row))  # type: ignore[arg-type]
    return None


def list_patients() -> list[PatientResponse]:
    """Fetch all patients."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
    rows = cursor.fetchall()
    conn.close()
    return [PatientResponse(**dict(row)) for row in rows]  # type: ignore[arg-type]


def update_patient(patient_id: int, patient: PatientCreate, updated_by: str) -> bool:
    """Update a patient record. Returns True if updated, False if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    data = patient.model_dump(exclude_none=False)
    data["date_of_birth"] = (
        data["date_of_birth"].isoformat() if data["date_of_birth"] else None
    )
    data["updated_by"] = updated_by

    set_clause = ", ".join(
        [f"{k} = ?" for k in data] + ["updated_at = CURRENT_TIMESTAMP"]
    )
    values = [*list(data.values()), patient_id]

    cursor.execute(
        f"UPDATE patients SET {set_clause} WHERE id = ?",
        values,
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_patient(patient_id: int) -> bool:
    """Delete a patient by ID. Returns True if deleted, False if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
