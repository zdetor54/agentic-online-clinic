"""API routes for agentic patient management."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

agent_router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    """Request model for agent processing."""

    prompt: str
    model_name: str | None = None
    message_history: list[dict[str, str]] | None = (
        None  # Chat history for multi-turn conversations
    )


class AgentResponse(BaseModel):
    """Response model for agent processing."""

    success: bool
    message: str
    data: dict | list | None = None
    usage: dict | None = None  # LLM usage metadata
    message_history: list[dict[str, str]] | None = None  # Updated conversation history


@agent_router.post("/process", summary="Process natural language request")
async def process_agent_endpoint(request: AgentRequest) -> AgentResponse:
    """
    Process a natural language request through the agentic orchestrator.

    Args:
        request: AgentRequest containing the user's prompt

    Returns:
        AgentResponse with the agent's result and usage metadata

    Raises:
        HTTPException: 400 if prompt is empty, 500 if processing fails
    """
    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty",
        )

    # Generate request ID for tracking
    request_id = str(uuid4())
    logger.info(f"[{request_id}] Received agent request: {request.prompt[:100]}...")

    try:
        from src.llm.orchestrator_agent import process_orchestrator_request

        result = await process_orchestrator_request(
            prompt=request.prompt,
            model_name=request.model_name,
            message_history=request.message_history,
            request_id=request_id,
        )
        if (
            not isinstance(result, dict)
            or "success" not in result
            or "message" not in result
        ):
            logger.error(f"[{request_id}] Agent returned invalid response: {result}")
            raise HTTPException(
                status_code=500, detail="Agent did not return a valid response"
            )
        return AgentResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data"),
            usage=result.get("usage"),
            message_history=result.get("message_history"),
        )

    except Exception as e:
        logger.error(f"[{request_id}] Agent endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {e!s}",
        ) from e
