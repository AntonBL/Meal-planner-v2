"""Update Pantry Page - AI-Powered Pantry Management.

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

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Update Pantry - AI Recipe Planner",
    page_icon="📝",
    layout="wide",
)

# Authentication
require_authentication()

st.title("📝 Update Pantry")
st.markdown("*Chat with AI to manage your pantry items*")

# Initialize session state for chat
if "pantry_messages" not in st.session_state:
    st.session_state.pantry_messages = []

# Initialize LLM
try:
    llm = ClaudeProvider()
except LLMAPIError as e:
    st.error(f"❌ Failed to initialize AI: {e}")
    st.stop()

# Show current pantry in sidebar
with st.sidebar:
    st.markdown("### 📦 Current Pantry")

    try:
        staples = load_data_file("staples")
        fresh = load_data_file("fresh")

        with st.expander("🥫 Pantry Staples", expanded=False):
            st.markdown(staples)

        with st.expander("🥬 Fresh Items", expanded=False):
            st.markdown(fresh)
    except Exception as e:
        st.error(f"Error loading pantry: {e}")

# Main chat interface
st.markdown("### 💬 Chat with AI to Update Pantry")
st.markdown("*Examples: 'Add 2 bottles of olive oil', 'I bought milk and eggs', 'Remove expired tomatoes'*")

# Display chat messages
for message in st.session_state.pantry_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to add, remove, or update?"):
    # Add user message to chat
    st.session_state.pantry_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Load current pantry data
    try:
        staples_content = load_data_file("staples")
        fresh_content = load_data_file("fresh")
        staples_path = get_data_file_path("staples")
        fresh_path = get_data_file_path("fresh")

        # Build AI prompt to interpret the request
        ai_prompt = f"""You are a pantry management assistant. Interpret what the user wants to do with their pantry.

USER REQUEST: "{prompt}"

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

Now interpret: "{prompt}"
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
