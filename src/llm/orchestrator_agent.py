"""Orchestrator agent that routes requests between patient and appointment agents."""

import os
import time
from typing import Any

from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from src.core.llm_logger import get_llm_logger
from src.llm.appointment_agent import process_appointment_agent_request
from src.llm.patient_agent import process_patient_agent_request


class OrchestratorToolResult(BaseModel):
    """Result from orchestrator tool operations."""

    success: bool
    message: str
    data: dict[str, Any] | None = None


_orchestrator_agent: Agent | None = None


def get_orchestrator_agent(model_name: str | None = None) -> Agent:
    """
    Get or create the PydanticAI orchestrator agent instance.

    Args:
        model_name: Optional model name override
                   If None, uses AZURE_OPENAI_DEPLOYMENT_NAME from .env

    Returns:
        Configured PydanticAI Agent with Azure OpenAI
    """
    global _orchestrator_agent  # noqa: PLW0603
    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"
    )
    if _orchestrator_agent is None:
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
        system_prompt = prompts.get("orchestrator_agent", "")

        _orchestrator_agent = Agent(
            model,
            system_prompt=system_prompt,
        )
        _orchestrator_agent.tool(delegate_to_patient_agent)
        _orchestrator_agent.tool(delegate_to_appointment_agent)

        logger.info(
            f"Initialized PydanticAI orchestrator agent with Azure OpenAI: {deployment_name}"
        )
    return _orchestrator_agent


async def delegate_to_patient_agent(
    ctx: RunContext[None],  # noqa: ARG001
    prompt: str,
) -> OrchestratorToolResult:
    """
    Delegate a patient-related request to the patient agent.

    Use this tool when the user wants to:
    - Search for patients by name or phone
    - View patient details
    - Create new patient records
    - Update existing patient information

    Args:
        prompt: The user's request related to patient management

    Returns:
        Result from the patient agent
    """
    logger.info(f"Orchestrator delegating to patient agent: {prompt[:100]}")
    try:
        result = await process_patient_agent_request(
            prompt=prompt,
            model_name=None,
            message_history=None,
            request_id=None,
        )

        return OrchestratorToolResult(
            success=result["success"],
            message=result["message"],
            data={"agent": "patient", "result": result},
        )
    except Exception as e:
        logger.error(f"Error delegating to patient agent: {e}")
        return OrchestratorToolResult(
            success=False,
            message=f"Patient agent error: {e!s}",
            data=None,
        )


async def delegate_to_appointment_agent(
    ctx: RunContext[None],  # noqa: ARG001
    prompt: str,
) -> OrchestratorToolResult:
    """
    Delegate an appointment-related request to the appointment agent.

    Use this tool when the user wants to:
    - Schedule new appointments
    - View appointment details
    - List appointments by date or patient
    - Update or cancel existing appointments

    Args:
        prompt: The user's request related to appointment management

    Returns:
        Result from the appointment agent
    """
    logger.info(f"Orchestrator delegating to appointment agent: {prompt[:100]}")
    try:
        result = await process_appointment_agent_request(
            prompt=prompt,
            model_name=None,
            message_history=None,
            request_id=None,
        )

        return OrchestratorToolResult(
            success=result["success"],
            message=result["message"],
            data={"agent": "appointment", "result": result},
        )
    except Exception as e:
        logger.error(f"Error delegating to appointment agent: {e}")
        return OrchestratorToolResult(
            success=False,
            message=f"Appointment agent error: {e!s}",
            data=None,
        )


async def process_orchestrator_request(
    prompt: str,
    model_name: str | None = None,
    message_history: list[dict[str, str]] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Process a user request through the orchestrator agent.

    The orchestrator analyzes the request and routes it to the appropriate
    specialist agent (patient or appointment).

    Args:
        prompt: User's natural language request
        model_name: Optional model override
        message_history: Previous conversation context
        request_id: Optional tracking ID

    Returns:
        Dict containing success status, message, usage metadata, and updated history
    """
    start_time = time.time()
    llm_logger = get_llm_logger()

    deployment_name = model_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano"
    )

    try:
        agent = get_orchestrator_agent(model_name=model_name)

        # Run the agent with conversation history
        result = await agent.run(prompt, message_history=message_history)
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract token usage from result
        usage = result.usage()
        current_prompt_tokens = usage.request_tokens if usage else 0
        current_completion_tokens = usage.response_tokens if usage else 0
        current_total_tokens = usage.total_tokens if usage else 0

        # Calculate cumulative token usage across conversation
        cumulative_usage = None
        if message_history:
            # Extract cumulative usage from last message if available
            for msg in reversed(message_history):
                if msg.get("role") == "assistant" and isinstance(
                    msg.get("usage"), dict
                ):
                    cumulative_usage = msg["usage"].get("cumulative")
                    break

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
        logger.error(f"Orchestrator agent error: {e}")

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
            "message": f"Orchestrator agent failed to process request: {e!s}",
            "data": None,
            "usage": {
                "request_id": request_id,
                "model": deployment_name,
                "duration_ms": duration_ms,
                "error": str(e),
            },
        }
