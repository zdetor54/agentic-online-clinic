"""Agentic patient management orchestrator using PydanticAI and direct CRUD access."""

import os
import time
from datetime import date
from typing import Any

from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from src.api.appointments.schemas import AppointmentCreate
from src.core.llm_logger import get_llm_logger
from src.llm.deps import AppointmentDeps, get_default_appointment_deps


class AppointmentToolResult(BaseModel):
    """Result from appointment tool operations."""

    success: bool
    message: str
    data: list[dict[str, Any]] = []


_appointment_agent: Agent | None = None


def format_appointment_info(appointment: dict) -> str:
    return (
        f"ID: {appointment['id']}, Patient ID: {appointment['patient_id']}, "
        f"Date: {appointment.get('appointment_date', 'N/A')}, Start Time: {appointment.get('appointment_start_time', 'N/A')}, End Time: {appointment.get('appointment_end_time', 'N/A')}, "
        f"Reason: {appointment.get('appointment_reason', 'N/A')}"
    )


def get_appointment_agent(model_name: str | None = None) -> Agent:
    """
    Get or create the PydanticAI appointment agent instance.
    Args:
        model_name: Optional model name override
                   If None, uses AZURE_OPENAI_DEPLOYMENT_NAME from .env
    Returns:
        Configured PydanticAI Agent with Azure OpenAI
    """
    global _appointment_agent  # noqa: PLW0603
    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"
    )
    if _appointment_agent is None:
        azure_provider = AzureProvider(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
        model = OpenAIChatModel(deployment_name, provider=azure_provider)
        # Load system prompt from YAML file
        from pathlib import Path

        import yaml

        prompt_path = Path(__file__).parent / "agent_system_prompts.yaml"
        with prompt_path.open(encoding="utf-8") as f:
            prompts = yaml.safe_load(f)
        system_prompt = prompts.get("appointment_agent", "")
        _appointment_agent = Agent(
            model,
            deps_type=AppointmentDeps,
            system_prompt=system_prompt,
        )
        _appointment_agent.tool(search_appointments)
        _appointment_agent.tool(get_appointment_by_id)
        _appointment_agent.tool(create_appointment)
        _appointment_agent.tool(update_appointment)
        logger.info(
            f"Initialized PydanticAI appointment agent with Azure OpenAI: {deployment_name}"
        )
    return _appointment_agent


async def search_appointments(
    ctx: RunContext[AppointmentDeps],
    appointment_date: str | None = None,
    patient_id: int | None = None,
) -> AppointmentToolResult:
    logger.info(
        f"Searching appointments: date={appointment_date}, patient_id={patient_id}"
    )
    try:
        appointments = ctx.deps.crud.list_appointments(
            appointment_date=appointment_date, patient_id=patient_id
        )
        if appointments:
            appointment_list = [
                format_appointment_info(a.model_dump()) for a in appointments
            ]
            return AppointmentToolResult(
                success=True,
                message=f"Found {len(appointments)} appointment(s):\n"
                + "\n".join(appointment_list),
                data=[a.model_dump() for a in appointments],
            )
        return AppointmentToolResult(
            success=True,
            message=f"No appointments found for date='{appointment_date}' or patient_id='{patient_id}'",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error searching appointments: {e}")
        return AppointmentToolResult(success=False, message=f"Error: {e!s}")


async def get_appointment_by_id(
    ctx: RunContext[AppointmentDeps],
    appointment_id: int,
) -> AppointmentToolResult:
    logger.info(f"Fetching appointment ID: {appointment_id}")
    try:
        appointment = ctx.deps.crud.get_appointment_by_id(appointment_id)
        if appointment:
            return AppointmentToolResult(
                success=True,
                message=format_appointment_info(appointment.model_dump()),
                data=[appointment.model_dump()],
            )
        return AppointmentToolResult(
            success=True,
            message=f"No appointment found with ID {appointment_id}",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error fetching appointment: {e}")
        return AppointmentToolResult(success=False, message=f"Error: {e!s}", data=[])


async def create_appointment(
    ctx: RunContext[AppointmentDeps],
    patient_id: int,
    appointment_date: str,
    appointment_start_time: str,
    appointment_end_time: str,
    appointment_reason: str | None = None,
) -> AppointmentToolResult:
    logger.info(
        f"Creating appointment for patient {patient_id}: {appointment_date} {appointment_start_time} - {appointment_end_time}"
    )
    try:
        appointment_create = AppointmentCreate(
            patient_id=patient_id,
            appointment_date=date.fromisoformat(appointment_date),
            appointment_start_time=appointment_start_time,
            appointment_end_time=appointment_end_time,
            appointment_reason=appointment_reason,
            created_by="agent",
        )
        appointment_id = ctx.deps.crud.create_appointment(appointment_create)
        appointment = ctx.deps.crud.get_appointment_by_id(appointment_id)
        if appointment:
            return AppointmentToolResult(
                success=True,
                message=f"Successfully created appointment: {format_appointment_info(appointment.model_dump())}",
                data=[appointment.model_dump()],
            )
        return AppointmentToolResult(
            success=False,
            message="Failed to create appointment: Not found after creation.",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        return AppointmentToolResult(success=False, message=f"Error: {e!s}")


async def update_appointment(
    ctx: RunContext[AppointmentDeps],
    appointment_id: int,
    patient_id: int,
    appointment_date: str,
    appointment_start_time: str,
    appointment_end_time: str,
    appointment_reason: str | None = None,
    updated_by: str = "agent",
) -> AppointmentToolResult:
    logger.info(
        f"Updating appointment ID {appointment_id} for patient {patient_id}: {appointment_date} {appointment_start_time} - {appointment_end_time}"
    )
    try:
        appointment_update = AppointmentCreate(
            patient_id=patient_id,
            appointment_date=date.fromisoformat(appointment_date),
            appointment_start_time=appointment_start_time,
            appointment_end_time=appointment_end_time,
            appointment_reason=appointment_reason,
        )
        success = ctx.deps.crud.update_appointment(
            appointment_id, appointment_update, updated_by
        )
        if success:
            appointment = ctx.deps.crud.get_appointment_by_id(appointment_id)
            if appointment:
                return AppointmentToolResult(
                    success=True,
                    message=f"Successfully updated appointment: {format_appointment_info(appointment.model_dump())}",
                    data=[appointment.model_dump()],
                )
            return AppointmentToolResult(
                success=False,
                message="Appointment updated but could not be retrieved.",
                data=[],
            )
        return AppointmentToolResult(
            success=False,
            message="Failed to update appointment.",
            data=[],
        )
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        return AppointmentToolResult(success=False, message=f"Error: {e!s}", data=[])


async def process_appointment_agent_request(
    prompt: str,
    model_name: str | None = None,
    request_id: str | None = None,
    message_history: list[dict[str, str]] | None = None,
    cumulative_usage: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Process appointment agent request and log usage metadata.

    Args:
        prompt: User's natural language prompt
        model_name: Optional model name override
        request_id: Optional request ID for tracking
        message_history: Optional conversation history for multi-turn chat
                        Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        cumulative_usage: Optional cumulative token usage from previous turns
                         Format: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}

    Returns:
        Dict with success, message, data, usage metadata (current + cumulative), and updated message_history
    """
    logger.info(f"Processing appointment agent request: {prompt}")
    start_time = time.time()
    llm_logger = get_llm_logger()

    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini"
    )

    try:
        agent_instance = get_appointment_agent(model_name)

        # Convert message_history to PydanticAI format if provided
        pydantic_history = None
        if message_history:
            from pydantic_ai.messages import (
                ModelRequest,
                ModelResponse,
                TextPart,
                UserPromptPart,
            )

            pydantic_history = []
            for msg in message_history:
                if msg["role"] == "user":
                    pydantic_history.append(
                        ModelRequest(parts=[UserPromptPart(msg["content"])])
                    )
                elif msg["role"] == "assistant":
                    pydantic_history.append(
                        ModelResponse(parts=[TextPart(content=msg["content"])])
                    )

        deps = get_default_appointment_deps(request_id)
        result = await agent_instance.run(
            prompt, deps=deps, message_history=pydantic_history
        )
        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Appointment agent result: {result.output}")

        # Extract usage metadata from current turn
        usage_data = result.usage()
        current_prompt_tokens = usage_data.request_tokens if usage_data else 0
        current_completion_tokens = usage_data.response_tokens if usage_data else 0
        current_total_tokens = usage_data.total_tokens if usage_data else 0

        # Calculate cumulative usage across conversation
        prev_cumulative = cumulative_usage or {}
        cumulative_prompt_tokens = (
            prev_cumulative.get("prompt_tokens", 0) + current_prompt_tokens
        )
        cumulative_completion_tokens = (
            prev_cumulative.get("completion_tokens", 0) + current_completion_tokens
        )
        cumulative_total_tokens = (
            prev_cumulative.get("total_tokens", 0) + current_total_tokens
        )

        logger.info(
            f"Token usage - Current turn: {current_total_tokens} "
            f"(prompt: {current_prompt_tokens}, completion: {current_completion_tokens})"
        )
        logger.info(
            f"Token usage - Cumulative: {cumulative_total_tokens} "
            f"(prompt: {cumulative_prompt_tokens}, completion: {cumulative_completion_tokens})"
        )

        # Log cumulative usage to LLM logger
        request_data = {
            "prompt": prompt,
            "model_name": model_name,
            "turn": len(message_history) // 2 + 1 if message_history else 1,
        }
        if message_history:
            request_data["message_history"] = message_history

        log_request_id = llm_logger.log_request(
            endpoint="/agent/process",
            model_name=deployment_name,
            request_data=request_data,
            response_data={"output": str(result.output)},
            prompt_tokens=cumulative_prompt_tokens,
            completion_tokens=cumulative_completion_tokens,
            total_tokens=cumulative_total_tokens,
            duration_ms=duration_ms,
            success=True,
            request_id=request_id,
        )

        # Build updated message history
        updated_history = message_history.copy() if message_history else []
        updated_history.append({"role": "user", "content": prompt})
        updated_history.append({"role": "assistant", "content": str(result.output)})

        return {
            "success": True,
            "message": str(result.output),
            "data": None,
            "usage": {
                "request_id": log_request_id,
                "model": deployment_name,
                "current_turn": {
                    "prompt_tokens": current_prompt_tokens,
                    "completion_tokens": current_completion_tokens,
                    "total_tokens": current_total_tokens,
                },
                "cumulative": {
                    "prompt_tokens": cumulative_prompt_tokens,
                    "completion_tokens": cumulative_completion_tokens,
                    "total_tokens": cumulative_total_tokens,
                },
                "duration_ms": duration_ms,
            },
            "message_history": updated_history,
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
