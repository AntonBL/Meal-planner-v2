"""Recipe parsing utilities for extracting structured data from markdown.

Following agent.md guidelines:
- Type hints on all functions
- Docstrings with Google style
- Structured logging
- DRY principle
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def parse_recipe_section(section: str) -> Optional[dict]:
    """Parse a single recipe section from markdown.

    Args:
        section: Markdown content for one recipe (between --- separators)

    Returns:
        Dictionary with recipe data, or None if malformed

    Example:
        >>> section = "## Pasta Carbonara\\n**Time:** 30 minutes\\n"
        >>> recipe = parse_recipe_section(section)
        >>> recipe['name']
        'Pasta Carbonara'
    """
    if not section or not section.strip():
        return None

    recipe = {
        'name': None,
        'time_minutes': None,
        'difficulty': None,
        'cuisine': None,
        'rating': None,
        'last_made': None,
        'ingredients': [],
        'notes': None,
        'type': None,
        'times_made': None,
    }

    lines = section.split('\n')
    in_ingredients_section = False
    in_notes_section = False

    for _i, line in enumerate(lines):
        line_stripped = line.strip()

        # Recipe name (## header)
        if line_stripped.startswith('##'):
            name = line_stripped.replace('##', '').strip()
            # Remove star ratings if present (e.g., "Recipe ⭐⭐⭐⭐⭐")
            name = re.sub(r'\s*⭐+\s*$', '', name)
            recipe['name'] = name

        # Cuisine
        elif line_stripped.startswith('**Cuisine:**'):
            cuisine = line_stripped.replace('**Cuisine:**', '').strip()
            recipe['cuisine'] = cuisine

        # Type
        elif line_stripped.startswith('**Type:**'):
            recipe_type = line_stripped.replace('**Type:**', '').strip()
            recipe['type'] = recipe_type

        # Time
        elif line_stripped.startswith('**Time:**'):
            time_str = line_stripped.replace('**Time:**', '').strip()
            # Extract minutes: "30 minutes" or "30 min" -> 30
            match = re.search(r'(\d+)', time_str)
            if match:
                recipe['time_minutes'] = int(match.group(1))

        # Difficulty
        elif line_stripped.startswith('**Difficulty:**'):
            difficulty = line_stripped.replace('**Difficulty:**', '').strip()
            recipe['difficulty'] = difficulty.lower()

        # Rating
        elif line_stripped.startswith('**Rating:**'):
            rating_str = line_stripped.replace('**Rating:**', '').strip()
            # Extract number: "5/5" or "5/5 ⭐⭐⭐⭐⭐" -> 5
            match = re.search(r'(\d+)', rating_str)
            if match:
                recipe['rating'] = int(match.group(1))

        # Last made
        elif line_stripped.startswith('**Last made:**'):
            last_made = line_stripped.replace('**Last made:**', '').strip()
            recipe['last_made'] = last_made

        # Times made
        elif line_stripped.startswith('**Times made:**'):
            times_str = line_stripped.replace('**Times made:**', '').strip()
            match = re.search(r'(\d+)', times_str)
            if match:
                recipe['times_made'] = int(match.group(1))

        # Ingredients section start
        elif line_stripped.startswith('**Ingredients:**'):
            in_ingredients_section = True
            in_notes_section = False

        # Notes section start
        elif line_stripped.startswith('**Notes:**'):
            in_ingredients_section = False
            in_notes_section = True
            # Get notes (could be on same line or next lines)
            notes_text = line_stripped.replace('**Notes:**', '').strip()
            if notes_text:
                recipe['notes'] = notes_text

        # Ingredient line
        elif in_ingredients_section and line_stripped.startswith('-'):
            ingredient = line_stripped[1:].strip()  # Remove leading dash
            if ingredient:
                recipe['ingredients'].append(ingredient)

        # Notes continuation
        elif in_notes_section and line_stripped and not line_stripped.startswith('**'):
            if recipe['notes']:
                recipe['notes'] += ' ' + line_stripped
            else:
                recipe['notes'] = line_stripped

        # Stop collecting notes/ingredients if we hit another ** field
        elif line_stripped.startswith('**') and line_stripped != '**Ingredients:**' and line_stripped != '**Notes:**':
            in_ingredients_section = False
            in_notes_section = False

    # Only return if we at least got a name
    if recipe['name']:
        logger.debug(
            "Parsed recipe",
            extra={
                "name": recipe['name'],
                "ingredients_count": len(recipe['ingredients'])
            }
        )
        return recipe

    return None


def parse_all_recipes(content: str) -> list[dict]:
    """Parse all recipes from markdown content.

    Recipes are separated by '---' dividers in the markdown.

    Args:
        content: Full markdown file content

    Returns:
        List of recipe dictionaries

    Example:
        >>> content = load_data_file("loved_recipes")
        >>> recipes = parse_all_recipes(content)
        >>> len(recipes) > 0
        True
    """
    if not content or not content.strip():
        logger.warning("Empty content provided to parse_all_recipes")
        return []

    # Split by --- separator
    sections = content.split('---')

    recipes = []

    for section in sections:
        # Skip header sections (before first recipe)
        if not section.strip() or '##' not in section:
            continue

        recipe = parse_recipe_section(section)
        if recipe:
            recipes.append(recipe)

    logger.info(
        "Parsed recipes from markdown",
        extra={"recipes_found": len(recipes)}
    )

    return recipes


def recipe_to_markdown(recipe: dict) -> str:
    """Convert a recipe dictionary back to markdown format.

    Args:
        recipe: Recipe dictionary

    Returns:
        Markdown formatted string

    Example:
        >>> recipe = {'name': 'Test Recipe', 'time_minutes': 30}
        >>> markdown = recipe_to_markdown(recipe)
        >>> '## Test Recipe' in markdown
        True
    """
    lines = []

    # Recipe name
    if recipe.get('name'):
        lines.append(f"## {recipe['name']}")

    # Metadata
    if recipe.get('cuisine'):
        lines.append(f"**Cuisine:** {recipe['cuisine']}")

    if recipe.get('type'):
        lines.append(f"**Type:** {recipe['type']}")

    if recipe.get('time_minutes'):
        lines.append(f"**Time:** {recipe['time_minutes']} minutes")

    if recipe.get('difficulty'):
        lines.append(f"**Difficulty:** {recipe['difficulty'].title()}")

    if recipe.get('rating'):
        stars = '⭐' * recipe['rating']
        lines.append(f"**Rating:** {recipe['rating']}/5 {stars}")

    if recipe.get('last_made'):
        lines.append(f"**Last made:** {recipe['last_made']}")

    if recipe.get('times_made'):
        lines.append(f"**Times made:** {recipe['times_made']}")

    # Ingredients
    if recipe.get('ingredients'):
        lines.append("")
        lines.append("**Ingredients:**")
        for ingredient in recipe['ingredients']:
            lines.append(f"- {ingredient}")

    # Notes
    if recipe.get('notes'):
        lines.append("")
        lines.append(f"**Notes:** {recipe['notes']}")

    return '\n'.join(lines)
