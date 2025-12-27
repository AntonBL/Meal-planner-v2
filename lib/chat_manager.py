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


# ============================================================================
# PER-RECIPE CHAT HISTORY SUPPORT (Multi-Recipe Mode)
# ============================================================================

def _get_recipe_chat_path(recipe_id: str) -> Path:
    """Get the path to a recipe-specific chat history file.

    Args:
        recipe_id: Unique identifier for the recipe

    Returns:
        Path object pointing to the recipe's chat history file
    """
    # Sanitize recipe_id for use in filename (remove special chars)
    safe_id = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in str(recipe_id))
    filename = f"cooking_chat_{safe_id}.json"
    return Path(__file__).parent.parent / "data" / filename


def save_recipe_chat_history(recipe_id: str, messages: list[dict[str, str]]) -> bool:
    """Save chat history for a specific recipe.

    Args:
        recipe_id: Unique identifier for the recipe
        messages: List of message dictionaries (role, content)

    Returns:
        True if successful, False otherwise
    """
    try:
        path = _get_recipe_chat_path(recipe_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        logger.debug(
            "Saved recipe chat history",
            extra={"recipe_id": recipe_id, "message_count": len(messages)}
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to save recipe chat history",
            extra={"recipe_id": recipe_id, "error": str(e)},
            exc_info=True
        )
        return False


def load_recipe_chat_history(recipe_id: str) -> list[dict[str, str]]:
    """Load chat history for a specific recipe.

    Args:
        recipe_id: Unique identifier for the recipe

    Returns:
        List of message dictionaries, or empty list if none found
    """
    try:
        path = _get_recipe_chat_path(recipe_id)

        if not path.exists():
            logger.debug(
                "No chat history found for recipe",
                extra={"recipe_id": recipe_id}
            )
            return []

        with open(path, encoding='utf-8') as f:
            messages = json.load(f)

        logger.debug(
            "Loaded recipe chat history",
            extra={"recipe_id": recipe_id, "message_count": len(messages)}
        )
        return messages

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse recipe chat history JSON",
            extra={"recipe_id": recipe_id, "error": str(e)},
            exc_info=True
        )
        return []

    except Exception as e:
        logger.error(
            "Failed to load recipe chat history",
            extra={"recipe_id": recipe_id, "error": str(e)},
            exc_info=True
        )
        return []


def clear_recipe_chat_history(recipe_id: str) -> bool:
    """Clear chat history for a specific recipe.

    Args:
        recipe_id: Unique identifier for the recipe

    Returns:
        True if successful, False otherwise
    """
    try:
        path = _get_recipe_chat_path(recipe_id)

        if path.exists():
            path.unlink()
            logger.info(
                "Cleared recipe chat history",
                extra={"recipe_id": recipe_id}
            )

        return True

    except Exception as e:
        logger.error(
            "Failed to clear recipe chat history",
            extra={"recipe_id": recipe_id, "error": str(e)},
            exc_info=True
        )
        return False


def clear_all_recipe_chats() -> bool:
    """Clear all recipe-specific chat histories.

    Returns:
        True if successful, False otherwise
    """
    try:
        data_dir = Path(__file__).parent.parent / "data"

        # Find all cooking_chat_*.json files
        chat_files = data_dir.glob("cooking_chat_*.json")

        count = 0
        for chat_file in chat_files:
            # Don't delete the legacy single chat file
            if chat_file.name == CHAT_HISTORY_FILE:
                continue

            chat_file.unlink()
            count += 1

        logger.info(
            "Cleared all recipe chat histories",
            extra={"files_deleted": count}
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to clear all recipe chats",
            extra={"error": str(e)},
            exc_info=True
        )
        return False
