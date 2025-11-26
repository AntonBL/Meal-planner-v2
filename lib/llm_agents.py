"""LLM agents for recipe generation and other AI-powered features.

Following agent.md guidelines:
- Protocol for dependency inversion
- Proper error handling with specific exceptions
- Structured logging
- Type hints and docstrings
"""

import logging
import os
from typing import Protocol

import anthropic

from lib.exceptions import LLMAPIError, RecipeParsingError
from lib.file_manager import load_context_for_recipe_generation

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers (dependency inversion principle)."""

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt."""
        ...


class ClaudeProvider:
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-3-5-sonnet-20241022)

        Raises:
            LLMAPIError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise LLMAPIError(
                "ANTHROPIC_API_KEY not found. "
                "Please set it in your .env file or pass it to the constructor."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or "claude-3-5-sonnet-20241022"

        logger.info(
            "Claude provider initialized",
            extra={"model": self.model},
        )

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Claude API.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from Claude

        Raises:
            LLMAPIError: If API call fails
        """
        logger.info(
            "Calling Claude API",
            extra={
                "model": self.model,
                "prompt_length": len(prompt),
                "max_tokens": max_tokens,
            },
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            logger.info(
                "Claude API call successful",
                extra={
                    "response_length": len(response_text),
                    "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
                },
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude API call failed",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise LLMAPIError(f"API call failed: {e}") from e


class RecipeGenerator:
    """Service for generating recipe suggestions using LLM."""

    def __init__(self, llm_provider: LLMProvider):
        """Initialize recipe generator.

        Args:
            llm_provider: LLM provider instance (dependency injection)
        """
        self.llm = llm_provider
        logger.debug("RecipeGenerator initialized")

    def suggest_recipes(
        self,
        cuisines: list[str],
        meal_type: str = "Dinner",
        num_suggestions: int = 4,
    ) -> list[dict[str, str]]:
        """Generate recipe suggestions based on available ingredients and preferences.

        Args:
            cuisines: List of preferred cuisines (e.g., ['Italian', 'Asian'])
            meal_type: Type of meal (Dinner, Lunch, Quick & Easy)
            num_suggestions: Number of recipes to suggest (default: 4)

        Returns:
            List of recipe dictionaries with keys:
            - name: Recipe name
            - description: Brief description
            - ingredients_available: List of ingredients you have
            - ingredients_needed: List of ingredients to buy
            - time_minutes: Estimated cooking time
            - difficulty: easy, medium, or hard
            - reason: Why this recipe was suggested

        Raises:
            LLMAPIError: If API call fails
            RecipeParsingError: If response cannot be parsed
            DataFileNotFoundError: If context files are missing

        Example:
            >>> generator = RecipeGenerator(ClaudeProvider())
            >>> recipes = generator.suggest_recipes(['Italian', 'Asian'])
            >>> len(recipes) == 4
            True
        """
        logger.info(
            "Starting recipe suggestion",
            extra={
                "cuisines": cuisines,
                "meal_type": meal_type,
                "num_suggestions": num_suggestions,
            },
        )

        # Load context data
        context = load_context_for_recipe_generation()

        # Build prompt
        prompt = self._build_recipe_prompt(
            cuisines=cuisines,
            meal_type=meal_type,
            num_suggestions=num_suggestions,
            context=context,
        )

        # Generate suggestions
        try:
            response = self.llm.generate(prompt, max_tokens=3000)
            recipes = self._parse_recipe_response(response)

            logger.info(
                "Recipe suggestions generated successfully",
                extra={"recipes_generated": len(recipes)},
            )

            return recipes

        except LLMAPIError:
            logger.error("Failed to generate recipes - API error")
            raise
        except RecipeParsingError:
            logger.error("Failed to parse recipe response")
            raise

    def _build_recipe_prompt(
        self,
        cuisines: list[str],
        meal_type: str,
        num_suggestions: int,
        context: dict[str, str],
    ) -> str:
        """Build LLM prompt for recipe generation.

        Args:
            cuisines: Preferred cuisines
            meal_type: Type of meal
            num_suggestions: Number of recipes to suggest
            context: Dictionary of context data from files

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful vegetarian meal planning assistant. Based on the available ingredients and user preferences below, suggest {num_suggestions} recipes.

AVAILABLE PANTRY STAPLES:
{context['staples']}

AVAILABLE FRESH ITEMS:
{context['fresh']}

USER PREFERENCES:
{context['preferences']}

FAVORITE RECIPES (for reference):
{context['loved_recipes']}

RECENT MEALS (for variety):
{context['meal_history']}

REQUEST:
- Cuisines: {', '.join(cuisines)}
- Meal type: {meal_type}

IMPORTANT REQUIREMENTS:
1. ALL RECIPES MUST BE VEGETARIAN (no meat, poultry, or fish)
2. Suggest {num_suggestions} recipes that:
   - Use mostly available ingredients (minimize shopping needs)
   - Match the requested cuisines
   - Avoid recently cooked meals (check meal history for variety)
   - Respect preferences (vegetarian diet)
   - Are appropriate for {meal_type}

3. For each recipe, provide:
   - Name and brief description (1-2 sentences)
   - List ingredients in two groups: AVAILABLE (already have) and NEEDED (must buy)
   - Estimated time in minutes
   - Difficulty (easy/medium/hard)
   - Why you're suggesting it (brief reason)

4. Format your response EXACTLY like this for EACH recipe:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
AVAILABLE: [comma-separated list of ingredients already in pantry]
NEEDED: [comma-separated list of ingredients to buy, or "None" if have everything]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
REASON: [Why suggesting this recipe]
---END---

Please provide exactly {num_suggestions} recipes in this format."""

        logger.debug(
            "Recipe prompt built",
            extra={"prompt_length": len(prompt), "cuisines": cuisines},
        )

        return prompt

    def _parse_recipe_response(self, response: str) -> list[dict[str, str]]:
        """Parse LLM response into structured recipe objects.

        Args:
            response: Raw response from LLM

        Returns:
            List of parsed recipe dictionaries

        Raises:
            RecipeParsingError: If response format is invalid
        """
        logger.debug("Parsing recipe response", extra={"response_length": len(response)})

        try:
            recipes = []
            recipe_blocks = response.split("---RECIPE---")[1:]  # Skip empty first element

            for block in recipe_blocks:
                if "---END---" not in block:
                    continue

                # Extract content before ---END---
                content = block.split("---END---")[0].strip()

                # Parse fields
                recipe: dict[str, str] = {}

                for line in content.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("NAME:"):
                        recipe["name"] = line.replace("NAME:", "").strip()
                    elif line.startswith("DESCRIPTION:"):
                        recipe["description"] = line.replace("DESCRIPTION:", "").strip()
                    elif line.startswith("AVAILABLE:"):
                        recipe["ingredients_available"] = line.replace("AVAILABLE:", "").strip()
                    elif line.startswith("NEEDED:"):
                        needed = line.replace("NEEDED:", "").strip()
                        recipe["ingredients_needed"] = needed if needed.lower() != "none" else ""
                    elif line.startswith("TIME:"):
                        recipe["time_minutes"] = line.replace("TIME:", "").strip()
                    elif line.startswith("DIFFICULTY:"):
                        recipe["difficulty"] = line.replace("DIFFICULTY:", "").strip()
                    elif line.startswith("REASON:"):
                        recipe["reason"] = line.replace("REASON:", "").strip()

                # Validate required fields
                required_fields = [
                    "name",
                    "description",
                    "ingredients_available",
                    "time_minutes",
                    "difficulty",
                ]
                if all(field in recipe for field in required_fields):
                    recipes.append(recipe)
                else:
                    logger.warning(
                        "Recipe missing required fields",
                        extra={"recipe": recipe, "missing": [f for f in required_fields if f not in recipe]},
                    )

            if not recipes:
                logger.error("No valid recipes parsed from response")
                raise RecipeParsingError(
                    "Could not parse any valid recipes from LLM response. "
                    "Response format may be incorrect."
                )

            logger.info(
                "Recipes parsed successfully",
                extra={"recipes_parsed": len(recipes)},
            )

            return recipes

        except Exception as e:
            logger.error(
                "Failed to parse recipe response",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise RecipeParsingError(f"Failed to parse recipes: {e}") from e
