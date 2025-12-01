"""Chat Manager - Persistent storage for cooking chat history.

Manages the cooking chat state across sessions by storing it in a JSON file.
"""

import json
from pathlib import Path

from lib.logging_config import get_logger

logger = get_logger(__name__)

# File name for chat history
CHAT_HISTORY_FILE = "cooking_chat_history.json"


def _get_chat_history_path() -> Path:
    """Get the path to the chat history JSON file.

    Returns:
        Path object pointing to the chat history file
    """
    return Path(__file__).parent.parent / "data" / CHAT_HISTORY_FILE


def save_chat_history(messages: list[dict[str, str]]) -> bool:
    """Save the chat history to persistent storage.

    Args:
        messages: List of message dictionaries (role, content)

    Returns:
        True if successful, False otherwise
    """
    try:
        path = _get_chat_history_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        # Log occasionally or on error, but maybe not every save to avoid noise
        # logger.debug("Saved chat history")
        return True

    except Exception as e:
        logger.error(
            "Failed to save chat history",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def load_chat_history() -> list[dict[str, str]]:
    """Load the chat history from persistent storage.

    Returns:
        List of message dictionaries, or empty list if none found
    """
    try:
        path = _get_chat_history_path()

        if not path.exists():
            return []

        with open(path, encoding='utf-8') as f:
            messages = json.load(f)

        logger.info(
            "Loaded chat history from file",
            extra={"message_count": len(messages)}
        )
        return messages

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse chat history JSON",
            extra={"error": str(e)},
            exc_info=True
        )
        return []

    except Exception as e:
        logger.error(
            "Failed to load chat history",
            extra={"error": str(e)},
            exc_info=True
        )
        return []


def clear_chat_history() -> bool:
    """Clear the chat history from persistent storage.

    Returns:
        True if successful, False otherwise
    """
    try:
        path = _get_chat_history_path()

        if path.exists():
            path.unlink()
            logger.info("Cleared chat history file")

        return True

    except Exception as e:
        logger.error(
            "Failed to clear chat history",
            extra={"error": str(e)},
            exc_info=True
        )
        return False
