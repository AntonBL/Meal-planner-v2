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
            model: Model to use (default: claude-haiku-4-5)

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
        self.model = model or "claude-haiku-4-5"

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
        additional_context: str | None = None,
    ) -> list[dict[str, str]]:
        """Generate recipe suggestions based on available ingredients and preferences.

        Args:
            cuisines: List of preferred cuisines (e.g., ['Italian', 'Asian'])
            meal_type: Type of meal (Dinner, Lunch, Quick & Easy)
            num_suggestions: Number of recipes to suggest (default: 4)
            additional_context: Optional free-form text with extra preferences (e.g., "spicy", "low carb")

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
            additional_context=additional_context,
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
        additional_context: str | None = None,
    ) -> str:
        """Build LLM prompt for recipe generation.

        Args:
            cuisines: Preferred cuisines
            meal_type: Type of meal
            num_suggestions: Number of recipes to suggest
            context: Dictionary of context data from files
            additional_context: Optional free-form text with extra preferences

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
- Meal type: {meal_type}{f"""
- Additional preferences: {additional_context}""" if additional_context else ""}

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
   - Step-by-step cooking instructions (clear and concise)
   - Why you're suggesting it (brief reason)

4. Format your response EXACTLY like this for EACH recipe:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
AVAILABLE: [comma-separated list of ingredients already in pantry]
NEEDED: [comma-separated list of ingredients to buy, or "None" if have everything]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INSTRUCTIONS:
1. [First step]
2. [Second step]
3. [Third step]
[Continue with all steps needed]
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
                instructions_lines = []
                in_instructions = False

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
                    elif line.startswith("INSTRUCTIONS:"):
                        in_instructions = True
                        # Continue to collect instruction lines
                    elif line.startswith("REASON:"):
                        in_instructions = False
                        recipe["reason"] = line.replace("REASON:", "").strip()
                    elif in_instructions:
                        # Collect instruction lines
                        instructions_lines.append(line)

                # Join instructions into a single string
                if instructions_lines:
                    recipe["instructions"] = "\n".join(instructions_lines)

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

    def refine_recipe(
        self,
        recipe: dict[str, str],
        user_message: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict[str, str]:
        """Refine a recipe based on user feedback via chat.

        Args:
            recipe: The current recipe dictionary
            user_message: New message from user (e.g., "make this less spicy")
            chat_history: Previous chat messages for this recipe (optional)

        Returns:
            Updated recipe dictionary

        Raises:
            LLMAPIError: If API call fails
            RecipeParsingError: If response cannot be parsed
        """
        logger.info(
            "Refining recipe via chat",
            extra={"recipe_name": recipe.get("name"), "message": user_message},
        )

        # Build conversation history
        if chat_history is None:
            chat_history = []

        # Build prompt
        prompt = self._build_refinement_prompt(recipe, user_message, chat_history)

        # Generate refinement
        try:
            response = self.llm.generate(prompt, max_tokens=2000)
            updated_recipe = self._parse_single_recipe(response)

            # Preserve recipe ID if it exists
            if "id" in recipe:
                updated_recipe["id"] = recipe["id"]

            logger.info(
                "Recipe refined successfully",
                extra={"recipe_name": updated_recipe.get("name")},
            )

            return updated_recipe

        except LLMAPIError:
            logger.error("Failed to refine recipe - API error")
            raise
        except RecipeParsingError:
            logger.error("Failed to parse refined recipe response")
            raise

    def _build_refinement_prompt(
        self,
        recipe: dict[str, str],
        user_message: str,
        chat_history: list[dict[str, str]],
    ) -> str:
        """Build prompt for recipe refinement.

        Args:
            recipe: Current recipe
            user_message: New user message
            chat_history: Previous chat messages

        Returns:
            Formatted prompt string
        """
        # Build conversation context
        conversation = ""
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation += f"{role.upper()}: {content}\n"

        prompt = f"""You are helping refine a recipe based on user feedback. The user wants to adjust the recipe below.

CURRENT RECIPE:
Name: {recipe.get('name', 'Unknown')}
Description: {recipe.get('description', '')}
Available Ingredients: {recipe.get('ingredients_available', '')}
Needed Ingredients: {recipe.get('ingredients_needed', '')}
Time: {recipe.get('time_minutes', '')} minutes
Difficulty: {recipe.get('difficulty', '')}
Instructions:
{recipe.get('instructions', '')}

{f'''PREVIOUS CONVERSATION:
{conversation}''' if conversation else ''}

USER REQUEST:
{user_message}

INSTRUCTIONS:
1. Modify the recipe according to the user's request
2. Keep it VEGETARIAN (no meat, poultry, or fish)
3. Update all relevant fields (ingredients, instructions, time, etc.)
4. Maintain the same quality and clarity

Format your response EXACTLY like this:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
AVAILABLE: [comma-separated list of ingredients already in pantry]
NEEDED: [comma-separated list of ingredients to buy, or "None" if have everything]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INSTRUCTIONS:
1. [First step]
2. [Second step]
3. [Third step]
[Continue with all steps needed]
REASON: [Brief note about the changes made based on user request]
---END---

Provide exactly ONE recipe in this format."""

        return prompt

    def _parse_single_recipe(self, response: str) -> dict[str, str]:
        """Parse a single recipe from LLM response.

        Args:
            response: Raw response from LLM

        Returns:
            Parsed recipe dictionary

        Raises:
            RecipeParsingError: If response format is invalid
        """
        logger.debug("Parsing single recipe response", extra={"response_length": len(response)})

        try:
            # Use existing parsing logic but expect only one recipe
            if "---RECIPE---" not in response or "---END---" not in response:
                raise RecipeParsingError("Response missing recipe markers")

            # Extract content between markers
            start = response.find("---RECIPE---") + len("---RECIPE---")
            end = response.find("---END---")
            content = response[start:end].strip()

            # Parse fields
            recipe: dict[str, str] = {}
            instructions_lines = []
            in_instructions = False

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
                elif line.startswith("INSTRUCTIONS:"):
                    in_instructions = True
                elif line.startswith("REASON:"):
                    in_instructions = False
                    recipe["reason"] = line.replace("REASON:", "").strip()
                elif in_instructions:
                    instructions_lines.append(line)

            # Join instructions
            if instructions_lines:
                recipe["instructions"] = "\n".join(instructions_lines)

            # Validate required fields
            required_fields = ["name", "description", "ingredients_available", "time_minutes", "difficulty"]
            if not all(field in recipe for field in required_fields):
                missing = [f for f in required_fields if f not in recipe]
                raise RecipeParsingError(f"Recipe missing required fields: {missing}")

            return recipe

        except Exception as e:
            logger.error(
                "Failed to parse single recipe",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise RecipeParsingError(f"Failed to parse recipe: {e}") from e
