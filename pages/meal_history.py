"""Meal History Page - View Past Meals and Ratings.

Displays meal history from JSON storage with search and filtering.
"""

from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from lib.auth import require_authentication
from lib.history_manager import load_meal_history
from lib.logging_config import get_logger, setup_logging

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
        for meal in filtered_meals:
            stars = "⭐" * meal.get('rating', 0)
            date_str = meal.get('date', 'Unknown Date')
            
            with st.expander(
                f"**{date_str}** - {meal['name']} {stars}",
                expanded=False
            ):
                if meal.get('rating'):
                    st.markdown(f"**Rating:** {meal['rating']}/5 {stars}")

                if meal.get('notes'):
                    st.markdown(f"**Notes:** {meal['notes']}")

                if meal.get('ingredients'):
                    st.markdown("**Ingredients used:**")
                    st.caption(meal['ingredients'])

        logger.info("Meal history displayed", extra={"total_meals": len(meals), "filtered": len(filtered_meals)})

except Exception as e:
    st.error(f"❌ Error loading meal history: {str(e)}")
    logger.error("Error loading meal history", exc_info=True)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
