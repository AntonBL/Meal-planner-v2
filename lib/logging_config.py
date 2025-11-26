"""Logging configuration for AI Recipe Planner.

Following agent.md guidelines: Use structured logging instead of print statements.
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started", extra={"version": "0.1.0"})
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Log to stdout for containerization (Streamlit Cloud, Docker)
            logging.StreamHandler(sys.stdout),
            # Also log to file for local development
            logging.FileHandler(logs_dir / "app.log"),
        ],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)
