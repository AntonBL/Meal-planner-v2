"""Weekly Plan Management Functions.

Shared functions for managing the weekly meal plan.
"""

from datetime import datetime
from pathlib import Path
import streamlit as st

from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger

logger = get_logger(__name__)


def load_current_plan() -> list[dict]:
    """Load the current weekly meal plan.

    Returns:
        List of meal dictionaries from the current plan
    """
    try:
        plan_path = get_data_file_path("weekly_plan")
        content = plan_path.read_text(encoding="utf-8")

        # Parse meals from Current Plan section
        lines = content.split('\n')
        meals = []
        current_meal = None
        in_current_plan = False

        for line in lines:
            # Start of current plan section
            if line.startswith('## Current Plan'):
                in_current_plan = True
                continue

            # End of current plan section
            if in_current_plan and line.startswith('## '):
                break

            # Skip empty state message
            if in_current_plan and line.strip().startswith('*No meals'):
                continue

            # Meal entry (### 1. Recipe Name)
            if in_current_plan and line.startswith('###'):
                # Save previous meal if exists
                if current_meal and current_meal.get('name'):
                    meals.append(current_meal)

                # Start new meal
                meal_line = line.replace('###', '').strip()
                # Remove leading number (e.g., "1. Recipe" -> "Recipe")
                name = meal_line.split('.', 1)[-1].strip()

                current_meal = {
                    'name': name,
                    'source': None,
                    'time_minutes': None,
                    'difficulty': None,
                    'added': None,
                }

            # Parse meal metadata
            elif in_current_plan and current_meal and line.startswith('**'):
                if '**Source:**' in line:
                    current_meal['source'] = line.replace('**Source:**', '').strip()
                elif '**Time:**' in line:
                    time_str = line.replace('**Time:**', '').strip()
                    import re
                    match = re.search(r'(\d+)', time_str)
                    if match:
                        current_meal['time_minutes'] = int(match.group(1))
                elif '**Difficulty:**' in line:
                    current_meal['difficulty'] = line.replace('**Difficulty:**', '').strip().lower()
                elif '**Added:**' in line:
                    current_meal['added'] = line.replace('**Added:**', '').strip()

        # Don't forget last meal
        if current_meal and current_meal.get('name'):
            meals.append(current_meal)

        logger.info(
            "Loaded current meal plan",
            extra={"meals_count": len(meals)}
        )

        return meals

    except Exception as e:
        logger.error("Failed to load current plan", exc_info=True)
        return []


def add_recipe_to_plan(recipe: dict) -> bool:
    """Add a recipe to the weekly meal plan.

    Args:
        recipe: Recipe dictionary with name, time, difficulty, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load current plan
        current_plan = load_current_plan()

        # Check if plan is full
        if len(current_plan) >= 7:
            logger.warning("Cannot add recipe - plan is full")
            st.warning("⚠️ Your plan is full (7 meals). Remove a meal first.")
            return False

        # Check if recipe already in plan
        if any(meal['name'] == recipe['name'] for meal in current_plan):
            st.info(f"ℹ️ {recipe['name']} is already in your plan")
            return False

        # Load file
        plan_path = get_data_file_path("weekly_plan")
        content = plan_path.read_text(encoding="utf-8")

        # Build entry
        meal_number = len(current_plan) + 1
        entry = f"\n### {meal_number}. {recipe['name']}\n"
        entry += f"**Source:** {recipe.get('source', 'Unknown')}\n"

        if recipe.get('time_minutes'):
            entry += f"**Time:** {recipe['time_minutes']} minutes\n"

        if recipe.get('difficulty'):
            entry += f"**Difficulty:** {(recipe['difficulty'] or 'unknown').title()}\n"

        entry += f"**Added:** {datetime.now().strftime('%Y-%m-%d')}\n"

        # Find insertion point (after "## Current Plan" line)
        lines = content.split('\n')
        insert_index = -1

        for i, line in enumerate(lines):
            if line.startswith('## Current Plan'):
                # Skip to after empty state message if present
                insert_index = i + 1
                # Remove empty state message if this is the first meal
                if len(current_plan) == 0:
                    # Look for the "*No meals*" line and skip past it
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip().startswith('*No meals'):
                            insert_index = j + 1
                            # Remove the empty state line
                            lines[j] = ''
                            break
                break

        if insert_index == -1:
            logger.error("Could not find insertion point in weekly plan")
            return False

        # Insert entry
        lines.insert(insert_index, entry)

        # Write back
        plan_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info(
            "Added recipe to weekly plan",
            extra={"recipe_name": recipe['name'], "plan_size": len(current_plan) + 1}
        )

        # Clear Streamlit cache if available
        try:
            st.cache_data.clear()
        except:
            pass

        return True

    except Exception as e:
        logger.error("Failed to add recipe to plan", exc_info=True)
        return False


def remove_meal_from_plan(index: int) -> bool:
    """Remove a meal from the weekly plan.

    Args:
        index: Index of meal to remove (0-based)

    Returns:
        True if successful, False otherwise
    """
    try:
        current_plan = load_current_plan()

        if index < 0 or index >= len(current_plan):
            logger.error(f"Invalid index: {index}")
            return False

        # Remove the meal
        removed_meal = current_plan.pop(index)

        # Rebuild the plan section
        plan_lines = []

        if len(current_plan) == 0:
            # Empty state
            plan_lines.append("## Current Plan")
            plan_lines.append("")
            plan_lines.append("*No meals planned yet. Click \"Add Meal\" to start planning!*")
        else:
            plan_lines.append("## Current Plan")
            plan_lines.append("")

            # Add remaining meals with renumbered indices
            for i, meal in enumerate(current_plan, 1):
                plan_lines.append(f"### {i}. {meal['name']}")
                if meal.get('source'):
                    plan_lines.append(f"**Source:** {meal['source']}")
                if meal.get('time_minutes'):
                    plan_lines.append(f"**Time:** {meal['time_minutes']} minutes")
                if meal.get('difficulty'):
                    plan_lines.append(f"**Difficulty:** {(meal['difficulty'] or 'unknown').title()}")
                if meal.get('added'):
                    plan_lines.append(f"**Added:** {meal['added']}")
                plan_lines.append("")

        # Load full file
        plan_path = get_data_file_path("weekly_plan")
        content = plan_path.read_text(encoding="utf-8")
        lines = content.split('\n')

        # Find and replace Current Plan section
        start_idx = -1
        end_idx = -1

        for i, line in enumerate(lines):
            if line.startswith('## Current Plan'):
                start_idx = i
            elif start_idx != -1 and line.startswith('## ') and i > start_idx:
                end_idx = i
                break

        if start_idx == -1:
            logger.error("Could not find Current Plan section")
            return False

        # If no end found, replace to end of file
        if end_idx == -1:
            end_idx = len(lines)

        # Replace section
        new_lines = lines[:start_idx] + plan_lines + lines[end_idx:]

        # Write back
        plan_path.write_text('\n'.join(new_lines), encoding="utf-8")

        logger.info(
            "Removed meal from plan",
            extra={"meal_name": removed_meal['name'], "new_plan_size": len(current_plan)}
        )

        # Clear cache
        try:
            st.cache_data.clear()
        except:
            pass

        return True

    except Exception as e:
        logger.error("Failed to remove meal from plan", exc_info=True)
        return False


def clear_weekly_plan() -> bool:
    """Clear the entire weekly plan (with archiving to history).

    Returns:
        True if successful, False otherwise
    """
    try:
        current_plan = load_current_plan()

        if len(current_plan) == 0:
            st.info("ℹ️ Plan is already empty")
            return True

        # Load file
        plan_path = get_data_file_path("weekly_plan")
        content = plan_path.read_text(encoding="utf-8")
        lines = content.split('\n')

        # Build archive entry
        week_of = datetime.now().strftime("%Y-%m-%d")
        archive = [f"\n### Week of {week_of}"]

        for meal in current_plan:
            archive.append(f"- {meal['name']}")

        archive.append("")

        # Find Plan History section
        history_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('## Plan History'):
                history_idx = i + 1
                break

        if history_idx != -1:
            # Insert archive after Plan History header
            # Skip any existing comment
            while history_idx < len(lines) and lines[history_idx].strip().startswith('<!--'):
                history_idx += 1

            for archive_line in reversed(archive):
                lines.insert(history_idx, archive_line)

        # Replace Current Plan section with empty state
        start_idx = -1
        end_idx = -1

        for i, line in enumerate(lines):
            if line.startswith('## Current Plan'):
                start_idx = i
            elif start_idx != -1 and line.startswith('## ') and i > start_idx:
                end_idx = i
                break

        if start_idx != -1:
            empty_plan = [
                "## Current Plan",
                "",
                "*No meals planned yet. Click \"Add Meal\" to start planning!*",
                ""
            ]

            if end_idx == -1:
                end_idx = len(lines)

            lines = lines[:start_idx] + empty_plan + lines[end_idx:]

        # Update last updated
        for i, line in enumerate(lines):
            if line.startswith('Last updated:'):
                lines[i] = f"Last updated: {datetime.now().strftime('%Y-%m-%d')}"
                break

        # Write back
        plan_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info("Cleared weekly plan and archived to history")

        # Clear cache
        try:
            st.cache_data.clear()
        except:
            pass

        return True

    except Exception as e:
        logger.error("Failed to clear weekly plan", exc_info=True)
        return False
