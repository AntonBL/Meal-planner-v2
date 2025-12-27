"""Pantry Page - AI-Powered Pantry Management.

Users chat with AI to add, update, or remove pantry items.
The AI reads and writes directly to pantry JSON storage.
"""

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime

import streamlit as st

from lib.auth import require_authentication
from lib.exceptions import LLMAPIError
from lib.llm_core import get_smart_model
from lib.logging_config import get_logger, setup_logging
from lib.pantry_manager import (
    add_pantry_item,
    load_pantry_items,
    remove_pantry_item,
)
from lib.ui import apply_styling, render_header
from lib.vision import detect_items_from_image

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Pantry - AI Recipe Planner",
    page_icon="🥫",
    layout="wide",
)

# Apply custom styling
# apply_styling()

# Authentication
require_authentication()

render_header(
    title="Pantry",
    subtitle="Manage your pantry staples and fresh items",
    icon="🥫"
)

# Initialize session state for chat
if "pantry_messages" not in st.session_state:
    st.session_state.pantry_messages = []

# Initialize session state for detected items from image
if "detected_items_from_image" not in st.session_state:
    st.session_state.detected_items_from_image = None

# Initialize LLM
try:
    llm = get_smart_model()
except LLMAPIError as e:
    st.error(f"❌ Failed to initialize AI: {e}")
    st.stop()


# ============================================================================
# MAIN CONTENT: Current Pantry Display
# ============================================================================

# Add delete mode toggle
col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.markdown("### 📦 Current Pantry")
with col_toggle:
    delete_mode = st.checkbox("🗑️ Delete mode", value=False, help="Enable to show delete buttons for items")

try:
    items = load_pantry_items()
    
    # Category icons
    category_icons = {
        "Grains & Pasta": "🌾",
        "Beans & Legumes": "🫘",
        "Oils & Condiments": "🫗",
        "Canned Goods": "🥫",
        "Spices & Herbs (Dried)": "🌿",
        "Proteins (Vegetarian)": "🥚",
        "Dairy & Alternatives": "🧈",
        "Vegetables": "🥬",
        "Fresh Herbs": "🌱",
        "Fruits": "🍋",
        "Uncategorized": "📦"
    }

    # Group by category
    sections = {}
    for item in items:
        cat = item.get("category", "Uncategorized")
        if cat not in sections:
            sections[cat] = []
        sections[cat].append(item)

    if sections:
        # Sort sections: defined categories first, then others
        defined_cats = list(category_icons.keys())
        sorted_cats = sorted(sections.keys(), key=lambda x: defined_cats.index(x) if x in defined_cats else 999)

        for section_name in sorted_cats:
            section_items = sections[section_name]
            icon = category_icons.get(section_name, "📦")

            with st.expander(f"{icon} {section_name}", expanded=False):
                for item in section_items:
                    # Format item text
                    text = f"{item['name']}"
                    if item.get('quantity') and item['quantity'] != "1":
                        text += f" - {item['quantity']}"
                    if item.get('expiry'):
                        text += f" (Exp: {item['expiry']})"
                        
                    if delete_mode:
                        cols = st.columns([4, 1])
                        with cols[0]:
                            st.markdown(f"• {text}")
                        with cols[1]:
                            if st.button("🗑️", key=f"del_{item['id']}", help="Delete this item"):
                                if remove_pantry_item(item['id']):
                                    st.success("Deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
                    else:
                        st.markdown(f"• {text}")
    else:
        st.info("Your pantry is empty. Use the chat below to add items!")

except Exception as e:
    st.error(f"Error loading pantry: {e}")
    logger.error("Error in pantry display", exc_info=True)

# ============================================================================
# INTERACTIVE TOOLS: Photo Upload & AI Chat
# ============================================================================

st.markdown("---")
st.markdown("### 🤖 Update Pantry")

# Photo Upload Section
with st.expander("📸 Quick Add: Upload Photo(s)", expanded=False):
    st.markdown("*Upload one or more photos of groceries, receipts, or your pantry to auto-detect items*")

    uploaded_files = st.file_uploader(
        "Choose image(s)",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        help="Supported formats: JPG, PNG, GIF, WebP. You can upload multiple images at once!",
        key="pantry_photo_upload",
        accept_multiple_files=True
    )

    if uploaded_files:
        # Display all uploaded images
        num_images = len(uploaded_files)
        st.markdown(f"**{num_images} image{'s' if num_images > 1 else ''} uploaded**")

        # Show images in a grid
        cols_per_row = 3
        for i in range(0, num_images, cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < num_images:
                    with col:
                        st.image(uploaded_files[idx], caption=f"Image {idx + 1}", use_container_width=True)

        # Detect button
        st.markdown("")
        if st.button("🔍 Detect Items with AI", type="primary", use_container_width=True):
            with st.spinner(f"🤖 Analyzing {num_images} image{'s' if num_images > 1 else ''}... This may take {10 * num_images}-{15 * num_images} seconds"):
                try:
                    all_detected_items = []

                    # Process each image
                    for idx, uploaded_file in enumerate(uploaded_files):
                        uploaded_file.seek(0)
                        detected_items = detect_items_from_image(uploaded_file, llm)

                        if detected_items:
                            all_detected_items.extend(detected_items)
                            logger.info(f"Detected {len(detected_items)} items from image {idx + 1}")

                    if all_detected_items:
                        st.session_state.detected_items_from_image = all_detected_items
                        st.success(f"✅ Detected {len(all_detected_items)} items from {num_images} image{'s' if num_images > 1 else ''}! Review them below.")
                        st.rerun()
                    else:
                        st.warning("⚠️ No items detected. Try clearer photos or add items manually using the chat below.")

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    logger.error("Photo upload error", exc_info=True)

    # Display detected items for review
    if st.session_state.detected_items_from_image:
        st.markdown("---")
        st.markdown("#### 📋 Detected Items - Review & Confirm")
        st.markdown("*Uncheck items you don't want to add, then click 'Add to Pantry'*")

        detected_items = st.session_state.detected_items_from_image

        # Create a container for the items
        items_container = st.container()

        with items_container:
            # Group items by category
            categories = {}
            for idx, item in enumerate(detected_items):
                cat = item.get('category', 'Fresh Item')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((idx, item))

            # Display items by category
            for category, cat_items in categories.items():
                st.markdown(f"**{category}:**")
                cols = st.columns(2)

                for i, (idx, item) in enumerate(cat_items):
                    with cols[i % 2]:
                        # Use the confirmed field from the item
                        checked = st.checkbox(
                            f"{item['name']} - {item['quantity']}",
                            value=item.get('confirmed', True),
                            key=f"confirm_item_{idx}",
                            help=f"Category: {item['category']}"
                        )
                        # Update the item's confirmed status
                        detected_items[idx]['confirmed'] = checked

        st.markdown("")

        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            if st.button("✅ Add Selected Items to Pantry", type="primary", use_container_width=True):
                # Filter only confirmed items
                items_to_add = [item for item in detected_items if item.get('confirmed', True)]

                if items_to_add:
                    try:
                        # Map categories to pantry categories
                        category_mapping = {
                            "Pantry Staple": "Uncategorized",  # Will be categorized by AI if needed
                            "Fresh Item": "Uncategorized",
                        }

                        for item in items_to_add:
                            pantry_item = {
                                'name': item['name'],
                                'quantity': item['quantity'],
                                'category': category_mapping.get(item['category'], item['category']),
                                'type': 'fresh' if item['category'] == 'Fresh Item' else 'staple',
                                'expiry': None
                            }
                            add_pantry_item(pantry_item)

                        names = ", ".join([i['name'] for i in items_to_add])
                        st.success(f"✅ Added {len(items_to_add)} items to pantry: {names}")

                        # Clear the detected items
                        st.session_state.detected_items_from_image = None
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding items: {e}")
                        logger.error("Error adding detected items to pantry", exc_info=True)
                else:
                    st.warning("⚠️ No items selected. Please check at least one item to add.")

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.detected_items_from_image = None
                st.rerun()

        with col3:
            st.markdown(f"*{len([i for i in detected_items if i.get('confirmed', True)])} selected*")

# Chat Interface Section
with st.expander("💬 Chat with AI to Update Pantry", expanded=False):
    st.markdown("*Examples: 'Add 2 bottles of olive oil', 'I bought milk and eggs', 'Remove expired tomatoes'*")
    st.markdown("")

    for message in st.session_state.pantry_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    vision_prompt = st.session_state.pop('process_vision_prompt', None)

    if prompt := st.chat_input("What would you like to add, remove, or update?"):
        process_prompt = prompt
    elif vision_prompt:
        process_prompt = vision_prompt
    else:
        process_prompt = None

    if process_prompt:
        if not vision_prompt:
            st.session_state.pantry_messages.append({"role": "user", "content": process_prompt})
            with st.chat_message("user"):
                st.markdown(process_prompt)

        # AI Processing
        try:
            # Build AI prompt
            ai_prompt = f"""You are a pantry management assistant. Interpret what the user wants to do with their pantry.

USER REQUEST: "{process_prompt}"

Analyze the request and respond in EXACTLY this format (nothing else):

ACTION: [add/remove/update]
ITEMS:
- Item: [item name] | Quantity: [quantity] | Category: [category name] | Expiry: [YYYY-MM-DD or none]

Categories: Grains & Pasta, Beans & Legumes, Oils & Condiments, Canned Goods, Spices & Herbs (Dried), Proteins (Vegetarian), Dairy & Alternatives, Vegetables, Fresh Herbs, Fruits. Use "Uncategorized" if unsure.

Examples:
USER: "add tomatoes"
ACTION: add
ITEMS:
- Item: Tomatoes | Quantity: 1 lb | Category: Vegetables | Expiry: none

USER: "remove expired milk"
ACTION: remove
ITEMS:
- Item: Milk | Quantity: any | Category: Dairy & Alternatives | Expiry: none

Now interpret: "{process_prompt}"
"""

            with st.chat_message("assistant"), st.spinner("Understanding your request..."):
                response = llm.generate(ai_prompt, max_tokens=1000)

                if "ACTION:" in response and "ITEMS:" in response:
                    action = ""
                    items_to_process = []

                    for line in response.split('\n'):
                        line = line.strip()
                        if line.startswith("ACTION:"):
                            action = line.replace("ACTION:", "").strip().lower()
                        elif line.startswith("- Item:"):
                            parts = line.replace("- Item:", "").split("|")
                            if len(parts) >= 3:
                                item_name = parts[0].replace("Item:", "").strip()
                                quantity = parts[1].replace("Quantity:", "").strip()
                                category = parts[2].replace("Category:", "").strip()
                                expiry = parts[3].replace("Expiry:", "").strip() if len(parts) > 3 else None
                                if expiry == "none": expiry = None

                                items_to_process.append({
                                    'name': item_name,
                                    'quantity': quantity,
                                    'category': category,
                                    'expiry': expiry,
                                    'type': 'fresh' if category in ['Vegetables', 'Fruits', 'Fresh Herbs', 'Dairy & Alternatives'] else 'staple'
                                })

                    # Perform Action
                    if action == "add" and items_to_process:
                        for item in items_to_process:
                            add_pantry_item(item)
                        
                        names = ", ".join([i['name'] for i in items_to_process])
                        msg = f"✅ Added {names} to pantry!"
                        st.success(msg)
                        st.session_state.pantry_messages.append({"role": "assistant", "content": msg})
                        st.rerun()

                    elif action == "remove" and items_to_process:
                        # For removal, we need to find items by name since we don't have IDs from the user
                        current_items = load_pantry_items()
                        removed_names = []
                        
                        for item_to_remove in items_to_process:
                            # Find matching items in pantry
                            matches = [
                                i for i in current_items 
                                if item_to_remove['name'].lower() in i['name'].lower()
                            ]
                            
                            for match in matches:
                                if remove_pantry_item(match['id']):
                                    removed_names.append(match['name'])
                        
                        if removed_names:
                            msg = f"✅ Removed {', '.join(removed_names)} from pantry!"
                            st.success(msg)
                            st.session_state.pantry_messages.append({"role": "assistant", "content": msg})
                            st.rerun()
                        else:
                            msg = "⚠️ Couldn't find those items in your pantry."
                            st.warning(msg)
                            st.session_state.pantry_messages.append({"role": "assistant", "content": msg})

                    else:
                        st.warning("Could not understand items to process.")
                else:
                    st.error("❌ I had trouble understanding that. Please try rephrasing.")

        except Exception as e:
            st.error(f"❌ Error: {e}")
            logger.error("Error processing request", exc_info=True)

# Navigation
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("app.py")
with col2:
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.pantry_messages = []
        st.rerun()
