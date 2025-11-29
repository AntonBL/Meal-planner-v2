"""Meal History Page - View Past Meals and Ratings.

Displays meal history from markdown file with search and filtering.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime

from lib.auth import require_authentication
from lib.file_manager import load_data_file
from lib.exceptions import DataFileNotFoundError
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


def parse_meal_history(content: str) -> list[dict]:
    """Parse meal history markdown into structured data.

    Args:
        content: Meal history markdown content

    Returns:
        List of meals with date, name, rating, notes, ingredients
    """
    meals = []
    lines = content.split('\n')
    current_meal = None

    for line in lines:
        line = line.strip()

        # Date header (### Day, Date)
        if line.startswith('###'):
            # Save previous meal if exists
            if current_meal and current_meal.get('name'):
                meals.append(current_meal)

            # Start new meal
            date_str = line.replace('###', '').strip()
            current_meal = {
                'date': date_str,
                'name': None,
                'rating': 0,
                'stars': '',
                'notes': None,
                'ingredients': None
            }

        # Recipe name (usually has stars)
        elif current_meal and not current_meal['name'] and '⭐' in line:
            parts = line.split('⭐')
            current_meal['name'] = parts[0].strip('*').strip()
            current_meal['stars'] = '⭐' * (len(parts) - 1)
            current_meal['rating'] = len(parts) - 1

        # Alternative: Recipe name without stars (bold markdown)
        elif current_meal and not current_meal['name'] and line.startswith('**') and line.endswith('**'):
            current_meal['name'] = line.strip('*').strip()

        # Rating line
        elif line.startswith('- Rating:'):
            if current_meal:
                rating_str = line.replace('- Rating:', '').strip()
                if '/' in rating_str:
                    try:
                        current_meal['rating'] = int(rating_str.split('/')[0])
                        current_meal['stars'] = '⭐' * current_meal['rating']
                    except:
                        pass

        # Notes line
        elif line.startswith('- Notes:'):
            if current_meal:
                current_meal['notes'] = line.replace('- Notes:', '').strip()

        # Ingredients line
        elif line.startswith('- Ingredients used:'):
            if current_meal:
                current_meal['ingredients'] = line.replace('- Ingredients used:', '').strip()

    # Don't forget last meal
    if current_meal and current_meal.get('name'):
        meals.append(current_meal)

    return meals


# Load and parse meal history
try:
    content = load_data_file("meal_history")
    meals = parse_meal_history(content)

    if not meals:
        st.info("📭 No meals logged yet. Cook a recipe and rate it to start your history!")
        logger.info("No meals found in history")
    else:
        # Stats at top
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🍽️ Total Meals", len(meals))

        with col2:
            ratings = [m['rating'] for m in meals if m['rating'] > 0]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                st.metric("⭐ Average Rating", f"{avg_rating:.1f}/5")
            else:
                st.metric("⭐ Average Rating", "N/A")

        with col3:
            five_star = sum(1 for m in meals if m['rating'] == 5)
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
                    or search_lower in (m.get('ingredients') or '').lower())
            ]

        if min_rating != "All":
            rating_map = {"5 stars": 5, "4+ stars": 4, "3+ stars": 3}
            min_val = rating_map[min_rating]
            filtered_meals = [m for m in filtered_meals if m['rating'] >= min_val]

        st.markdown(f"### Showing {len(filtered_meals)} of {len(meals)} meals")

        # Display meals
        for meal in filtered_meals:
            with st.expander(
                f"**{meal['date']}** - {meal['name']} {meal['stars']}",
                expanded=False
            ):
                if meal['rating']:
                    st.markdown(f"**Rating:** {meal['rating']}/5 {meal['stars']}")

                if meal.get('notes'):
                    st.markdown(f"**Notes:** {meal['notes']}")

                if meal.get('ingredients'):
                    st.markdown("**Ingredients used:**")
                    st.caption(meal['ingredients'])

        logger.info("Meal history displayed", extra={"total_meals": len(meals), "filtered": len(filtered_meals)})

except DataFileNotFoundError:
    st.warning("⚠️ Meal history file not found. It will be created when you log your first meal.")
    logger.warning("Meal history file not found")

except Exception as e:
    st.error(f"❌ Error loading meal history: {str(e)}")
    logger.error("Error loading meal history", exc_info=True)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
