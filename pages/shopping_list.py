"""Shopping List Page - View and manage shopping list.

Shows ingredients added from recipe suggestions, grouped by recipe.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime
from itertools import groupby

from lib.auth import require_authentication
from lib.file_manager import load_data_file, get_data_file_path
from lib.logging_config import get_logger, setup_logging

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Shopping List - AI Recipe Planner",
    page_icon="🛒",
    layout="wide",
)

# Authentication
require_authentication()

st.title("🛒 Shopping List")
st.markdown("*Ingredients to buy for your planned recipes*")

st.markdown("---")

try:
    shopping_content = load_data_file("shopping_list")

    # Parse shopping list to extract items grouped by recipe
    lines = shopping_content.split('\n')
    shopping_items = []
    current_recipe = None

    for line in lines:
        line = line.strip()

        # Recipe header (## For: Recipe Name (Added: YYYY-MM-DD))
        if line.startswith('##'):
            # Extract recipe name
            recipe_part = line.replace('##', '').strip()

            # Handle different formats
            if 'For:' in recipe_part:
                recipe_part = recipe_part.split('For:')[1].strip()

            if '(Added:' in recipe_part:
                current_recipe = recipe_part.split('(Added:')[0].strip()
            else:
                current_recipe = recipe_part.strip()

        # Item line (- Item name)
        elif line.startswith('-') and current_recipe:
            item_text = line[1:].strip()
            if item_text:
                shopping_items.append({
                    'recipe': current_recipe,
                    'item': item_text
                })

    if not shopping_items:
        st.info("📭 Your shopping list is empty!\n\nAdd ingredients from recipe suggestions on the **Generate Recipes** page.")

        # Quick navigation
        st.markdown("---")
        if st.button("🎲 Go to Recipe Generator", use_container_width=True, type="primary"):
            st.switch_page("pages/generate_recipes.py")
    else:
        # Show summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📋 Total Items", len(shopping_items))

        with col2:
            unique_recipes = len(set(item['recipe'] for item in shopping_items))
            st.metric("🍽️ Recipes", unique_recipes)

        with col3:
            st.metric("📅 Last Updated", datetime.now().strftime("%Y-%m-%d"))

        st.markdown("---")

        # Group items by recipe
        shopping_items_sorted = sorted(shopping_items, key=lambda x: x['recipe'])

        for recipe_name, items_group in groupby(shopping_items_sorted, key=lambda x: x['recipe']):
            with st.expander(f"📋 **{recipe_name}**", expanded=True):
                items_list = list(items_group)

                for item in items_list:
                    st.checkbox(
                        item['item'],
                        key=f"shop_item_{recipe_name}_{item['item']}",
                        help="Check off items as you purchase them"
                    )

                st.caption(f"*{len(items_list)} items for this recipe*")

        # Actions
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🗑️ Clear All Items", use_container_width=True, type="secondary"):
                shopping_path = get_data_file_path("shopping_list")
                # Reset to template
                template = f"# Shopping List\n\nGenerated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                shopping_path.write_text(template, encoding="utf-8")
                st.success("✅ Shopping list cleared!")
                logger.info("Shopping list cleared by user")
                st.rerun()

        with col2:
            if st.button("📝 View as Text", use_container_width=True):
                st.session_state['show_text_view'] = not st.session_state.get('show_text_view', False)
                st.rerun()

        with col3:
            if st.button("🎲 Add More Recipes", use_container_width=True):
                st.switch_page("pages/generate_recipes.py")

        # Show text view if toggled
        if st.session_state.get('show_text_view', False):
            st.markdown("---")
            st.markdown("### 📄 Plain Text View")
            st.markdown("*Copy this to your notes app or print it*")

            text_output = ""
            for recipe_name, items_group in groupby(shopping_items_sorted, key=lambda x: x['recipe']):
                text_output += f"\n**{recipe_name}:**\n"
                for item in items_group:
                    text_output += f"☐ {item['item']}\n"

            st.text_area("Shopping List", text_output, height=300, label_visibility="collapsed")

except Exception as e:
    st.error(f"❌ Error loading shopping list: {e}")
    logger.error("Error loading shopping list", exc_info=True)

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("🎲 Generate Recipes", use_container_width=True):
        st.switch_page("pages/generate_recipes.py")

with col3:
    if st.button("📝 Update Pantry", use_container_width=True):
        st.switch_page("pages/update_pantry.py")
