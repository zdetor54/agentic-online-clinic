from datetime import date

from loguru import logger

from src.api.patients.crud import (
    create_patient,
    delete_patient,
    get_patient_by_id,
    list_patients,
)
from src.api.patients.schemas import PatientCreate

# Create a sample patient
patient = PatientCreate(
    first_name="Zacharias",
    last_name="Detorakis",
    date_of_birth=date(1990, 1, 1),
    gender="Male",
    phone="1234567890",
    email="zacharias.detorakis@example.com",
    address="123 Main St",
    created_by="admin",
)

new_id = create_patient(patient)
logger.success(f"Inserted patient with ID: {new_id}")
patient = get_patient_by_id(new_id)
logger.info(f"Fetched patient: {patient}")

patients = list_patients()
logger.success(f"Total patients in database: {len(patients)}")

delete_patient(new_id)
logger.success(f"Deleted patient with ID: {new_id}")
patients = list_patients()
logger.info(f"Total patients in database: {len(patients)}")
# logger.info("All patients:")
# for p in patients:
#     logger.info(p)
