"""Meal History Page - View Past Meals and Ratings.

Displays meal history from JSON storage with search and filtering.
"""

from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from lib.active_recipe_manager import save_active_recipe
from lib.auth import require_authentication
from lib.history_manager import load_meal_history
from lib.logging_config import get_logger, setup_logging
from lib.recipe_store import get_recipe_by_name
from lib.weekly_plan_manager import add_recipe_to_plan

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Meal History - AI Recipe Planner",
    page_icon="📅",
    layout="wide",
)

# Authentication
require_authentication()

st.title("📅 Meal History")
st.markdown("*Your cooking journal and recipe ratings*")


# Load meal history
try:
    meals = load_meal_history()

    if not meals:
        st.info("📭 No meals logged yet. Cook a recipe and rate it to start your history!")
        logger.info("No meals found in history")
    else:
        # Stats at top
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🍽️ Total Meals", len(meals))

        with col2:
            ratings = [m['rating'] for m in meals if m.get('rating', 0) > 0]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                st.metric("⭐ Average Rating", f"{avg_rating:.1f}/5")
            else:
                st.metric("⭐ Average Rating", "N/A")

        with col3:
            five_star = sum(1 for m in meals if m.get('rating') == 5)
            st.metric("🌟 5-Star Meals", five_star)

        st.markdown("---")

        # Filter options
        col1, col2 = st.columns([2, 1])

        with col1:
            search = st.text_input(
                "🔍 Search meals",
                placeholder="Search by name or ingredients...",
                key="search_meals"
            )

        with col2:
            min_rating = st.selectbox(
                "Filter by rating",
                ["All", "5 stars", "4+ stars", "3+ stars"]
            )

        # Filter meals
        filtered_meals = meals

        if search:
            search_lower = search.lower()
            filtered_meals = [
                m for m in filtered_meals
                if (search_lower in (m.get('name') or '').lower()
                    or search_lower in (m.get('ingredients') or '').lower()
                    or search_lower in (m.get('notes') or '').lower())
            ]

        if min_rating != "All":
            rating_map = {"5 stars": 5, "4+ stars": 4, "3+ stars": 3}
            min_val = rating_map[min_rating]
            filtered_meals = [m for m in filtered_meals if m.get('rating', 0) >= min_val]

        st.markdown(f"### Showing {len(filtered_meals)} of {len(meals)} meals")

        # Display meals
        for idx, meal in enumerate(filtered_meals):
            stars = "⭐" * meal.get('rating', 0)
            date_str = meal.get('date', 'Unknown Date')

            with st.expander(
                f"**{date_str}** - {meal['name']} {stars}",
                expanded=False
            ):
                # Try to look up full recipe details
                recipe_name = meal['name'].strip().rstrip('*')  # Remove trailing asterisks if any
                full_recipe = get_recipe_by_name(recipe_name)

                if meal.get('rating'):
                    st.markdown(f"**Rating:** {meal['rating']}/5 {stars}")

                if meal.get('notes'):
                    st.markdown(f"**Notes:** {meal['notes']}")

                # Display recipe description if available
                if full_recipe and full_recipe.get('description'):
                    st.markdown(f"**Description:** {full_recipe['description']}")

                # Display time and difficulty if available
                if full_recipe:
                    col1, col2 = st.columns(2)
                    with col1:
                        if full_recipe.get('time_minutes'):
                            st.markdown(f"⏱️ **Time:** {full_recipe['time_minutes']} min")
                    with col2:
                        if full_recipe.get('difficulty'):
                            st.markdown(f"📊 **Difficulty:** {full_recipe['difficulty'].title()}")

                if meal.get('ingredients'):
                    st.markdown("**Ingredients used:**")
                    st.caption(meal['ingredients'])

                # Display cooking instructions if available
                if full_recipe and full_recipe.get('instructions'):
                    st.markdown("---")
                    st.markdown("### 👨‍🍳 Cooking Instructions")
                    st.markdown(full_recipe['instructions'])

                # Action buttons
                st.markdown("---")
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    # Add to weekly plan button
                    if st.button(
                        "📅 Add to Weekly Plan",
                        key=f"add_plan_{idx}_{meal['name'][:20]}",
                        use_container_width=True
                    ):
                        if full_recipe:
                            if add_recipe_to_plan(full_recipe):
                                st.success("✅ Added to weekly plan!")
                                logger.info(
                                    "Added meal from history to weekly plan",
                                    extra={"meal_name": meal['name']}
                                )
                        else:
                            st.warning("⚠️ Could not find full recipe details. Please try from the recipe generator.")
                            logger.warning(f"Could not find recipe for: {recipe_name}")

                with btn_col2:
                    # Cook this button
                    if st.button(
                        "👨‍🍳 Cook This",
                        key=f"cook_{idx}_{meal['name'][:20]}",
                        use_container_width=True,
                        type="primary"
                    ):
                        if full_recipe:
                            # Save as active recipe
                            st.session_state['active_recipe'] = full_recipe
                            save_active_recipe(full_recipe)
                            logger.info(
                                "Started cooking mode from meal history",
                                extra={"recipe_name": full_recipe['name']}
                            )
                            st.switch_page("pages/cooking_mode.py")
                        else:
                            st.warning("⚠️ Could not find full recipe details. Please try from the recipe generator.")
                            logger.warning(f"Could not find recipe for: {recipe_name}")

                with btn_col3:
                    # View full recipe (placeholder for future feature)
                    if full_recipe:
                        st.caption(f"Source: {full_recipe.get('source', 'Unknown')}")

        logger.info("Meal history displayed", extra={"total_meals": len(meals), "filtered": len(filtered_meals)})

except Exception as e:
    st.error(f"❌ Error loading meal history: {str(e)}")
    logger.error("Error loading meal history", exc_info=True)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
