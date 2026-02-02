"""API routes for agentic patient management."""

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from src.llm.agent import process_agent_request

agent_router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    """Request model for agent processing."""

    prompt: str
    model_name: str | None = None


class AgentResponse(BaseModel):
    """Response model for agent processing."""

    success: bool
    message: str
    data: dict | list | None = None


@agent_router.post("/process", summary="Process natural language request")
async def process_agent_endpoint(request: AgentRequest) -> AgentResponse:
    """
    Process a natural language request through the agentic orchestrator.

    Args:
        request: AgentRequest containing the user's prompt

    Returns:
        AgentResponse with the agent's result

    Raises:
        HTTPException: 400 if prompt is empty, 500 if processing fails
    """
    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty",
        )

    logger.info(f"Received agent request: {request.prompt[:100]}...")

    try:
        result = await process_agent_request(request.prompt, request.model_name)
        if (
            not isinstance(result, dict)
            or "success" not in result
            or "message" not in result
        ):
            logger.error(f"Agent returned invalid response: {result}")
            raise HTTPException(
                status_code=500, detail="Agent did not return a valid response"
            )
        return AgentResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data"),
        )

    except Exception as e:
        logger.error(f"Agent endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {e!s}",
        ) from e
