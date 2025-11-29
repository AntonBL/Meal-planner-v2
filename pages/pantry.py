"""Pantry Page - AI-Powered Pantry Management.

Users chat with AI to add, update, or remove pantry items.
The AI reads and writes directly to pantry markdown files.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime
from pathlib import Path

from lib.auth import require_authentication
from lib.llm_agents import ClaudeProvider
from lib.file_manager import load_data_file, get_data_file_path
from lib.exceptions import LLMAPIError
from lib.logging_config import get_logger, setup_logging
from lib.vision import detect_items_from_image

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Pantry - AI Recipe Planner",
    page_icon="🥫",
    layout="wide",
)

# Authentication
require_authentication()

st.title("🥫 Pantry")

# Initialize session state for chat
if "pantry_messages" not in st.session_state:
    st.session_state.pantry_messages = []

# Initialize LLM
try:
    llm = ClaudeProvider()
except LLMAPIError as e:
    st.error(f"❌ Failed to initialize AI: {e}")
    st.stop()

# Helper function to parse pantry items by section
def parse_pantry_by_sections(content):
    """Parse markdown pantry content into sections with items."""
    sections = {}
    current_section = None
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if line.strip().startswith('##'):
            # This is a section header
            current_section = line.strip()[2:].strip()
            sections[current_section] = []
        elif line.strip().startswith('-') and current_section:
            # This is an item line under a section
            sections[current_section].append({
                'line_number': i,
                'text': line.strip()[2:],  # Remove "- " prefix
                'full_line': line
            })

    return sections

def delete_pantry_item(file_path, line_number):
    """Delete an item from pantry file by line number."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split('\n')

        # Remove the line
        del lines[line_number]

        # Write back
        file_path.write_text('\n'.join(lines), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Failed to delete pantry item: {e}", exc_info=True)
        return False

# ============================================================================
# MAIN CONTENT: Current Pantry Display (at top to prevent auto-scroll)
# ============================================================================

# Add delete mode toggle
col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.markdown("### 📦 Current Pantry")
with col_toggle:
    delete_mode = st.checkbox("🗑️ Delete mode", value=False, help="Enable to show delete buttons for items")

try:
    staples_path = get_data_file_path("staples")
    fresh_path = get_data_file_path("fresh")
    staples_content = load_data_file("staples")
    fresh_content = load_data_file("fresh")

    # Parse items by sections
    staples_sections = parse_pantry_by_sections(staples_content)
    fresh_sections = parse_pantry_by_sections(fresh_content)

    # Category icons for better visual organization
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
        "Fruits": "🍋"
    }

    # Combine all sections from both files
    all_sections = {}

    # Add staples sections
    for section_name, items in staples_sections.items():
        if items:  # Only add non-empty sections
            all_sections[section_name] = {
                'items': items,
                'file_path': staples_path,
                'file_type': 'staples'
            }

    # Add fresh sections
    for section_name, items in fresh_sections.items():
        if items:  # Only add non-empty sections
            all_sections[section_name] = {
                'items': items,
                'file_path': fresh_path,
                'file_type': 'fresh'
            }

    # Display sections in a single column for better organization
    if all_sections:
        for section_name, section_data in all_sections.items():
            icon = category_icons.get(section_name, "📦")

            with st.expander(f"{icon} {section_name}", expanded=False):
                for item in section_data['items']:
                    if delete_mode:
                        # Show with delete button
                        cols = st.columns([4, 1])
                        with cols[0]:
                            st.markdown(f"• {item['text']}")
                        with cols[1]:
                            if st.button("🗑️", key=f"del_{section_data['file_type']}_{item['line_number']}", help="Delete this item"):
                                if delete_pantry_item(section_data['file_path'], item['line_number']):
                                    st.success(f"Deleted!")
                                    logger.info(f"Deleted item: {item['text']}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
                    else:
                        # Clean view without delete buttons
                        st.markdown(f"• {item['text']}")
    else:
        st.info("Your pantry is empty. Use the chat below to add items!")

except Exception as e:
    st.error(f"Error loading pantry: {e}")
    logger.error("Error in pantry display", exc_info=True)

# ============================================================================
# INTERACTIVE TOOLS: Photo Upload & AI Chat (in expanders to prevent scroll)
# ============================================================================

st.markdown("---")
st.markdown("### 🤖 Update Pantry")

# Photo Upload Section
with st.expander("📸 Quick Add: Upload Photo", expanded=False):
    st.markdown("*Upload a photo of groceries, receipt, or your pantry to auto-detect items*")

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        help="Supported formats: JPG, PNG, GIF, WebP",
        key="pantry_photo_upload"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

        with col2:
            if st.button("🔍 Detect Items with AI", type="primary", use_container_width=True):
                with st.spinner("🤖 Analyzing image... This may take 10-15 seconds"):
                    try:
                        # Reset file pointer
                        uploaded_file.seek(0)

                        # Detect items using vision
                        detected_items = detect_items_from_image(uploaded_file, llm)

                        if detected_items:
                            # Build a natural language prompt from detected items
                            item_descriptions = []
                            for item in detected_items:
                                item_descriptions.append(f"{item['name']} ({item['quantity']})")

                            items_text = ", ".join(item_descriptions)
                            auto_prompt = f"Add {items_text}"

                            st.success(f"✅ Detected {len(detected_items)} items!")
                            st.info(f"📝 Auto-prompt: \"{auto_prompt}\"")
                            st.markdown("*The AI will process this in the chat below*")

                            # Add to chat as if user typed it
                            st.session_state.pantry_messages.append({"role": "user", "content": auto_prompt})

                            # Trigger processing by setting a flag
                            st.session_state['process_vision_prompt'] = auto_prompt

                            st.rerun()
                        else:
                            st.warning("⚠️ No items detected. Try a clearer photo or add items manually using the chat below.")

                    except LLMAPIError as e:
                        st.error(f"❌ Vision API error: {e}")
                        logger.error("Vision detection failed", exc_info=True)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")
                        logger.error("Photo upload error", exc_info=True)

# Chat Interface Section
with st.expander("💬 Chat with AI to Update Pantry", expanded=False):
    st.markdown("*Examples: 'Add 2 bottles of olive oil', 'I bought milk and eggs', 'Remove expired tomatoes'*")
    st.markdown("")  # Add some spacing

    # Display chat messages
    for message in st.session_state.pantry_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check if there's a vision prompt to process automatically
    vision_prompt = st.session_state.pop('process_vision_prompt', None)

    # Chat input
    if prompt := st.chat_input("What would you like to add, remove, or update?"):
        process_prompt = prompt
    elif vision_prompt:
        process_prompt = vision_prompt
    else:
        process_prompt = None

    if process_prompt:
        # Add user message to chat (if from manual input, not vision)
        if not vision_prompt:
            st.session_state.pantry_messages.append({"role": "user", "content": process_prompt})
            with st.chat_message("user"):
                st.markdown(process_prompt)

        # Load current pantry data
        try:
            staples_content = load_data_file("staples")
            fresh_content = load_data_file("fresh")
            staples_path = get_data_file_path("staples")
            fresh_path = get_data_file_path("fresh")

            # Build AI prompt to interpret the request
            ai_prompt = f"""You are a pantry management assistant. Interpret what the user wants to do with their pantry.

USER REQUEST: "{process_prompt}"

Analyze the request and respond in EXACTLY this format (nothing else):

ACTION: [add/remove/update]
ITEMS:
- Item: [item name] | Quantity: [quantity] | Category: [staple/fresh] | Expiry: [YYYY-MM-DD or none]

Examples:
USER: "add tomatoes"
ACTION: add
ITEMS:
- Item: Tomatoes | Quantity: 1 lb | Category: fresh | Expiry: none

USER: "I bought 2 bottles of olive oil and some rice"
ACTION: add
ITEMS:
- Item: Olive Oil | Quantity: 2 bottles | Category: staple | Expiry: none
- Item: Rice | Quantity: 1 bag | Category: staple | Expiry: none

USER: "remove expired milk"
ACTION: remove
ITEMS:
- Item: Milk | Quantity: any | Category: fresh | Expiry: none

Now interpret: "{process_prompt}"
"""

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Understanding your request..."):
                    try:
                        response = llm.generate(ai_prompt, max_tokens=1000)

                        # Parse the response
                        if "ACTION:" in response and "ITEMS:" in response:
                            action = ""
                            items = []

                            for line in response.split('\n'):
                                line = line.strip()
                                if line.startswith("ACTION:"):
                                    action = line.replace("ACTION:", "").strip().lower()
                                elif line.startswith("- Item:"):
                                    # Parse item line
                                    parts = line.replace("- Item:", "").split("|")
                                    if len(parts) >= 3:
                                        item_name = parts[0].replace("Item:", "").strip()
                                        quantity = parts[1].replace("Quantity:", "").strip()
                                        category = parts[2].replace("Category:", "").strip()
                                        expiry = parts[3].replace("Expiry:", "").strip() if len(parts) > 3 else "none"

                                        items.append({
                                            'name': item_name,
                                            'quantity': quantity,
                                            'category': category,
                                            'expiry': expiry
                                        })

                            # Now perform the action
                            if action == "add" and items:
                                for item in items:
                                    # Determine which file
                                    if item['category'] == 'fresh':
                                        file_path = fresh_path
                                        current_content = fresh_content
                                    else:
                                        file_path = staples_path
                                        current_content = staples_content

                                    # Build new line
                                    today = datetime.now().strftime("%Y-%m-%d")
                                    new_line = f"- {item['name']} - {item['quantity']} - Added: {today}"
                                    if item['expiry'] != "none":
                                        new_line += f" - Expires: {item['expiry']}"
                                    new_line += "\n"

                                    # Find first section header and insert after it
                                    lines = current_content.split('\n')
                                    for i, line in enumerate(lines):
                                        if line.startswith('##'):
                                            lines.insert(i + 1, new_line)
                                            break

                                    # Write back
                                    file_path.write_text('\n'.join(lines), encoding="utf-8")

                                item_names = ", ".join([i['name'] for i in items])
                                success_msg = f"✅ Added {item_names} to pantry!"
                                st.success(success_msg)

                                logger.info("Pantry updated via AI", extra={"action": "add", "items": items})

                                st.session_state.pantry_messages.append({
                                    "role": "assistant",
                                    "content": success_msg
                                })

                                st.rerun()

                            elif action == "remove" and items:
                                removed_items = []
                                for item in items:
                                    # Check both files for the item
                                    for file_path, content in [(staples_path, staples_content), (fresh_path, fresh_content)]:
                                        lines = content.split('\n')
                                        new_lines = []
                                        item_removed = False

                                        for line in lines:
                                            # Check if this line contains the item name
                                            if line.strip().startswith('-') and item['name'].lower() in line.lower():
                                                # Skip this line (remove it)
                                                item_removed = True
                                            else:
                                                new_lines.append(line)

                                        if item_removed:
                                            # Write back updated content
                                            file_path.write_text('\n'.join(new_lines), encoding="utf-8")
                                            removed_items.append(item['name'])
                                            break  # Found and removed, don't check other file

                                if removed_items:
                                    item_names = ", ".join(removed_items)
                                    success_msg = f"✅ Removed {item_names} from pantry!"
                                    st.success(success_msg)

                                    logger.info("Pantry updated via AI", extra={"action": "remove", "items": removed_items})

                                    st.session_state.pantry_messages.append({
                                        "role": "assistant",
                                        "content": success_msg
                                    })

                                    st.rerun()
                                else:
                                    st.warning("⚠️ Couldn't find those items in your pantry. Please check the sidebar to see what's available.")

                            else:
                                st.warning(f"I understood you want to {action}, but couldn't parse the items. Please try being more specific.")
                        else:
                            st.error("❌ I had trouble understanding that. Please try rephrasing, like 'add tomatoes' or 'I bought milk and eggs'")
                            logger.error("Invalid AI response format", extra={"response": response[:500]})

                    except LLMAPIError as e:
                        st.error(f"❌ AI error: {e}")
                        logger.error("LLM API error", exc_info=True)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")
                        logger.error("Unexpected error updating pantry", exc_info=True)

        except Exception as e:
            st.error(f"❌ Error loading pantry files: {e}")
            logger.error("Error loading pantry files", exc_info=True)

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
