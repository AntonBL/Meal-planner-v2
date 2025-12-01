"""Weekly Meal Planner Page.

Allows users to plan up to 7 meals for the week by selecting
from their saved recipes (loved and liked collections).
"""

from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from lib.active_recipe_manager import save_active_recipe
from lib.auth import require_authentication
from lib.logging_config import get_logger, setup_logging
from lib.recipe_store import get_recipe_by_id, get_recipe_by_name, load_recipes
from lib.weekly_plan_manager import (
    add_recipe_to_plan,
    clear_weekly_plan,
    load_current_plan,
    remove_meal_from_plan,
)

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
    """Load all recipes available for meal planning from recipe store.

    Returns:
        List of recipe dicts from the JSON recipe store
    """
    try:
        recipes = load_recipes()

        logger.info(
            "Loaded recipes for meal planning",
            extra={"total_recipes": len(recipes)}
        )

        return recipes

    except Exception:
        logger.error("Failed to load recipes", exc_info=True)
        st.error("❌ Could not load saved recipes")
        return []


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
                    meta.append(f"📊 {(meal['difficulty'] or 'unknown').title()}")
                if meal.get('source'):
                    meta.append(f"📚 {meal['source']}")

                if meta:
                    st.caption(" • ".join(meta))

            with col2:
                if st.button("👨‍🍳 Cook", key=f"view_{idx}", use_container_width=True):
                    # Load full recipe from recipe store by ID

                    # Try to get recipe by ID first (if available)
                    full_recipe = None
                    if meal.get('recipe_id'):
                        full_recipe = get_recipe_by_id(meal['recipe_id'])

                    # Fallback: search by name (for recipes added before migration)
                    if not full_recipe:
                        full_recipe = get_recipe_by_name(meal['name'])

                    if full_recipe:
                        # Prepare active recipe data with all necessary fields
                        active_recipe = {
                            'id': full_recipe.get('id'),
                            'name': full_recipe['name'],
                            'time_minutes': full_recipe.get('time_minutes'),
                            'difficulty': full_recipe.get('difficulty'),
                            'description': full_recipe.get('description', ''),
                            'ingredients_available': ', '.join(full_recipe.get('ingredients', [])),
                            'ingredients_needed': '',
                            'instructions': full_recipe.get('instructions', 'No instructions available'),
                            'reason': f"From your weekly plan • {full_recipe.get('source')} recipe"
                        }

                        # Save to both session state AND persistent storage
                        st.session_state['active_recipe'] = active_recipe
                        save_active_recipe(active_recipe)

                        logger.info(
                            "User started cooking from weekly plan",
                            extra={"recipe_name": meal['name'], "recipe_id": full_recipe.get('id')}
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
            source_filter = st.selectbox("Source", ["All", "Loved", "Liked", "Generated"], key="source_filter")

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
                            meta.append(f"📊 {(recipe['difficulty'] or 'unknown').title()}")

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
                            # Prepare recipe with ingredients for shopping list
                            plan_recipe = recipe.copy()

                            # Convert ingredients list to comma-separated string for shopping list
                            if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                                plan_recipe['ingredients_needed'] = ', '.join(recipe['ingredients'])

                            if add_recipe_to_plan(plan_recipe):
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
        # Calculate total cooking time
        def safe_int(value):
            """Safely convert value to int, handling strings and None."""
            if value is None:
                return 0
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        
        total_time = sum(safe_int(meal.get('time_minutes')) for meal in current_plan)
        hours = total_time // 60
        minutes = total_time % 60

        # Difficulty breakdown
        difficulty_counts = {}
        for meal in current_plan:
            diff = meal.get('difficulty') or 'unknown'
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
