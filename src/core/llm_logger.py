"""LLM request/response logging utility for tracking API calls, token usage, and costs."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


class LLMLogEntry(BaseModel):
    """Structured log entry for LLM API calls."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    endpoint: str
    model_name: str
    request_data: dict[str, Any]
    response_data: dict[str, Any]
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None  # Always 3 decimals, USD
    duration_ms: int | None = None
    success: bool = True
    error: str | None = None


class LLMLogger:
    """Logger for LLM API requests and responses."""

    # Pricing per 1M tokens (latest as of 2026-02, Standard tier)
    PRICING: ClassVar[dict[str, dict[str, float]]] = {
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-5": {"input": 1.25, "output": 10.00},
        "gpt-5-mini": {"input": 0.25, "output": 2.00},
        "gpt-5-nano": {"input": 0.05, "output": 0.40},
    }

    def __init__(self, log_dir: str | Path = "logs") -> None:
        """Initialize LLM logger with log directory.

        Args:
            log_dir: Directory to store LLM logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.log_file = self.log_dir / "llm_requests.json"

    def _calculate_cost(
        self, model_name: str, prompt_tokens: int | None, completion_tokens: int | None
    ) -> float | None:
        """Calculate estimated cost based on token usage, rounded to 3 decimals.

        Args:
            model_name: Name of the model used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD (rounded to 3 decimals) or None if pricing unavailable
        """
        if not prompt_tokens or not completion_tokens:
            return None

        # Prefer exact match, then fallback to substring match (longest key first)
        model_name_lc = model_name.lower()
        pricing_key = None
        # Try exact match first
        if model_name_lc in self.PRICING:
            pricing_key = model_name_lc
        else:
            # Try substring match, prefer longest key
            sorted_keys = sorted(self.PRICING.keys(), key=len, reverse=True)
            for key in sorted_keys:
                if key in model_name_lc:
                    pricing_key = key
                    break

        if not pricing_key:
            logger.warning(f"No pricing found for model: {model_name}")
            return None

        pricing = self.PRICING[pricing_key]
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
        # return round(input_cost + output_cost, 3)

    def log_request(
        self,
        endpoint: str,
        model_name: str,
        request_data: dict[str, Any],
        response_data: dict[str, Any],
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        duration_ms: int | None = None,
        success: bool = True,
        error: str | None = None,
        request_id: str | None = None,
    ) -> str:
        """Log an LLM request/response to a JSON file as a list of entries.

        Args:
            endpoint: API endpoint called
            model_name: Model name used
            request_data: Request payload
            response_data: Response payload
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total number of tokens
            duration_ms: Request duration in milliseconds
            success: Whether the request succeeded
            error: Error message if request failed
            request_id: Optional request ID (generated if not provided)

        Returns:
            Request ID for tracking
        """
        import json

        estimated_cost_usd = self._calculate_cost(
            model_name, prompt_tokens, completion_tokens
        )

        log_entry = LLMLogEntry(
            request_id=request_id or str(uuid4()),
            endpoint=endpoint,
            model_name=model_name,
            request_data=request_data,
            response_data=response_data,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

        # Read existing log (list of entries)
        if self.log_file.exists():
            try:
                with self.log_file.open("r", encoding="utf-8") as f:
                    log_data = json.load(f)
                if not isinstance(log_data, list):
                    log_data = []
            except Exception as e:
                logger.warning(f"Failed to read log file, starting new log: {e}")
                log_data = []
        else:
            log_data = []

        log_data.append(log_entry.model_dump())

        # Write back as pretty JSON
        with self.log_file.open("w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.debug(
            f"Logged LLM request {log_entry.request_id}: "
            f"model={model_name}, tokens={total_tokens}, cost=${estimated_cost_usd} USD"
        )

        return log_entry.request_id

    def get_logs(
        self, limit: int | None = None, filter_model: str | None = None
    ) -> list[dict]:
        """Retrieve logged entries as dicts (robust to missing fields).

        Args:
            limit: Maximum number of entries to return (most recent first)
            filter_model: Filter by model name

        Returns:
            List of log entry dicts
        """
        import json

        if not self.log_file.exists():
            return []

        with self.log_file.open("r", encoding="utf-8") as f:
            try:
                log_data = json.load(f)
            except Exception:
                return []

        entries = [
            entry
            for entry in log_data
            if isinstance(entry, dict)
            and (filter_model is None or filter_model in entry.get("model_name", ""))
        ]
        entries.reverse()
        if limit:
            entries = entries[:limit]
        return entries

    def get_total_cost(self, filter_model: str | None = None) -> float:
        """Calculate total estimated cost from logs (robust to missing fields).

        Args:
            filter_model: Filter by model name

        Returns:
            Total estimated cost in USD
        """
        entries = self.get_logs(filter_model=filter_model)
        return sum(
            float(entry.get("estimated_cost_usd", 0) or 0)
            for entry in entries
            if "estimated_cost_usd" in entry and entry["estimated_cost_usd"] is not None
        )

    def get_cost_breakdown(
        self,
        filter_model: str | None = None,
    ) -> dict[str, dict[str, dict[str, float]]]:
        """Get cost breakdown by date, hour, and model.

        Args:
            filter_model: Filter by model name

        Returns:
            Nested dict: {date: {hour: {model: total_cost}}}
        """
        from collections import defaultdict
        from datetime import datetime

        entries = self.get_logs(filter_model=filter_model)
        breakdown: dict[str, dict[str, dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(float))
        )
        for entry in entries:
            ts = entry.get("timestamp")
            model = entry.get("model_name", "unknown")
            cost = float(entry.get("estimated_cost_usd", 0) or 0)
            if not ts or cost == 0:
                continue
            try:
                dt = datetime.fromisoformat(ts)
                date_str = dt.date().isoformat()
                hour_str = f"{dt.hour:02d}"
            except Exception as exc:
                import logging

                logging.warning(f"Failed to parse timestamp '{ts}': {exc}")
                continue
            breakdown[date_str][hour_str][model] += cost
        return breakdown


# Global logger instance
_llm_logger: LLMLogger | None = None


def get_llm_logger(log_dir: str | Path = "logs") -> LLMLogger:
    """Get or create the global LLM logger instance.

    Args:
        log_dir: Directory to store LLM logs

    Returns:
        LLMLogger instance
    """
    global _llm_logger  # noqa: PLW0603
    if _llm_logger is None:
        _llm_logger = LLMLogger(log_dir)
    return _llm_logger
