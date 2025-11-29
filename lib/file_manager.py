"""File operations for loading and managing data files.

Following agent.md guidelines:
- Type hints on all functions
- Docstrings with Google style
- Structured logging instead of print
- Specific exceptions
- DRY principle (reusable functions)
"""

import logging
from pathlib import Path
from typing import Literal

from lib.exceptions import DataFileNotFoundError, InvalidDataFormatError

logger = logging.getLogger(__name__)

# Type alias for valid data file types
DataFileType = Literal[
    "staples",
    "fresh",
    "shopping_list",
    "loved_recipes",
    "liked_recipes",
    "not_again_recipes",
    "generated_recipes",
    "preferences",
    "meal_history",
    "weekly_plan",
]


def get_data_file_path(file_type: DataFileType) -> Path:
    """Get the path to a data file by type.

    Args:
        file_type: Type of data file to load

    Returns:
        Path object pointing to the data file

    Raises:
        ValueError: If file_type is not recognized

    Example:
        >>> path = get_data_file_path("staples")
        >>> print(path)
        data/pantry/staples.md
    """
    file_map = {
        "staples": "data/pantry/staples.md",
        "fresh": "data/pantry/fresh.md",
        "shopping_list": "data/pantry/shopping_list.md",
        "loved_recipes": "data/recipes/loved.md",
        "liked_recipes": "data/recipes/liked.md",
        "not_again_recipes": "data/recipes/not_again.md",
        "generated_recipes": "data/recipes/generated.md",
        "preferences": "data/preferences.md",
        "meal_history": "data/meal_history.md",
        "weekly_plan": "data/weekly_plan.md",
    }

    if file_type not in file_map:
        raise ValueError(f"Unknown file type: {file_type}")

    return Path(file_map[file_type])


def load_data_file(file_type: DataFileType) -> str:
    """Load a data file and return its contents.

    Args:
        file_type: Type of data file to load

    Returns:
        File contents as string

    Raises:
        DataFileNotFoundError: If file doesn't exist
        InvalidDataFormatError: If file is empty or unreadable

    Example:
        >>> content = load_data_file("staples")
        >>> "Pantry Staples" in content
        True
    """
    file_path = get_data_file_path(file_type)

    logger.debug(
        "Loading data file",
        extra={"file_type": file_type, "file_path": str(file_path)},
    )

    # Check if file exists
    if not file_path.exists():
        logger.error(
            "Data file not found",
            extra={"file_type": file_type, "file_path": str(file_path)},
        )
        raise DataFileNotFoundError(
            f"Data file not found: {file_path}. "
            f"Please ensure the data directory structure is set up correctly."
        )

    try:
        content = file_path.read_text(encoding="utf-8")

        # Validate content
        if not content or content.strip() == "":
            logger.warning(
                "Data file is empty",
                extra={"file_type": file_type, "file_path": str(file_path)},
            )
            raise InvalidDataFormatError(f"Data file is empty: {file_path}")

        logger.info(
            "Data file loaded successfully",
            extra={
                "file_type": file_type,
                "file_path": str(file_path),
                "size_bytes": len(content),
            },
        )

        return content

    except UnicodeDecodeError as e:
        logger.error(
            "Failed to decode data file",
            extra={"file_type": file_type, "error": str(e)},
            exc_info=True,
        )
        raise InvalidDataFormatError(
            f"Cannot read file {file_path}: Invalid encoding. Expected UTF-8."
        ) from e


def load_all_pantry_data() -> dict[str, str]:
    """Load all pantry-related data files.

    Returns:
        Dictionary with keys: staples, fresh, shopping_list
        Values are file contents as strings

    Raises:
        DataFileNotFoundError: If any required file is missing

    Example:
        >>> pantry_data = load_all_pantry_data()
        >>> "staples" in pantry_data
        True
    """
    logger.info("Loading all pantry data files")

    try:
        pantry_data = {
            "staples": load_data_file("staples"),
            "fresh": load_data_file("fresh"),
            "shopping_list": load_data_file("shopping_list"),
        }

        logger.info(
            "All pantry data loaded successfully",
            extra={
                "files_loaded": 3,
                "total_size_bytes": sum(len(v) for v in pantry_data.values()),
            },
        )

        return pantry_data

    except DataFileNotFoundError:
        logger.error("Failed to load pantry data - missing files")
        raise


def load_all_recipe_data() -> dict[str, str]:
    """Load all recipe-related data files.

    Returns:
        Dictionary with keys: loved, liked, not_again, generated
        Values are file contents as strings

    Raises:
        DataFileNotFoundError: If any required file is missing

    Example:
        >>> recipe_data = load_all_recipe_data()
        >>> "loved" in recipe_data
        True
    """
    logger.info("Loading all recipe data files")

    try:
        recipe_data = {
            "loved": load_data_file("loved_recipes"),
            "liked": load_data_file("liked_recipes"),
            "not_again": load_data_file("not_again_recipes"),
            "generated": load_data_file("generated_recipes"),
        }

        logger.info(
            "All recipe data loaded successfully",
            extra={
                "files_loaded": 4,
                "total_size_bytes": sum(len(v) for v in recipe_data.values()),
            },
        )

        return recipe_data

    except DataFileNotFoundError:
        logger.error("Failed to load recipe data - missing files")
        raise


def load_context_for_recipe_generation() -> dict[str, str]:
    """Load all data needed for recipe generation.

    Returns:
        Dictionary containing all context data:
        - staples, fresh, shopping_list (pantry)
        - loved_recipes, preferences, meal_history

    Raises:
        DataFileNotFoundError: If any required file is missing

    Example:
        >>> context = load_context_for_recipe_generation()
        >>> all(k in context for k in ["staples", "fresh", "preferences"])
        True
    """
    logger.info("Loading context for recipe generation")

    try:
        # Load pantry data
        pantry_data = load_all_pantry_data()

        # Load recipe and preference data
        context = {
            **pantry_data,
            "loved_recipes": load_data_file("loved_recipes"),
            "preferences": load_data_file("preferences"),
            "meal_history": load_data_file("meal_history"),
        }

        logger.info(
            "Recipe generation context loaded successfully",
            extra={
                "files_loaded": len(context),
                "total_size_bytes": sum(len(v) for v in context.values()),
            },
        )

        return context

    except DataFileNotFoundError:
        logger.error("Failed to load recipe generation context")
        raise
