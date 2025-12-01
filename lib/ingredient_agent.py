"""Ingredient Categorization Agent using LLM.

This module provides AI-powered ingredient categorization for the shopping list.
"""

import logging
from typing import Optional

from lib.exceptions import LLMAPIError
from lib.llm_core import ClaudeProvider, LLMProvider

logger = logging.getLogger(__name__)


class IngredientCategorizer:
    """Service for categorizing ingredients using LLM."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize ingredient categorizer.

        Args:
            llm_provider: LLM provider instance (defaults to ClaudeProvider)
        """
        self.llm = llm_provider or ClaudeProvider()
        logger.debug("IngredientCategorizer initialized")

    def categorize(self, ingredient_name: str) -> str:
        """Categorize an ingredient into a shopping category.

        Args:
            ingredient_name: Name of the ingredient to categorize

        Returns:
            Category name for home pantry organization
        """
        from lib.prompt_manager import get_prompt
        
        prompt = get_prompt("ingredient_categorization", ingredient_name=ingredient_name)

        try:
            response = self.llm.generate(prompt, max_tokens=50)
            category = response.strip()
            
            logger.info(
                f"Categorized ingredient",
                extra={"ingredient": ingredient_name, "category": category}
            )
            
            return category

        except LLMAPIError as e:
            logger.warning(
                f"Failed to categorize ingredient with LLM, using fallback",
                extra={"ingredient": ingredient_name, "error": str(e)}
            )
            # Fallback to simple default
            return "Other"


# Singleton instance for easy reuse
_categorizer_instance: Optional[IngredientCategorizer] = None


def get_ingredient_categorizer() -> IngredientCategorizer:
    """Get or create the singleton ingredient categorizer instance.
    
    Returns:
        IngredientCategorizer instance
    """
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = IngredientCategorizer()
    return _categorizer_instance
