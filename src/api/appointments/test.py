from datetime import date

from loguru import logger

from src.api.appointments.crud import (
    create_appointment,
    delete_appointment,
    get_appointment_by_id,
    list_appointments,
)
from src.api.appointments.schemas import AppointmentCreate

# Create a sample appointment
appointment = AppointmentCreate(
    patient_id=2,
    appointment_date=date(2026, 2, 11),
    appointment_start_time="11:00",
    appointment_end_time="11:30",
    appointment_reason="Routine check-up",
    created_by="admin",
)

new_id = create_appointment(appointment)
logger.success(f"Inserted appointment with ID: {new_id}")
appointment = get_appointment_by_id(new_id)
logger.info(f"Fetched appointment: {appointment}")

appointments = list_appointments()
logger.success(f"Total appointments in database: {len(appointments)}")

delete_appointment(new_id)
logger.success(f"Deleted appointment with ID: {new_id}")


appointments = list_appointments(appointment_date="2026-02-11")
logger.info(f"Total appointments in database: {len(appointments)}")
logger.info("All appointments:")
for a in appointments:
    logger.info(a)
