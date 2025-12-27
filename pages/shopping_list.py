"""Shopping List Page - View and manage shopping list.

Shows ingredients added from recipe suggestions, grouped by recipe.
Users can mark items as bought (adds to pantry) or remove from list.
"""

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime
from itertools import groupby

import streamlit as st

from lib.auth import require_authentication
from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger, setup_logging
from lib.mobile_ui import add_mobile_styles, mobile_section_header
from lib.shopping_list_manager import (
    add_items_to_list,
    categorize_ingredient,
    clear_shopping_list,
    load_shopping_list,
    get_grouped_shopping_list,
    remove_items_from_list,
    toggle_item_checked,
)
from lib.ui import apply_styling, render_header, render_metric_card

setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Shopping List - AI Recipe Planner",
    page_icon="🛒",
    layout="wide",
)

# Apply mobile styles
add_mobile_styles()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


# Authentication
require_authentication()

render_header(
    title="Shopping List",
    subtitle="Ingredients to buy for your planned recipes",
    icon="🛒"
)

# Manual Add Section
st.markdown("### ➕ Add Item Manually")
with st.form("manual_add_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_item = st.text_input("Item Name", placeholder="e.g., Milk, Bread, Eggs")
    with col2:
        submitted = st.form_submit_button("Add to List", use_container_width=True, type="primary")

    if submitted and new_item:
        # Use "Manual Additions" as the recipe name for manual items
        if add_items_to_list("Manual Additions", [new_item]):
            st.success(f"✅ Added '{new_item}' to shopping list")
            st.rerun()
        else:
            st.error("❌ Failed to add item")

st.markdown("---")

try:
    # Load grouped shopping list (combined by ingredients, grouped by store section)
    grouped_items = get_grouped_shopping_list()
    total_items = sum(len(items) for items in grouped_items.values())

    if total_items == 0:
        st.info("📭 Your shopping list is empty!\n\nAdd ingredients from recipe suggestions on the **Generate Recipes** page.")

        # Quick navigation
        st.markdown("---")
        if st.button("🎲 Go to Recipe Generator", use_container_width=True, type="primary"):
            st.switch_page("pages/generate_recipes.py")
    else:
        # Show summary
        col1, col2, col3 = st.columns(3)

        with col1:
            render_metric_card("📋 Combined Items", str(total_items))

        with col2:
            num_sections = len(grouped_items)
            render_metric_card("🏪 Store Sections", str(num_sections))

        with col3:
            # Find most recent added date from all items
            all_items_list = [item for items in grouped_items.values() for item in items]
            last_updated = max([item.get('added', '') for item in all_items_list]) if all_items_list else datetime.now().strftime("%Y-%m-%d")
            render_metric_card("📅 Last Updated", last_updated)

        st.markdown("---")

        # Display grouped by store section
        section_icons = {
            "Fresh Produce": "🥬",
            "Dairy & Eggs": "🥛",
            "Proteins": "🥚",
            "Grains & Pasta": "🌾",
            "Canned & Dried": "🥫",
            "Frozen Foods": "❄️",
            "Beverages": "🥤",
            "Baking Supplies": "🧁",
            "Snacks": "🍿",
            "Other": "📦"
        }

        for section_name, items in grouped_items.items():
            icon = section_icons.get(section_name, "📦")

            with st.expander(f"{icon} **{section_name}** ({len(items)} items)", expanded=True):
                # Display checkboxes for each item
                checked_items = []
                for idx, item in enumerate(items):
                    # Format item display with recipes
                    item_text = item['item']
                    recipe_count = item.get('recipe_count', 1)

                    if recipe_count > 1:
                        item_display = f"{item_text} *(used in {recipe_count} recipes)*"
                    else:
                        item_display = item_text

                    # Use the checked state from JSON if available, default to False
                    is_checked = st.checkbox(
                        item_display,
                        value=item.get('checked', False),
                        key=f"shop_item_{section_name}_{idx}",
                        help="Check items you've purchased"
                    )

                    # Update state if changed (update all original items)
                    if is_checked != item.get('checked', False):
                        # For combined items, we need to update all contributing recipes
                        for recipe in item.get('recipes', []):
                            toggle_item_checked(recipe, item_text, is_checked)

                    if is_checked:
                        # Store both the display text and the structured name for matching
                        structured_name = item.get('structured', {}).get('name', item['item'])
                        checked_items.append((item['item'], structured_name, item.get('recipes', [])))

                # Action buttons for this section
                if checked_items:
                    st.markdown("---")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            f"✅ Bought → Add to Pantry ({len(checked_items)})",
                            key=f"buy_{section_name}",
                            use_container_width=True,
                            type="primary"
                        ):
                            # Add checked items to pantry
                            success_count = 0
                            for item_text, structured_name, recipes in checked_items:
                                # Parse ingredient name from formatted text
                                ing_name = item_text.split('(')[0].strip() if '(' in item_text else item_text
                                category = categorize_ingredient(ing_name)
                                if add_item_to_pantry(ing_name, category):
                                    success_count += 1

                                # Remove from all recipes using structured name for better matching
                                for recipe in recipes:
                                    remove_items_from_list(recipe, [structured_name])

                            st.success(f"✅ Added {success_count} items to pantry!")
                            st.rerun()

                    with col2:
                        if st.button(
                            f"🗑️ Remove ({len(checked_items)})",
                            key=f"remove_{section_name}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            # Remove from all recipes using structured name for better matching
                            for item_text, structured_name, recipes in checked_items:
                                for recipe in recipes:
                                    remove_items_from_list(recipe, [structured_name])

                            st.success(f"🗑️ Removed {len(checked_items)} items from list")
                            st.rerun()

        # Global actions
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🗑️ Clear All Items", use_container_width=True, type="secondary"):
                if clear_shopping_list():
                    st.success("✅ Shopping list cleared!")
                    logger.info("Shopping list cleared by user")
                    st.rerun()
                else:
                    st.error("❌ Failed to clear list")

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
            for section_name, items in grouped_items.items():
                icon = section_icons.get(section_name, "📦")
                text_output += f"\n{icon} {section_name}:\n"
                for item in items:
                    checkbox = "[x]" if item.get('checked') else "[ ]"
                    text_output += f"{checkbox} {item['item']}\n"

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
