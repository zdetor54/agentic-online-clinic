"""CRUD operations for patient management."""

from loguru import logger

from ..database import get_connection
from .schemas import PatientCreate, PatientResponse


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


def list_patients(
    name: str | None = None, phone: str | None = None
) -> list[PatientResponse]:
    """Fetch all patients."""
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = []
    query_params = []

    if phone:
        where_clauses.append("phone LIKE ?")
        query_params.append(f"%{phone}%")

    if name:
        name_parts = [w.strip() for w in name.split() if w.strip()]
        for part in name_parts:
            where_clauses.append(
                "(lower(first_name) LIKE ? OR lower(last_name) LIKE ?)"
            )
            query_params.extend([f"%{part.lower()}%", f"%{part.lower()}%"])

    where_statement = ""
    if where_clauses:
        where_statement = "WHERE " + " AND ".join(where_clauses)

    _sql = f"SELECT * FROM patients {where_statement}"
    logger.info(f"list_patients SQL: {_sql} with params {query_params}")

    cursor.execute(_sql, query_params)
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

    # Exclude created_by from updates to preserve original creator
    data.pop("created_by", None)

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
