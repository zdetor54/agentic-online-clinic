"""CRUD operations for patient management."""

from loguru import logger

from ..database import get_connection
from .schemas import AppointmentCreate, AppointmentResponse


def create_appointment(appointment: AppointmentCreate) -> int:
    """Insert a new appointment and return the new appointment ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all fields from the model as a dictionary
    data = appointment.model_dump(exclude_none=False)

    # Handle date serialization
    if data.get("appointment_date"):
        data["appointment_date"] = data["appointment_date"].isoformat()
    # Dynamically build SQL from dictionary keys
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())

    cursor.execute(
        f"INSERT INTO appointments ({columns}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    if new_id is None:
        raise RuntimeError("Failed to insert appointment")
    return new_id


def get_appointment_by_id(appointment_id: int) -> AppointmentResponse | None:
    """Fetch an appointment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # Convert sqlite3.Row to dict, then to AppointmentResponse
        return AppointmentResponse(**dict(row))  # type: ignore[arg-type]
    return None


def list_appointments(
    appointment_date: str | None = None,
    patient_id: int | None = None,
) -> list[AppointmentResponse]:
    """Fetch all appointments."""
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = []
    query_params = []

    if appointment_date:
        where_clauses.append("appointment_date = ?")
        query_params.append(appointment_date)

    if patient_id:
        where_clauses.append("patient_id = ?")
        query_params.append(patient_id)

    where_statement = ""
    if where_clauses:
        where_statement = "WHERE " + " AND ".join(where_clauses)

    _sql = f"SELECT * FROM appointments {where_statement}"
    logger.info(f"list_appointments SQL: {_sql} with params {query_params}")

    cursor.execute(_sql, query_params)
    rows = cursor.fetchall()
    conn.close()
    return [AppointmentResponse(**dict(row)) for row in rows]  # type: ignore[arg-type]


def update_appointment(
    appointment_id: int, appointment: AppointmentCreate, updated_by: str
) -> bool:
    """Update an appointment record. Returns True if updated, False if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    data = appointment.model_dump(exclude_none=False)
    data["appointment_date"] = (
        data["appointment_date"].isoformat() if data["appointment_date"] else None
    )
    data["updated_by"] = updated_by

    # Exclude created_by from updates to preserve original creator
    data.pop("created_by", None)

    set_clause = ", ".join(
        [f"{k} = ?" for k in data] + ["updated_at = CURRENT_TIMESTAMP"]
    )
    values = [*list(data.values()), appointment_id]

    cursor.execute(
        f"UPDATE appointments SET {set_clause} WHERE id = ?",
        values,
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_appointment(appointment_id: int) -> bool:
    """Delete an appointment by ID. Returns True if deleted, False if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
