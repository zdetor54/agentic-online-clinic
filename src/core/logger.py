import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from loguru import logger

LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

# Generate a consistent timestamp per session
_SESSION_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def configure_logger(
    log_dir: str = "logs",
    rotation: str = "10 MB",
    retention: str = "30 days",
    file_level: LogLevel = "DEBUG",
    terminal_level: LogLevel = "INFO",
) -> None:
    """Configures the Loguru logger to log to both files and terminal.

    Args:
        log_dir: Directory to store log files.
        rotation: Log rotation policy.
        retention: Log file retention policy.
        file_level: Log level for file output.
        terminal_level: Log level for terminal output.
    """
    Path(log_dir).mkdir(exist_ok=True)
    script_name = Path(sys.argv[0]).stem
    log_filename = f"{log_dir}/{script_name}_{_SESSION_TIMESTAMP}.log"

    # Check if log file already exists (logger already configured)
    if Path(log_filename).exists():
        return

    # Remove existing handlers to avoid duplicate logs
    logger.remove()
    logger.add(log_filename, rotation=rotation, retention=retention, level=file_level)
    logger.add(sys.stdout, level=terminal_level)

    # Create the log file by writing an initial log entry
    logger.debug("Logger configured successfully")
