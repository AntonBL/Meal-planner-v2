"""Custom exceptions for AI Recipe Planner.

Following agent.md guidelines: Use specific exceptions for better error handling.
"""


class RecipePlannerError(Exception):
    """Base exception for recipe planner errors."""

    pass


class DataFileNotFoundError(RecipePlannerError):
    """Data file not found in expected location."""

    pass


class InvalidDataFormatError(RecipePlannerError):
    """Data file has invalid or corrupted format."""

    pass


class LLMAPIError(RecipePlannerError):
    """Error communicating with LLM API."""

    pass


class RecipeParsingError(RecipePlannerError):
    """Error parsing recipe from LLM response."""

    pass


class InvalidIngredientError(RecipePlannerError):
    """Invalid ingredient provided."""

    pass
