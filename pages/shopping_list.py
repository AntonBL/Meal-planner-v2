"""Shopping List Page - View and manage shopping list.

Shows ingredients added from recipe suggestions, grouped by recipe.
Users can mark items as bought (adds to pantry) or remove from list.
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def categorize_ingredient(ingredient_name: str) -> str:
    """Categorize ingredient as 'staple' or 'fresh' based on keywords.

    Args:
        ingredient_name: Name of the ingredient

    Returns:
        'staple' or 'fresh'
    """
    ingredient_lower = ingredient_name.lower()

    # Fresh item keywords
    fresh_keywords = [
        'milk', 'cheese', 'yogurt', 'cream', 'butter',
        'egg', 'eggs',
        'lettuce', 'spinach', 'kale', 'arugula', 'greens',
        'tomato', 'tomatoes', 'cucumber', 'pepper', 'peppers',
        'onion', 'onions', 'garlic', 'ginger',
        'carrot', 'carrots', 'celery', 'broccoli', 'cauliflower',
        'mushroom', 'mushrooms',
        'potato', 'potatoes', 'sweet potato',
        'avocado', 'avocados',
        'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges',
        'lemon', 'lemons', 'lime', 'limes',
        'fresh', 'tofu', 'tempeh'
    ]

    # Check if any fresh keyword is in the ingredient
    for keyword in fresh_keywords:
        if keyword in ingredient_lower:
            return 'fresh'

    # Default to staple
    return 'staple'


def add_item_to_pantry(item_name: str, category: str) -> bool:
    """Add an item to the appropriate pantry file.

    Args:
        item_name: Name of the item
        category: 'staple' or 'fresh'

    Returns:
        True if successful, False otherwise
    """
    try:
        # Determine which file
        if category == 'fresh':
            file_path = get_data_file_path("fresh")
        else:
            file_path = get_data_file_path("staples")

        # Read current content
        current_content = file_path.read_text(encoding="utf-8")

        # Build new item line
        today = datetime.now().strftime("%Y-%m-%d")
        new_line = f"- {item_name} - Added: {today} (from shopping list)\n"

        # Find first section header and insert after it
        lines = current_content.split('\n')
        insert_index = -1

        for i, line in enumerate(lines):
            if line.startswith('##'):
                insert_index = i + 1
                break

        if insert_index == -1:
            lines.append(new_line)
        else:
            lines.insert(insert_index, new_line)

        # Write back
        file_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info(
            "Added shopping item to pantry",
            extra={"item": item_name, "category": category}
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to add item to pantry",
            extra={"item": item_name, "error": str(e)},
            exc_info=True
        )
        return False


def remove_items_from_shopping_list(recipe_name: str, items_to_remove: list) -> bool:
    """Remove specific items from shopping list for a given recipe.

    Args:
        recipe_name: Name of the recipe
        items_to_remove: List of item names to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        shopping_path = get_data_file_path("shopping_list")
        content = shopping_path.read_text(encoding="utf-8")

        lines = content.split('\n')
        new_lines = []
        current_recipe = None

        for line in lines:
            line_stripped = line.strip()

            # Track current recipe section
            if line_stripped.startswith('##'):
                if 'For:' in line_stripped:
                    recipe_part = line_stripped.replace('##', '').strip()
                    if '(Added:' in recipe_part:
                        recipe_part = recipe_part.split('For:')[1].strip()
                        current_recipe = recipe_part.split('(Added:')[0].strip()
                    else:
                        current_recipe = recipe_part.replace('For:', '').strip()
                new_lines.append(line)

            # Check if this is an item to remove
            elif line_stripped.startswith('-') and current_recipe == recipe_name:
                item_text = line_stripped[1:].strip()
                if item_text not in items_to_remove:
                    new_lines.append(line)
                else:
                    logger.info(f"Removing item from shopping list: {item_text}")

            else:
                new_lines.append(line)

        # Write back
        shopping_path.write_text('\n'.join(new_lines), encoding="utf-8")

        logger.info(
            "Removed items from shopping list",
            extra={"recipe": recipe_name, "count": len(items_to_remove)}
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to remove items from shopping list",
            extra={"recipe": recipe_name, "error": str(e)},
            exc_info=True
        )
        return False


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

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

                # Display checkboxes for each item
                checked_items = []
                for idx, item in enumerate(items_list):
                    is_checked = st.checkbox(
                        item['item'],
                        key=f"shop_item_{recipe_name}_{idx}",
                        help="Check items you've purchased"
                    )
                    if is_checked:
                        checked_items.append(item['item'])

                st.caption(f"*{len(items_list)} items for this recipe*")

                # Action buttons for this recipe section
                if checked_items:
                    st.markdown("---")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            f"✅ Bought → Add to Pantry ({len(checked_items)})",
                            key=f"buy_{recipe_name}",
                            use_container_width=True,
                            type="primary"
                        ):
                            # Add checked items to pantry
                            success_count = 0
                            for item_name in checked_items:
                                category = categorize_ingredient(item_name)
                                if add_item_to_pantry(item_name, category):
                                    success_count += 1

                            # Remove from shopping list
                            remove_items_from_shopping_list(recipe_name, checked_items)

                            st.success(f"✅ Added {success_count} items to pantry!")
                            st.rerun()

                    with col2:
                        if st.button(
                            f"🗑️ Remove ({len(checked_items)})",
                            key=f"remove_{recipe_name}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            # Just remove from shopping list without adding to pantry
                            remove_items_from_shopping_list(recipe_name, checked_items)
                            st.success(f"🗑️ Removed {len(checked_items)} items from list")
                            st.rerun()

        # Global actions
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
    if st.button("🥫 Pantry", use_container_width=True):
        st.switch_page("pages/pantry.py")
