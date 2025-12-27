"""Prompt Manager - Centralized LLM prompt storage and management.

This module manages all LLM prompts used throughout the application,
allowing users to customize them without editing code.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)

# Default prompts
DEFAULT_PROMPTS = {
    "recipe_generation": """You are a helpful vegetarian meal planning assistant. Based on the available ingredients and user preferences below, suggest {num_suggestions} recipes.

AVAILABLE PANTRY STAPLES:
{staples}

AVAILABLE FRESH ITEMS:
{fresh}

USER PREFERENCES:
{preferences}

FAVORITE RECIPES (for reference):
{loved_recipes}

RECENT MEALS (for variety):
{meal_history}

REQUEST:
- Cuisines: {cuisines}
- Meal type: {meal_type}
{additional_context}

IMPORTANT REQUIREMENTS:
1. ALL RECIPES MUST BE VEGETARIAN (no meat, poultry, or fish)
2. ASSUME the pantry is well-stocked with:
   - All common oils (olive oil, vegetable oil, sesame oil, etc.)
   - All common vinegars (balsamic, rice, apple cider, etc.)
   - All common spices and seasonings (salt, pepper, cumin, paprika, etc.)
   - All common sauces and condiments (soy sauce, hot sauce, ketchup, mustard, etc.)
   - If a specific oil/vinegar/spice/sauce is needed, assume it's available or can be substituted
3. Suggest {num_suggestions} recipes that:
   - Use mostly available fresh ingredients (minimize shopping needs)
   - Match the requested cuisines
   - Avoid recently cooked meals (check meal history for variety)
   - Are appropriate for {meal_type}

4. For each recipe, provide:
   - Name and brief description (1-2 sentences)
   - List ALL ingredients with quantities in two groups:
     * AVAILABLE: Fresh ingredients already in pantry (from the lists above) WITH FULL QUANTITIES
     * NEEDED: Fresh ingredients to buy WITH FULL QUANTITIES (DO NOT include oils, vinegars, spices, sauces, or condiments)
   - Estimated time in minutes
   - Difficulty (easy/medium/hard)
   - Step-by-step cooking instructions (clear and concise) with amounts and timing
   - Why you're suggesting it (brief reason)

5. INGREDIENT FORMAT REQUIREMENTS:
   - ALWAYS include the quantity and unit (e.g., "2 cups", "1 lb", "3 cloves")
   - Be specific with measurements (not "some spinach" but "2 cups fresh spinach")
   - Include modifiers when relevant (e.g., "diced", "fresh", "chopped")
   - Format: "[quantity] [unit] [modifier] [ingredient name]"
   - Examples: "2 cups fresh spinach", "1 lb tomatoes (diced)", "3 cloves garlic"

6. Format your response EXACTLY like this for EACH recipe:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
AVAILABLE: [comma-separated list of FRESH ingredients WITH QUANTITIES already in pantry, e.g., "2 cups spinach, 1 onion"]
NEEDED: [comma-separated list of FRESH ingredients WITH QUANTITIES to buy, or "None" if have everything, e.g., "1 lb tomatoes, 2 bell peppers"]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INSTRUCTIONS:
1. [First step with specific quantities and timing]
2. [Second step with specific quantities and timing]
3. [Third step with specific quantities and timing]
[Continue with all steps needed]
REASON: [Why suggesting this recipe]
---END---

Please provide exactly {num_suggestions} recipes in this format.""",

    "recipe_refinement": """You are helping refine a recipe based on user feedback. The user wants to adjust the recipe below.

CURRENT RECIPE:
Name: {recipe_name}
Description: {recipe_description}
Available Ingredients: {ingredients_available}
Needed Ingredients: {ingredients_needed}
Time: {time_minutes} minutes
Difficulty: {difficulty}
Instructions:
{instructions}

{conversation_history}

USER REQUEST:
{user_message}

INSTRUCTIONS:
1. Modify the recipe according to the user's request
2. Keep it VEGETARIAN (no meat, poultry, or fish)
3. Update all relevant fields (ingredients, instructions, time, etc.)
4. Maintain the same quality and clarity
5. ALWAYS include quantities and units for ALL ingredients (e.g., "2 cups", "1 lb", "3 cloves")
6. Be specific with measurements - never vague quantities
7. Format ingredients as: "[quantity] [unit] [modifier] [ingredient name]"

Format your response EXACTLY like this:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
AVAILABLE: [comma-separated list of ingredients WITH QUANTITIES already in pantry, e.g., "2 cups spinach, 1 onion"]
NEEDED: [comma-separated list of ingredients WITH QUANTITIES to buy, or "None", e.g., "1 lb tomatoes, 2 bell peppers"]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INSTRUCTIONS:
1. [First step with specific quantities and timing]
2. [Second step with specific quantities and timing]
3. [Third step with specific quantities and timing]
[Continue with all steps needed]
REASON: [Brief note about the changes made based on user request]
---END---

Provide exactly ONE recipe in this format.""",

    "recipe_chat": """You are a helpful cooking assistant discussing recipe modifications with a user. The user is looking at this recipe:

RECIPE: {recipe_name}
DESCRIPTION: {recipe_description}
TIME: {time_minutes} minutes
DIFFICULTY: {difficulty}

{conversation_history}

USER MESSAGE:
{user_message}

INSTRUCTIONS:
1. Respond conversationally to the user's request about modifying the recipe
2. Acknowledge what changes they want to make
3. Discuss feasibility, suggest alternatives if needed, or confirm it sounds good
4. At the end of your response, remind them: "When you're ready, click the 'Update Recipe' button to apply these changes!"
5. Keep responses concise (2-3 sentences max)
6. Be friendly and encouraging

Respond naturally as a cooking assistant:""",

    "ingredient_categorization": """Categorize this ingredient into ONE of these categories for a home pantry:

FRESH ITEMS (need to buy regularly):
- Fresh Produce (fruits, vegetables, fresh herbs, salad greens)
- Dairy & Eggs (milk, cheese, yogurt, butter, eggs, cream)
- Proteins (tofu, tempeh, plant-based alternatives)

PANTRY STAPLES (buy occasionally):
- Grains & Pasta (rice, quinoa, pasta, noodles, couscous, bread)
- Baking Supplies (flour, sugar, baking powder, yeast, cocoa)
- Canned & Dried (canned beans, tomatoes, dried beans, lentils, nuts, seeds)
- Snacks (chips, crackers, cookies, granola bars)

FROZEN:
- Frozen Foods (frozen vegetables, meals, ice cream, frozen fruit)

BEVERAGES:
- Beverages (water, juice, soda, coffee, tea, wine, beer)

OTHER:
- Other (anything else)

NOTE: Assume oils, vinegars, spices, seasonings, sauces, and condiments are already stocked.
If the ingredient is one of these, categorize as "Other" since it doesn't need to be on the shopping list.

Ingredient: {ingredient_name}

Respond with ONLY the category name exactly as shown above, nothing else."""
}


def _get_prompts_path() -> Path:
    """Get the path to the prompts JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "prompts.json"


def load_prompts() -> Dict[str, str]:
    """Load prompts from JSON storage.
    
    Returns:
        Dictionary of prompt templates
    """
    try:
        prompts_path = _get_prompts_path()
        
        if not prompts_path.exists():
            logger.info("Prompts file doesn't exist, creating with defaults")
            save_prompts(DEFAULT_PROMPTS)
            return DEFAULT_PROMPTS.copy()
        
        with open(prompts_path, encoding='utf-8') as f:
            data = json.load(f)
        
        prompts = {k: v for k, v in data.items() if k != 'last_updated'}
        logger.info(f"Loaded {len(prompts)} prompts from JSON")
        return prompts
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse prompts JSON: {e}", exc_info=True)
        return DEFAULT_PROMPTS.copy()
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}", exc_info=True)
        return DEFAULT_PROMPTS.copy()


def save_prompts(prompts: Dict[str, str]) -> bool:
    """Save prompts to JSON storage.
    
    Args:
        prompts: Dictionary of prompt templates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        prompts_path = _get_prompts_path()
        prompts_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            **prompts,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(prompts_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(prompts)} prompts to JSON")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save prompts: {e}", exc_info=True)
        return False


def get_prompt(prompt_name: str, **kwargs) -> str:
    """Get a prompt template and render it with variables.
    
    Args:
        prompt_name: Name of the prompt to retrieve
        **kwargs: Variables to substitute in the template
        
    Returns:
        Rendered prompt string
    """
    prompts = load_prompts()
    template = prompts.get(prompt_name, DEFAULT_PROMPTS.get(prompt_name, ""))
    
    if not template:
        logger.warning(f"Prompt '{prompt_name}' not found")
        return ""
    
    try:
        # Simple string formatting
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing variable in prompt '{prompt_name}': {e}")
        return template
    except Exception as e:
        logger.error(f"Failed to render prompt '{prompt_name}': {e}")
        return template


def reset_to_defaults() -> bool:
    """Reset all prompts to default values.
    
    Returns:
        True if successful, False otherwise
    """
    return save_prompts(DEFAULT_PROMPTS)


def get_prompt_variables(prompt_name: str) -> list[str]:
    """Get list of variables used in a prompt template.
    
    Args:
        prompt_name: Name of the prompt
        
    Returns:
        List of variable names
    """
    import re
    
    prompts = load_prompts()
    template = prompts.get(prompt_name, DEFAULT_PROMPTS.get(prompt_name, ""))
    
    # Find all {variable} patterns
    variables = re.findall(r'\{(\w+)\}', template)
    return list(set(variables))
