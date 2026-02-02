"""Agentic orchestrator for patient management using PydanticAI."""

import os
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class PatientToolResult(BaseModel):
    """Result from patient tool operations."""

    success: bool
    message: str
    data: dict[str, Any] | list[dict[str, Any]] | None = None


# Create agent instance (will be initialized when needed)
_agent: Agent | None = None


def get_agent(model_name: str | None = None) -> Agent:
    """
    Get or create the PydanticAI agent instance.

    Args:
        model_name: Optional model name override
                   If None, uses AZURE_OPENAI_DEPLOYMENT_NAME from .env

    Returns:
        Configured PydanticAI Agent with Azure OpenAI
    """
    global _agent  # noqa: PLW0603

    # Use provided model or default from env
    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"
    )

    if _agent is None:
        # Create Azure provider - it will use env vars automatically
        azure_provider = AzureProvider(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )

        # Create OpenAI chat model with Azure provider
        model = OpenAIChatModel(deployment_name, provider=azure_provider)

        _agent = Agent(
            model,
            system_prompt="""You are a helpful medical office assistant that helps manage patient records.

You can:
1. Search for patients by name or phone number
2. View a specific patient's details by ID
3. Create new patient records

IMPORTANT SEARCH RULES:
- When user says "Jane Smith", search using ONLY the last name "Smith"
- When user says "show me patient X Y", use the last name "Y" for search
- The search API matches first name OR last name separately, not full names together
- Example: For "Jane Smith", call search_patients with name="Smith"

Always use the patient ID from search results when you need to reference a specific patient.

Be clear and helpful in your responses.""",
        )
        # Register tools
        _agent.tool(search_patients)
        _agent.tool(get_patient_by_id)
        _agent.tool(create_patient)

        logger.info(
            f"Initialized PydanticAI agent with Azure OpenAI: {deployment_name}"
        )

    return _agent


async def search_patients(
    ctx: RunContext[None],  # noqa: ARG001
    name: str | None = None,
    phone: str | None = None,
) -> PatientToolResult:
    """
    Search for patients by name or phone number.

    Args:
        ctx: The context for the tool execution
        name: Patient name to search (matches first or last name or full name like "John Doe")
        phone: Phone number to search

    Returns:
        PatientToolResult with search results
    """
    logger.info(f"Searching patients: name={name}, phone={phone}")

    try:
        params = {}

        # If user provides a full name like "Jane Smith", try searching for both first and last
        if name:
            # Try the name as-is first
            params["name"] = name

        if phone:
            params["phone"] = phone

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/patients/", params=params, timeout=10.0
            )

            if response.status_code == 200:
                patients = response.json()
                if patients:
                    # Format patient info clearly
                    patient_list = []
                    for p in patients:
                        patient_info = (
                            f"ID: {p['id']}, Name: {p['first_name']} {p['last_name']}, "
                            f"DOB: {p['date_of_birth']}, Gender: {p['gender']}"
                        )
                        if p.get("phone"):
                            patient_info += f", Phone: {p['phone']}"
                        patient_list.append(patient_info)

                    return PatientToolResult(
                        success=True,
                        message=f"Found {len(patients)} patient(s):\n"
                        + "\n".join(patient_list),
                        data=patients,
                    )
                return PatientToolResult(
                    success=True,
                    message=f"No patients found with name='{name}' or phone='{phone}'",
                )

            return PatientToolResult(
                success=False,
                message=f"Search failed: {response.text}",
            )

    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}")


async def get_patient_by_id(
    ctx: RunContext[None],  # noqa: ARG001
    patient_id: int,
) -> PatientToolResult:
    """
    Get a specific patient by ID.

    Args:
        ctx: The context for the tool execution
        patient_id: The ID of the patient to retrieve

    Returns:
        PatientToolResult with patient details
    """
    logger.info(f"Fetching patient ID: {patient_id}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/patients/{patient_id}", timeout=10.0
            )

            if response.status_code == 200:
                patient = response.json()
                return PatientToolResult(
                    success=True,
                    message=f"Found patient: {patient['first_name']} {patient['last_name']}",
                    data=patient,
                )

            if response.status_code == 404:
                return PatientToolResult(
                    success=False, message=f"Patient with ID {patient_id} not found"
                )

            return PatientToolResult(
                success=False,
                message=f"Failed to retrieve patient: {response.text}",
            )

    except Exception as e:
        logger.error(f"Error fetching patient: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}")


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
    """
    Create a new patient record.

    Args:
        ctx: The context for the tool execution
        first_name: Patient's first name
        last_name: Patient's last name
        date_of_birth: Date of birth in YYYY-MM-DD format
        gender: Gender (Male, Female, or Other)
        phone: Phone number (optional)
        email: Email address (optional)
        address: Address (optional)

    Returns:
        PatientToolResult with created patient details
    """
    logger.info(f"Creating patient: {first_name} {last_name}")

    try:
        payload = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "date_of_birth": date_of_birth,
            "gender": gender,
            "phone": phone.strip() if phone else None,
            "email": email.strip() if email else None,
            "address": address.strip() if address else None,
            "created_by": "agent",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/patients/", json=payload, timeout=10.0
            )

            if response.status_code == 201:
                patient = response.json()
                return PatientToolResult(
                    success=True,
                    message=f"Successfully created patient: {first_name} {last_name}",
                    data=patient,
                )

            error_detail = response.json().get("detail", response.text)
            return PatientToolResult(
                success=False, message=f"Failed to create patient: {error_detail}"
            )

    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        return PatientToolResult(success=False, message=f"Error: {e!s}")


async def process_agent_request(
    prompt: str, model_name: str | None = None
) -> dict[str, Any]:
    """
    Process a natural language request through the agent.

    Args:
        prompt: The user's natural language request
        model_name: Optional model name override

    Returns:
        Dictionary with agent response
    """
    logger.info(f"Processing agent request: {prompt}")

    try:
        # Get agent instance when needed (lazy initialization)
        agent_instance = get_agent(model_name)
        result = await agent_instance.run(prompt)
        logger.info(f"Agent result: {result.output}")

        return {
            "success": True,
            "message": str(result.output),
            "data": None,
        }

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "success": False,
            "message": f"Agent failed to process request: {e!s}",
            "data": None,
        }
