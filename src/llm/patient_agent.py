"""Agentic patient management orchestrator using PydanticAI and direct CRUD access."""

import os
import time
from datetime import datetime
from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from src.api.patients import crud
from src.api.patients.schemas import PatientCreate
from src.core.llm_logger import get_llm_logger


class PatientToolResult(BaseModel):
    """Result from patient tool operations."""

    success: bool
    message: str
    data: list[dict[str, Any]] = []


_patient_agent: Agent | None = None


def format_patient_info(patient: dict) -> str:
    info = (
        f"ID: {patient['id']}, Name: {patient['first_name']} {patient['last_name']}, "
        f"DOB: {patient.get('date_of_birth', 'N/A')}, Gender: {patient.get('gender', 'N/A')}"
    )
    if patient.get("phone"):
        info += f", Phone: {patient['phone']}"
    return info


def get_patient_agent(model_name: str | None = None) -> Agent:
    """
    Get or create the PydanticAI patient agent instance.
    Args:
        model_name: Optional model name override
                   If None, uses AZURE_OPENAI_DEPLOYMENT_NAME from .env
    Returns:
        Configured PydanticAI Agent with Azure OpenAI
    """
    global _patient_agent  # noqa: PLW0603
    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"
    )
    if _patient_agent is None:
        azure_provider = AzureProvider(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
        model = OpenAIChatModel(deployment_name, provider=azure_provider)
        _patient_agent = Agent(
            model,
            system_prompt="""You are a helpful medical office assistant that helps manage patient records.
You can:
1. Search for patients by name (first, last, or both) or phone number
2. View a specific patient's details by ID
3. Create new patient records
4. Update existing patient records
IMPORTANT SEARCH RULES:
- When the user provides both first and last name (e.g., \"Jane Smith\"), search using BOTH names if possible.
- If only one name is provided, search using that name (it may match either first or last name).
- The search API matches first name OR last name separately, but if both are provided, search for patients matching BOTH names.
- Example: For \"Jane Smith\", call search_patients with name=\"Jane Smith\" (or use both fields if supported).
Always use the patient ID from search results when you need to reference a specific patient.
Be clear and helpful in your responses.
Always include a link similar to http://localhost:8501/?patient_id= for every patient you reference even if you don't create or update, replacing the ID appropriately and don't include all the patient details again.
""",
        )
        _patient_agent.tool(search_patients)
        _patient_agent.tool(get_patient_by_id)
        _patient_agent.tool(create_patient)
        _patient_agent.tool(update_patient)
        logger.info(
            f"Initialized PydanticAI patient agent with Azure OpenAI: {deployment_name}"
        )
    return _patient_agent


async def search_patients(
    ctx: RunContext[None],  # noqa: ARG001
    name: str | None = None,
    phone: str | None = None,
) -> PatientToolResult:
    logger.info(f"Searching patients: name={name}, phone={phone}")
    try:
        patients = crud.list_patients(name=name, phone=phone)
        if patients:
            patient_list = [format_patient_info(p.model_dump()) for p in patients]
            return PatientToolResult(
                success=True,
                message=f"Found {len(patients)} patient(s):\n"
                + "\n".join(patient_list),
                data=[p.model_dump() for p in patients],
            )
        return PatientToolResult(
            success=True,
            message=f"No patients found with name='{name}' or phone='{phone}'",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}")


async def get_patient_by_id(
    ctx: RunContext[None],  # noqa: ARG001
    patient_id: int,
) -> PatientToolResult:
    logger.info(f"Fetching patient ID: {patient_id}")
    try:
        patient = crud.get_patient_by_id(patient_id)
        if patient:
            return PatientToolResult(
                success=True,
                message=format_patient_info(patient.model_dump()),
                data=[patient.model_dump()],
            )
        return PatientToolResult(
            success=True,
            message=f"No patient found with ID {patient_id}",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error fetching patient: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}", data=[])


async def create_patient(
    ctx: RunContext[None],  # noqa: ARG001
    first_name: str,
    last_name: str,
    date_of_birth: str,
    gender: str,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
) -> PatientToolResult:
    logger.info(f"Creating patient: {first_name} {last_name}")
    try:
        # Convert date_of_birth to date
        dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        # Validate gender
        gender_titled = gender.title()
        if gender_titled in ("Male", "Female", "Other"):
            gender_value: Literal["Male", "Female", "Other"] = gender_titled  # type: ignore[assignment]
        else:
            gender_value = "Other"
        patient_create = PatientCreate(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            date_of_birth=dob_date,
            gender=gender_value,
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            address=address.strip() if address else None,
            created_by="agent",
        )
        patient_id = crud.create_patient(patient_create)
        patient = crud.get_patient_by_id(patient_id)
        if patient:
            return PatientToolResult(
                success=True,
                message=f"Successfully created patient: {first_name} {last_name}",
                data=[patient.model_dump()],
            )
        return PatientToolResult(
            success=False,
            message="Failed to create patient: Not found after creation.",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}")


async def update_patient(
    ctx: RunContext[None],  # noqa: ARG001
    patient_id: int,
    first_name: str,
    last_name: str,
    date_of_birth: str,
    gender: str,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    updated_by: str = "agent",
) -> PatientToolResult:
    logger.info(f"Updating patient ID {patient_id}: {first_name} {last_name}")
    try:
        # Convert date_of_birth to date
        dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        # Validate gender
        gender_titled = gender.title()
        if gender_titled in ("Male", "Female", "Other"):
            gender_value: Literal["Male", "Female", "Other"] = gender_titled  # type: ignore[assignment]
        else:
            gender_value = "Other"
        patient_update = PatientCreate(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            date_of_birth=dob_date,
            gender=gender_value,
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            address=address.strip() if address else None,
            created_by=updated_by,
        )
        success = crud.update_patient(patient_id, patient_update, updated_by)
        if success:
            patient = crud.get_patient_by_id(patient_id)
            if patient:
                return PatientToolResult(
                    success=True,
                    message=f"Successfully updated patient: {format_patient_info(patient.model_dump())}",
                    data=[patient.model_dump()],
                )
            return PatientToolResult(
                success=False,
                message="Patient updated but could not be retrieved.",
                data=[],
            )
        return PatientToolResult(
            success=False,
            message="Failed to update patient.",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error updating patient: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}", data=[])


async def process_patient_agent_request(
    prompt: str, model_name: str | None = None, request_id: str | None = None
) -> dict[str, Any]:
    """Process patient agent request and log usage metadata.

    Args:
        prompt: User's natural language prompt
        model_name: Optional model name override
        request_id: Optional request ID for tracking

    Returns:
        Dict with success, message, data, and usage metadata
    """
    logger.info(f"Processing patient agent request: {prompt}")
    start_time = time.time()
    llm_logger = get_llm_logger()

    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini"
    )

    try:
        agent_instance = get_patient_agent(model_name)
        result = await agent_instance.run(prompt)
        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Patient agent result: {result.output}")

        # Extract usage metadata from result
        usage_data = result.usage()
        prompt_tokens = usage_data.request_tokens if usage_data else None
        completion_tokens = usage_data.response_tokens if usage_data else None
        total_tokens = usage_data.total_tokens if usage_data else None

        # Log to LLM logger
        log_request_id = llm_logger.log_request(
            endpoint="/agent/process",
            model_name=deployment_name,
            request_data={"prompt": prompt, "model_name": model_name},
            response_data={"output": str(result.output)},
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            success=True,
            request_id=request_id,
        )

        return {
            "success": True,
            "message": str(result.output),
            "data": None,
            "usage": {
                "request_id": log_request_id,
                "model": deployment_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "duration_ms": duration_ms,
            },
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Patient agent error: {e}")

        # Log error to LLM logger
        llm_logger.log_request(
            endpoint="/agent/process",
            model_name=deployment_name,
            request_data={"prompt": prompt, "model_name": model_name},
            response_data={},
            duration_ms=duration_ms,
            success=False,
            error=str(e),
            request_id=request_id,
        )

        return {
            "success": False,
            "message": f"Patient agent failed to process request: {e!s}",
            "data": None,
            "usage": {
                "request_id": request_id,
                "model": deployment_name,
                "duration_ms": duration_ms,
                "error": str(e),
            },
        }
