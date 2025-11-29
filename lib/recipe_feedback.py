"""Recipe Feedback and Pantry Management.

Shared utilities for saving recipe feedback, managing ratings, and updating
pantry after cooking. Used by both cooking_mode.py and generate_recipes.py.

This module consolidates previously duplicated code to maintain DRY principles.
"""

from datetime import datetime
from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger
from lib.constants import (
    RATING_LOVED_THRESHOLD,
    RATING_LIKED_THRESHOLD,
    RECIPE_SOURCE_GENERATED
)

logger = get_logger(__name__)


def save_recipe_feedback(
    recipe: dict,
    rating: int,
    make_again: str,
    notes: str
) -> bool:
    """Save recipe feedback to meal history and recipe files.

    Args:
        recipe: Recipe dictionary with name, ingredients, etc.
        rating: Star rating (1-5)
        make_again: "Yes", "No", or "Maybe"
        notes: User notes

    Returns:
        True if successful, False otherwise
    """
    try:
        # 1. Add to meal history
        history_path = get_data_file_path("meal_history")
        history_content = history_path.read_text(encoding="utf-8")

        # Build meal entry
        today = datetime.now()
        date_str = today.strftime("%A, %Y-%m-%d")
        stars = "⭐" * rating

        new_entry = f"\n### {date_str}\n"
        new_entry += f"**{recipe['name']}** {stars}\n"
        new_entry += f"- Rating: {rating}/5\n"

        if notes:
            new_entry += f"- Notes: {notes}\n"

        # Add ingredients
        ingredients_list = []
        if recipe.get('ingredients_available'):
            ingredients_list.append(recipe['ingredients_available'])
        if recipe.get('ingredients_needed'):
            ingredients_list.append(recipe['ingredients_needed'])

        if ingredients_list:
            all_ingredients = ', '.join(ingredients_list)
            new_entry += f"- Ingredients used: {all_ingredients}\n"

        new_entry += "\n"

        # Find where to insert (after most recent month header or at end)
        lines = history_content.split('\n')

        # Find first month header (## November 2025)
        insert_index = -1
        for i, line in enumerate(lines):
            if line.startswith('## '):
                # Insert after this line
                insert_index = i + 1
                break

        if insert_index == -1:
            # No month header found, create one
            month_year = today.strftime("%B %Y")
            new_entry = f"\n## {month_year}\n" + new_entry
            lines.append(new_entry)
        else:
            # Insert after month header
            lines.insert(insert_index, new_entry)

        # Write back
        history_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info(
            "Saved meal to history",
            extra={"recipe_name": recipe['name'], "rating": rating}
        )

        # 2. Save to appropriate recipe file based on rating
        if rating >= RATING_LOVED_THRESHOLD:
            recipe_file = "loved_recipes"
        elif rating >= RATING_LIKED_THRESHOLD:
            recipe_file = "liked_recipes"
        else:
            recipe_file = "not_again_recipes"

        recipe_path = get_data_file_path(recipe_file)
        recipe_content = recipe_path.read_text(encoding="utf-8")

        # Build recipe entry
        recipe_entry = f"\n---\n\n"
        recipe_entry += f"## {recipe['name']}\n"
        recipe_entry += f"**Last made:** {today.strftime('%Y-%m-%d')}\n"
        recipe_entry += f"**Rating:** {rating}/5 {stars}\n"

        if recipe.get('time_minutes'):
            recipe_entry += f"**Time:** {recipe['time_minutes']} minutes\n"

        if recipe.get('difficulty'):
            recipe_entry += f"**Difficulty:** {(recipe['difficulty'] or 'unknown').title()}\n"

        recipe_entry += "\n**Ingredients:**\n"

        # Combine all ingredients
        if recipe.get('ingredients_available'):
            for item in recipe['ingredients_available'].split(','):
                recipe_entry += f"- {item.strip()}\n"

        if recipe.get('ingredients_needed'):
            for item in recipe['ingredients_needed'].split(','):
                recipe_entry += f"- {item.strip()}\n"

        if notes:
            recipe_entry += f"\n**Notes:** {notes}\n"

        if make_again:
            recipe_entry += f"\n**Make again:** {make_again}\n"

        recipe_entry += "\n"

        # Append to recipe file
        recipe_path.write_text(recipe_content + recipe_entry, encoding="utf-8")

        logger.info(
            "Saved recipe to file",
            extra={"recipe_name": recipe['name'], "file": recipe_file}
        )

        # If this was a generated recipe, remove it from generated.md now that it's been rated
        if recipe.get('source') == RECIPE_SOURCE_GENERATED:
            # Import here to avoid circular dependency
            from lib.weekly_plan_manager import remove_generated_recipe
            remove_generated_recipe(recipe['name'])

        return True

    except Exception as e:
        logger.error(
            "Failed to save recipe feedback",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False


def is_staple_ingredient(ingredient_name: str) -> bool:
    """Check if an ingredient is a staple that shouldn't be removed after one use.

    Args:
        ingredient_name: Name of the ingredient

    Returns:
        True if it's a staple (keep), False if consumable (remove)
    """
    ingredient_lower = ingredient_name.lower()

    # Staple keywords - these items are NOT removed after cooking
    staple_keywords = [
        # Oils and fats
        'oil', 'olive oil', 'vegetable oil', 'canola oil', 'sesame oil',
        'coconut oil', 'butter', 'ghee',

        # Sauces and condiments
        'soy sauce', 'tamari', 'vinegar', 'hot sauce', 'sriracha',
        'ketchup', 'mustard', 'mayo', 'mayonnaise',

        # Spices and herbs (dried)
        'salt', 'pepper', 'cumin', 'paprika', 'oregano', 'basil',
        'thyme', 'rosemary', 'cinnamon', 'ginger powder', 'garlic powder',
        'onion powder', 'chili powder', 'curry powder', 'turmeric',
        'coriander', 'cayenne', 'nutmeg', 'cloves',

        # Baking and cooking basics
        'flour', 'sugar', 'brown sugar', 'baking soda', 'baking powder',
        'yeast', 'cornstarch', 'vanilla extract',

        # Grains and pasta (dried/shelf-stable)
        'rice', 'pasta', 'noodles', 'quinoa', 'couscous', 'lentils',
        'beans', 'chickpeas',

        # Other shelf-stable items
        'stock', 'broth', 'tomato paste', 'tomato sauce', 'canned tomatoes',
        'honey', 'maple syrup', 'peanut butter', 'tahini',
    ]

    # Check if any staple keyword matches
    for keyword in staple_keywords:
        if keyword in ingredient_lower:
            return True

    return False


def update_pantry_after_cooking(recipe: dict) -> bool:
    """Update pantry by removing consumable ingredients used in recipe.

    Staples like oil, soy sauce, and spices are kept in pantry.
    Fresh items and consumables are removed.

    Args:
        recipe: Recipe dictionary with ingredients

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all ingredients from recipe
        ingredients = []

        if recipe.get('ingredients_available'):
            ingredients.extend([i.strip() for i in recipe['ingredients_available'].split(',')])

        if recipe.get('ingredients_needed'):
            ingredients.extend([i.strip() for i in recipe['ingredients_needed'].split(',')])

        if not ingredients:
            logger.warning("No ingredients to update pantry with")
            return True

        # Categorize ingredients
        items_to_remove = []
        staples_kept = []

        for ingredient in ingredients:
            if is_staple_ingredient(ingredient):
                staples_kept.append(ingredient)
            else:
                items_to_remove.append(ingredient)

        # Remove consumable items from pantry files
        removed_count = 0

        for file_name in ['staples', 'fresh']:
            file_path = get_data_file_path(file_name)
            content = file_path.read_text(encoding="utf-8")
            lines = content.split('\n')
            new_lines = []

            for line in lines:
                line_stripped = line.strip().lower()

                # Check if this line contains an ingredient to remove
                should_remove = False
                for item in items_to_remove:
                    if line_stripped.startswith('-') and item.lower() in line_stripped:
                        should_remove = True
                        removed_count += 1
                        logger.info(f"Removing from pantry: {item}")
                        break

                if not should_remove:
                    new_lines.append(line)

            # Write back
            file_path.write_text('\n'.join(new_lines), encoding="utf-8")

        # Add usage note
        today = datetime.now().strftime("%Y-%m-%d")
        note = f"\n<!-- Cooked {recipe['name']} on {today}"
        if staples_kept:
            note += f" | Staples used (not removed): {', '.join(staples_kept)}"
        if items_to_remove:
            note += f" | Removed: {', '.join(items_to_remove)}"
        note += " -->\n"

        # Add note to staples file
        staples_path = get_data_file_path("staples")
        staples_content = staples_path.read_text(encoding="utf-8")
        staples_path.write_text(staples_content + note, encoding="utf-8")

        logger.info(
            "Updated pantry after cooking",
            extra={
                "recipe_name": recipe['name'],
                "removed_count": removed_count,
                "staples_kept": len(staples_kept)
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to update pantry after cooking",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False
