"""
AI Recipe Planner - Main Application
A Streamlit app for intelligent meal planning and pantry management.
"""

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from lib.auth import require_authentication
from lib.mobile_ui import add_mobile_styles
from lib.ui import apply_styling, render_card, render_header, render_metric_card

# Page configuration
st.set_page_config(
    page_title="AI Recipe Planner",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_styling()
add_mobile_styles()  # Add mobile-optimized styles

# ============================================================================
# Authentication
# ============================================================================
# Authentication is encapsulated in lib/auth.py
# To disable auth, set ENABLE_AUTH = False in lib/auth.py

name, username = require_authentication()

# ============================================================================
# Data Migration (one-time)
# ============================================================================
# Title
render_header(
    title="AI Recipe Planner",
    subtitle="Your intelligent cooking companion",
    icon="🏠"
)

# Helper functions
def count_items_in_file(file_path):
    """Count items (lines starting with '-') in a markdown file."""
    try:
        content = Path(file_path).read_text()
        return len([line for line in content.split('\n') if line.strip().startswith('-')])
    except FileNotFoundError:
        return 0

def get_expiring_soon():
    """Get count of items expiring soon (next 3 days)."""
    try:
        fresh_content = Path("data/pantry/fresh.md").read_text()

        # Parse expiry dates
        lines = fresh_content.split('\n')
        expiring_count = 0
        today = datetime.now().date()
        threshold = today + timedelta(days=3)

        for line in lines:
            if not line.strip().startswith('-'):
                continue

            # Look for expiry date
            if 'Expires:' in line or 'Use by:' in line:
                # Extract date (format: YYYY-MM-DD or ~YYYY-MM-DD)
                parts = line.split('Expires:') if 'Expires:' in line else line.split('Use by:')
                if len(parts) > 1:
                    date_str = parts[1].split('-')[0].strip().replace('~', '').strip()

                    try:
                        # Try to parse date
                        if len(date_str) >= 10:  # YYYY-MM-DD
                            expiry_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()

                            # Check if within threshold
                            if today <= expiry_date <= threshold:
                                expiring_count += 1
                    except ValueError:
                        # Invalid date format, skip
                        continue

        return expiring_count

    except FileNotFoundError:
        return 0
    except Exception:
        return 0

# Stats Dashboard
st.markdown("### 📊 Dashboard")
col1, col2, col3 = st.columns(3)

with col1:
    pantry_count = count_items_in_file("data/pantry/staples.md")
    render_metric_card("🥫 Pantry Items", str(pantry_count))

with col2:
    fresh_count = count_items_in_file("data/pantry/fresh.md")
    render_metric_card("🥬 Fresh Items", str(fresh_count))

with col3:
    expiring_count = get_expiring_soon()
    render_metric_card("⚠️ Expiring Soon", str(expiring_count), delta="Warning" if expiring_count > 0 else None)

# Separator
st.markdown("---")

# Main Actions
st.markdown("### 🎯 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🎲 Generate Recipes", use_container_width=True, type="primary"):
        st.switch_page("pages/generate_recipes.py")
    st.caption("Get AI-powered recipe suggestions based on your pantry")

with col2:
    if st.button("📅 Weekly Planner", use_container_width=True):
        st.switch_page("pages/weekly_planner.py")
    st.caption("Plan up to 7 meals for the week")

with col3:
    if st.button("🥫 Pantry", use_container_width=True):
        st.switch_page("pages/pantry.py")
    st.caption("Add items manually or via photo upload")

with col4:
    if st.button("📜 Meal History", use_container_width=True):
        st.switch_page("pages/meal_history.py")
    st.caption("View past meals and ratings")

# Second row of actions
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🛒 Shopping List", use_container_width=True):
        st.switch_page("pages/shopping_list.py")
    st.caption("View ingredients to buy for recipes")

# Separator
st.markdown("---")

# Recent Activity
st.markdown("### 📝 Recent Activity")

try:
    meal_history = Path("data/meal_history.md").read_text()
    # Extract the most recent meal entry
    lines = meal_history.split('\n')
    recent_meals = []
    for i, line in enumerate(lines):
        if line.startswith('### '):
            # Found a meal entry
            date_line = line.replace('###', '').strip()
            if i + 1 < len(lines):
                recipe_line = lines[i + 1].strip()
                recent_meals.append(f"{date_line}: {recipe_line}")
            if len(recent_meals) >= 3:
                break

    if recent_meals:
        for meal in recent_meals:
            render_card(f"**{meal}**", icon="🍳")
    else:
        st.info("No meals logged yet. Start cooking and log your first meal!")

except FileNotFoundError:
    st.info("No meal history found yet.")

# Separator
st.markdown("---")

# Footer
st.markdown("### 💡 Tips")
st.info("""
- **Running low on ingredients?** Check the Shopping List for items to buy
- **Can't decide what to cook?** Try the Recipe Generator with different cuisine options
- **Have groceries?** Upload a photo to quickly update your pantry
""")

# Sidebar
with st.sidebar:
    st.markdown("## 🍳 Navigation")
    st.markdown("Use the buttons above or navigate using these links:")
    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/generate_recipes.py", label="Generate Recipes", icon="🎲")
    st.page_link("pages/weekly_planner.py", label="Weekly Planner", icon="📅")
    st.page_link("pages/pantry.py", label="Pantry", icon="🥫")
    st.page_link("pages/shopping_list.py", label="Shopping List", icon="🛒")
    st.page_link("pages/meal_history.py", label="Meal History", icon="📜")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("AI Recipe Planner helps you discover recipes based on what you have in your pantry.")
    st.markdown("Built with ❤️ using Streamlit and Claude AI")
