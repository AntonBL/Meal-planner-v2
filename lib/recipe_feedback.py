"""Recipe Feedback and Pantry Management.

Shared utilities for saving recipe feedback, managing ratings, and updating
pantry after cooking. Used by both cooking_mode.py and generate_recipes.py.

This module consolidates previously duplicated code to maintain DRY principles.
"""

from datetime import datetime

from lib.constants import RATING_LIKED_THRESHOLD, RATING_LOVED_THRESHOLD, RECIPE_SOURCE_GENERATED
from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger

logger = get_logger(__name__)


from lib.history_manager import add_meal_to_history
from lib.pantry_manager import load_pantry_items, remove_pantry_item
from lib.recipe_store import get_recipe_by_id, save_recipe


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
        today = datetime.now()
        date_str = today.strftime("%A, %Y-%m-%d")
        
        # Prepare ingredients string using unified schema
        from lib.ingredient_schema import from_legacy_recipe, to_comma_separated

        canonical_ingredients = from_legacy_recipe(recipe)
        all_ingredients = to_comma_separated(canonical_ingredients) if canonical_ingredients else None

        meal_entry = {
            "date": date_str,
            "name": recipe['name'],
            "rating": rating,
            "notes": notes,
            "ingredients": all_ingredients
        }
        
        add_meal_to_history(meal_entry)

        # 2. Save to appropriate recipe file based on rating (Legacy support or update JSON stats)
        # We already update JSON stats in cooking_mode.py via update_recipe_stats
        # But we might want to update the recipe object itself with rating/notes if we want to persist that
        # For now, let's assume update_recipe_stats handles the core stats.
        # If we want to save "loved/liked" status, we should update the recipe in the store.
        
        if recipe.get('id'):
            full_recipe = get_recipe_by_id(recipe['id'])
            if full_recipe:
                full_recipe['rating'] = rating
                full_recipe['last_cooked'] = today.strftime('%Y-%m-%d')
                # We could append notes to description or a notes field
                save_recipe(full_recipe)

        # If this was a generated recipe, we don't need to do anything special anymore
        # as generated recipes are now saved directly to the main recipe store.
        
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
    return any(keyword in ingredient_lower for keyword in staple_keywords)


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
        # Get all ingredients from recipe using unified schema
        from lib.ingredient_schema import from_legacy_recipe, to_string_list

        canonical_ingredients = from_legacy_recipe(recipe)

        if not canonical_ingredients:
            logger.warning(
                "No ingredients to update pantry with",
                extra={"recipe_name": recipe.get('name'), "recipe_keys": list(recipe.keys())}
            )
            return True

        # Convert to simple string list for processing
        ingredients = to_string_list(canonical_ingredients)

        # Categorize ingredients
        items_to_remove = []
        staples_kept = []

        for ingredient in ingredients:
            if is_staple_ingredient(ingredient):
                staples_kept.append(ingredient)
            else:
                items_to_remove.append(ingredient)

        # Remove consumable items from pantry
        removed_count = 0
        current_pantry_items = load_pantry_items()
        
        for item_to_remove in items_to_remove:
            # Find matching items in pantry
            # Simple substring match for now
            matches = [
                i for i in current_pantry_items 
                if item_to_remove.lower() in i['name'].lower() or i['name'].lower() in item_to_remove.lower()
            ]
            
            for match in matches:
                if remove_pantry_item(match['id']):
                    removed_count += 1
                    logger.info(f"Removed from pantry: {match['name']}")

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
