"""Dependency containers for PydanticAI agents.

Each agent gets a frozen dataclass that holds its external dependencies
(CRUD operations, request tracking, etc.). These are passed to agents via
`deps_type` and accessed in tools through `ctx.deps`.
"""

from dataclasses import dataclass
from typing import Protocol

from src.api.appointments.schemas import AppointmentCreate, AppointmentResponse
from src.api.patients.schemas import PatientCreate, PatientResponse


# ---------------------------------------------------------------------------
# Patient CRUD protocol
# ---------------------------------------------------------------------------
class PatientCrudProtocol(Protocol):
    """Interface that any patient data layer must implement."""

    def create_patient(self, patient: PatientCreate) -> int: ...

    def get_patient_by_id(self, patient_id: int) -> PatientResponse | None: ...

    def list_patients(
        self,
        name: str | None = None,
        phone: str | None = None,
    ) -> list[PatientResponse]: ...

    def update_patient(
        self,
        patient_id: int,
        patient: PatientCreate,
        updated_by: str,
    ) -> bool: ...


# ---------------------------------------------------------------------------
# Appointment CRUD protocol
# ---------------------------------------------------------------------------
class AppointmentCrudProtocol(Protocol):
    """Interface that any appointment data layer must implement."""

    def create_appointment(self, appointment: AppointmentCreate) -> int: ...

    def get_appointment_by_id(
        self, appointment_id: int
    ) -> AppointmentResponse | None: ...

    def list_appointments(
        self,
        appointment_date: str | None = None,
        patient_id: int | None = None,
    ) -> list[AppointmentResponse]: ...

    def update_appointment(
        self,
        appointment_id: int,
        appointment: AppointmentCreate,
        updated_by: str,
    ) -> bool: ...


# ---------------------------------------------------------------------------
# Agent dependency containers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PatientDeps:
    """Dependencies injected into the patient agent's tools."""

    crud: PatientCrudProtocol
    request_id: str | None = None


@dataclass(frozen=True)
class AppointmentDeps:
    """Dependencies injected into the appointment agent's tools."""

    crud: AppointmentCrudProtocol
    request_id: str | None = None


@dataclass(frozen=True)
class OrchestratorDeps:
    """Dependencies injected into the orchestrator agent's tools.

    Holds references to sub-agent processor callables so the orchestrator
    doesn't import concrete agent modules at the top level.
    """

    patient_deps: PatientDeps
    appointment_deps: AppointmentDeps
    request_id: str | None = None


# ---------------------------------------------------------------------------
# Default CRUD adapters (wrap the module-level functions as object methods)
# ---------------------------------------------------------------------------
class _PatientCrudAdapter:
    """Adapts the patients CRUD module functions to the PatientCrudProtocol."""

    def __init__(self) -> None:
        from src.api.patients import crud

        self._crud = crud

    def create_patient(self, patient: PatientCreate) -> int:
        return self._crud.create_patient(patient)

    def get_patient_by_id(self, patient_id: int) -> PatientResponse | None:
        return self._crud.get_patient_by_id(patient_id)

    def list_patients(
        self,
        name: str | None = None,
        phone: str | None = None,
    ) -> list[PatientResponse]:
        return self._crud.list_patients(name=name, phone=phone)

    def update_patient(
        self,
        patient_id: int,
        patient: PatientCreate,
        updated_by: str,
    ) -> bool:
        return self._crud.update_patient(patient_id, patient, updated_by)


class _AppointmentCrudAdapter:
    """Adapts the appointments CRUD module functions to the AppointmentCrudProtocol."""

    def __init__(self) -> None:
        from src.api.appointments import crud

        self._crud = crud

    def create_appointment(self, appointment: AppointmentCreate) -> int:
        return self._crud.create_appointment(appointment)

    def get_appointment_by_id(self, appointment_id: int) -> AppointmentResponse | None:
        return self._crud.get_appointment_by_id(appointment_id)

    def list_appointments(
        self,
        appointment_date: str | None = None,
        patient_id: int | None = None,
    ) -> list[AppointmentResponse]:
        return self._crud.list_appointments(
            appointment_date=appointment_date, patient_id=patient_id
        )

    def update_appointment(
        self,
        appointment_id: int,
        appointment: AppointmentCreate,
        updated_by: str,
    ) -> bool:
        return self._crud.update_appointment(appointment_id, appointment, updated_by)


def get_default_patient_deps(request_id: str | None = None) -> PatientDeps:
    """Create PatientDeps with the real SQLite CRUD adapter."""
    return PatientDeps(crud=_PatientCrudAdapter(), request_id=request_id)


def get_default_appointment_deps(request_id: str | None = None) -> AppointmentDeps:
    """Create AppointmentDeps with the real SQLite CRUD adapter."""
    return AppointmentDeps(crud=_AppointmentCrudAdapter(), request_id=request_id)


def get_default_orchestrator_deps(request_id: str | None = None) -> OrchestratorDeps:
    """Create OrchestratorDeps with real CRUD adapters for both sub-agents."""
    return OrchestratorDeps(
        patient_deps=get_default_patient_deps(request_id),
        appointment_deps=get_default_appointment_deps(request_id),
        request_id=request_id,
    )
