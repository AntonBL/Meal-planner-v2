"""Weekly Meal Planner Page.

Allows users to plan up to 7 meals for the week by selecting
from their saved recipes (loved and liked collections).
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime
from pathlib import Path

from lib.auth import require_authentication
from lib.file_manager import load_data_file, get_data_file_path
from lib.recipe_parser import parse_all_recipes
from lib.logging_config import get_logger, setup_logging

setup_logging("INFO")
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Weekly Planner - AI Recipe Planner",
    page_icon="📅",
    layout="wide",
)

# Authentication
require_authentication()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_available_recipes() -> list[dict]:
    """Load all recipes available for meal planning.

    Returns:
        List of recipe dicts from loved and liked collections
    """
    try:
        recipes = []

        # Load loved recipes
        try:
            loved_content = load_data_file("loved_recipes")
            loved_recipes = parse_all_recipes(loved_content)
            for recipe in loved_recipes:
                recipe['source'] = 'Loved'
                recipe['source_file'] = 'loved_recipes'
                recipes.append(recipe)
        except Exception as e:
            logger.warning(f"Could not load loved recipes: {e}")

        # Load liked recipes
        try:
            liked_content = load_data_file("liked_recipes")
            liked_recipes = parse_all_recipes(liked_content)
            for recipe in liked_recipes:
                recipe['source'] = 'Liked'
                recipe['source_file'] = 'liked_recipes'
                recipes.append(recipe)
        except Exception as e:
            logger.warning(f"Could not load liked recipes: {e}")

        logger.info(
            "Loaded recipes for meal planning",
            extra={"total_recipes": len(recipes)}
        )

        return recipes

    except Exception as e:
        logger.error("Failed to load recipes", exc_info=True)
        st.error("❌ Could not load saved recipes")
        return []


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
            entry += f"**Difficulty:** {recipe['difficulty'].title()}\n"

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

        # Clear cache
        load_current_plan.clear()
        st.cache_data.clear()

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
                    plan_lines.append(f"**Difficulty:** {meal['difficulty'].title()}")
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
        st.cache_data.clear()

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
        st.cache_data.clear()

        return True

    except Exception as e:
        logger.error("Failed to clear weekly plan", exc_info=True)
        return False


# ============================================================================
# MAIN PAGE
# ============================================================================

st.title("📅 Weekly Meal Planner")
st.markdown("*Plan up to 7 meals for the week from your favorite recipes*")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📅 Current Plan", "➕ Add Meals", "📊 Overview"])

# ============================================================================
# TAB 1: CURRENT PLAN
# ============================================================================

with tab1:
    st.markdown("### Your Weekly Plan")

    current_plan = load_current_plan()

    if not current_plan:
        st.info("📭 No meals planned yet. Go to the '➕ Add Meals' tab to start planning!")
    else:
        # Header with count
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{len(current_plan)}/7 meals planned**")

        with col2:
            # Clear plan button
            if st.button("🗑️ Clear Plan", key="clear_plan_btn"):
                if st.session_state.get('confirm_clear'):
                    if clear_weekly_plan():
                        st.success("✅ Plan cleared and archived")
                        st.session_state['confirm_clear'] = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear plan")
                else:
                    st.session_state['confirm_clear'] = True
                    st.warning("⚠️ Click again to confirm")

        # Progress bar
        st.progress(len(current_plan) / 7)

        st.markdown("---")

        # Display each meal
        for idx, meal in enumerate(current_plan):
            col1, col2, col3 = st.columns([5, 1, 1])

            with col1:
                st.markdown(f"**{idx + 1}. {meal['name']}**")

                meta = []
                if meal.get('time_minutes'):
                    meta.append(f"⏱️ {meal['time_minutes']} min")
                if meal.get('difficulty'):
                    meta.append(f"📊 {meal['difficulty'].title()}")
                if meal.get('source'):
                    meta.append(f"📚 {meal['source']}")

                if meta:
                    st.caption(" • ".join(meta))

            with col2:
                if st.button("👨‍🍳 Cook", key=f"view_{idx}", use_container_width=True):
                    # Find full recipe details from loved/liked
                    available_recipes = load_available_recipes()
                    full_recipe = next((r for r in available_recipes if r['name'] == meal['name']), None)

                    if full_recipe:
                        # Set active recipe for cooking mode
                        st.session_state['active_recipe'] = {
                            'name': full_recipe['name'],
                            'time_minutes': full_recipe.get('time_minutes'),
                            'difficulty': full_recipe.get('difficulty'),
                            'description': full_recipe.get('notes', ''),
                            'ingredients_available': ', '.join(full_recipe.get('ingredients', [])),
                            'ingredients_needed': '',
                            'reason': f"From your weekly plan • {full_recipe.get('source')} recipe"
                        }

                        logger.info(
                            "User started cooking from weekly plan",
                            extra={"recipe_name": meal['name']}
                        )

                        st.switch_page("pages/cooking_mode.py")
                    else:
                        st.error("❌ Could not find recipe details")

            with col3:
                if st.button("🗑️", key=f"remove_{idx}", use_container_width=True):
                    if remove_meal_from_plan(idx):
                        st.success("✅ Removed")
                        st.rerun()
                    else:
                        st.error("❌ Failed")

            st.markdown("---")

# ============================================================================
# TAB 2: ADD MEALS
# ============================================================================

with tab2:
    st.markdown("### Add Meals to Plan")

    # Load available recipes
    available_recipes = load_available_recipes()

    # Check current plan size
    current_plan = load_current_plan()
    plan_full = len(current_plan) >= 7

    if plan_full:
        st.warning("⚠️ Your plan is full (7 meals). Remove a meal to add more.")

    if not available_recipes:
        st.info("📭 No saved recipes found. Generate and rate some recipes first!")
    else:
        # Filters
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            search = st.text_input("🔍 Search recipes", placeholder="Type to filter...", key="search_recipes")

        with col2:
            source_filter = st.selectbox("Source", ["All", "Loved", "Liked"], key="source_filter")

        with col3:
            time_filter = st.selectbox("Time", ["All", "< 30 min", "30-45 min", "> 45 min"], key="time_filter")

        # Filter recipes
        filtered = available_recipes

        if search:
            filtered = [r for r in filtered if search.lower() in r['name'].lower()]

        if source_filter != "All":
            filtered = [r for r in filtered if r['source'] == source_filter]

        if time_filter != "All":
            if time_filter == "< 30 min":
                filtered = [r for r in filtered if r.get('time_minutes') and r['time_minutes'] < 30]
            elif time_filter == "30-45 min":
                filtered = [r for r in filtered if r.get('time_minutes') and 30 <= r['time_minutes'] <= 45]
            elif time_filter == "> 45 min":
                filtered = [r for r in filtered if r.get('time_minutes') and r['time_minutes'] > 45]

        st.markdown(f"**Showing {len(filtered)} recipes**")
        st.markdown("---")

        # Display in columns (3 per row)
        cols_per_row = 3

        for i in range(0, len(filtered), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, col in enumerate(cols):
                if i + j < len(filtered):
                    recipe = filtered[i + j]

                    with col:
                        # Recipe card
                        st.markdown(f"**{recipe['name']}**")

                        # Metadata
                        if recipe.get('rating'):
                            st.caption(f"{'⭐' * recipe['rating']}")

                        meta = []
                        if recipe.get('time_minutes'):
                            meta.append(f"⏱️ {recipe['time_minutes']} min")
                        if recipe.get('difficulty'):
                            meta.append(f"📊 {recipe['difficulty'].title()}")

                        if meta:
                            st.caption(" • ".join(meta))

                        # Check if already in plan
                        in_plan = any(meal['name'] == recipe['name'] for meal in current_plan)

                        # Add button
                        if st.button(
                            "✅ In Plan" if in_plan else "➕ Add to Plan",
                            key=f"add_{recipe['name']}_{i}_{j}",
                            disabled=plan_full or in_plan,
                            use_container_width=True,
                            type="secondary" if in_plan else "primary"
                        ):
                            if add_recipe_to_plan(recipe):
                                st.success(f"✅ Added {recipe['name']}")
                                st.rerun()

                        st.markdown("")  # Spacing

# ============================================================================
# TAB 3: OVERVIEW
# ============================================================================

with tab3:
    st.markdown("### Plan Overview")

    current_plan = load_current_plan()

    if not current_plan:
        st.info("📭 No meals in your plan yet")
    else:
        # Calculate stats
        total_time = sum(meal.get('time_minutes', 0) for meal in current_plan)
        hours = total_time // 60
        minutes = total_time % 60

        # Difficulty breakdown
        difficulty_counts = {}
        for meal in current_plan:
            diff = meal.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        # Display stats
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📋 Total Meals", len(current_plan))

        with col2:
            if hours > 0:
                st.metric("⏱️ Total Cook Time", f"{hours}h {minutes}m")
            else:
                st.metric("⏱️ Total Cook Time", f"{minutes}m")

        with col3:
            avg_time = total_time // len(current_plan) if len(current_plan) > 0 else 0
            st.metric("⏱️ Avg Time/Meal", f"{avg_time} min")

        st.markdown("---")

        # Difficulty breakdown
        st.markdown("**📊 Difficulty Breakdown:**")
        for diff, count in difficulty_counts.items():
            st.markdown(f"- {diff.title()}: {count} meal{'s' if count != 1 else ''}")

        st.markdown("---")

        # Ingredients preview (would need full recipe loading)
        st.markdown("**🛒 Shopping List Preview:**")
        st.info("💡 Click '👨‍🍳 Cook' on any meal to see full ingredient list and get AI cooking assistance!")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666;">'
    "💡 <b>Tip:</b> Plan your week, then click 'Cook' on any meal to get step-by-step AI assistance!"
    "</div>",
    unsafe_allow_html=True,
)
