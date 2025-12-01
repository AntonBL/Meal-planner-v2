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
    remove_items_from_list,
    toggle_item_checked,
)
from lib.ui import apply_styling, render_header, render_metric_card

setup_logging("INFO")
logger = get_logger(__name__)

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


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Shopping List - AI Recipe Planner",
    page_icon="🛒",
    layout="wide",
)

# Apply custom styling
apply_styling()

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
    shopping_items = load_shopping_list()

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
            render_metric_card("📋 Total Items", str(len(shopping_items)))

        with col2:
            unique_recipes = len({item['recipe'] for item in shopping_items})
            render_metric_card("🍽️ Recipes", str(unique_recipes))

        with col3:
            # Find most recent added date
            last_updated = max([item.get('added', '') for item in shopping_items]) if shopping_items else datetime.now().strftime("%Y-%m-%d")
            render_metric_card("📅 Last Updated", last_updated)

        st.markdown("---")

        # Group items by recipe
        shopping_items_sorted = sorted(shopping_items, key=lambda x: x['recipe'])

        for recipe_name, items_group in groupby(shopping_items_sorted, key=lambda x: x['recipe']):
            with st.expander(f"📋 **{recipe_name}**", expanded=True):
                items_list = list(items_group)

                # Display checkboxes for each item
                checked_items = []
                for idx, item in enumerate(items_list):
                    # Use the checked state from JSON if available, default to False
                    is_checked = st.checkbox(
                        item['item'],
                        value=item.get('checked', False),
                        key=f"shop_item_{recipe_name}_{idx}",
                        help="Check items you've purchased"
                    )
                    
                    # Update state if changed
                    if is_checked != item.get('checked', False):
                        toggle_item_checked(recipe_name, item['item'], is_checked)
                        # We don't rerun here to avoid jarring UX, just update backend
                    
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
                            remove_items_from_list(recipe_name, checked_items)

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
                            remove_items_from_list(recipe_name, checked_items)
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
            for recipe_name, items_group in groupby(shopping_items_sorted, key=lambda x: x['recipe']):
                text_output += f"\n**{recipe_name}:**\n"
                for item in items_group:
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
