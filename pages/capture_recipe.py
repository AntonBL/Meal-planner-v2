"""Capture Recipe Page - Extract recipes from images using AI.

Upload a screenshot or photo of a recipe and let AI extract the details,
then refine with chat before saving to your recipe library.
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from lib.auth import require_authentication
from lib.constants import RECIPE_SOURCE_CAPTURED
from lib.exceptions import LLMAPIError
from lib.llm_agents import RecipeGenerator
from lib.llm_core import get_smart_model
from lib.logging_config import get_logger, setup_logging
from lib.recipe_book_manager import add_to_recipe_book, is_in_recipe_book
from lib.recipe_store import save_recipe
from lib.ui import render_header
from lib.vision import extract_recipe_from_image
from lib.weekly_plan_manager import add_recipe_to_plan

setup_logging("INFO")
logger = get_logger(__name__)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Capture Recipe - AI Recipe Planner",
    page_icon="📸",
    layout="wide",
)

# Authentication
require_authentication()

render_header(
    title="Capture Recipe",
    subtitle="Extract recipes from screenshots using AI",
    icon="📸"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize session state for captured recipe
if "captured_recipe" not in st.session_state:
    st.session_state.captured_recipe = None

# Initialize session state for chat
if "capture_chat" not in st.session_state:
    st.session_state.capture_chat = []

# ============================================================================
# SIDEBAR INSTRUCTIONS
# ============================================================================

with st.sidebar:
    st.markdown("## How It Works")
    st.markdown(
        """
        1. **Upload image(s)** of a recipe (screenshot, photo, or website)
        2. **AI analyzes ALL images** together to extract the complete recipe
        3. **Review & refine** using chat to make adjustments
        4. **Save to library** or add to weekly plan
        """
    )
    st.markdown("---")
    st.markdown("**💡 Tips:**")
    st.markdown("- **Multi-page recipes:** Upload all pages in order - they'll be combined automatically!")
    st.markdown("- Works best with clear screenshots from recipe websites")
    st.markdown("- For cookbook recipes spanning 2-3 pages, upload them all at once")

# ============================================================================
# MAIN CONTENT: IMAGE UPLOAD SECTION
# ============================================================================

st.markdown("### 📤 Upload Recipe Image(s)")

# File uploader with multiple file support
uploaded_files = st.file_uploader(
    "Choose recipe image(s)",
    type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
    help="Upload one or more screenshots or photos of a recipe. Useful for multi-page recipes!",
    key="recipe_image_upload",
    accept_multiple_files=True
)

if uploaded_files:
    # Display number of images uploaded
    num_images = len(uploaded_files)
    st.markdown(f"**{num_images} image{'s' if num_images > 1 else ''} uploaded**")

    if num_images > 1:
        st.info("💡 **Multi-page recipe detected!** All images will be analyzed together in order.")

    # Display all uploaded images in a grid
    cols_per_row = 3
    for i in range(0, num_images, cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < num_images:
                with col:
                    st.image(uploaded_files[idx], caption=f"Page {idx + 1}", use_container_width=True)

    st.markdown("")

    # Extract button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Ready to extract?**")
        if num_images > 1:
            st.markdown(f"AI will analyze all {num_images} images in order to extract the complete recipe.")
        else:
            st.markdown("Click the button below to analyze the image with AI.")

    with col2:
        if st.button("🔍 Extract Recipe", type="primary", use_container_width=True):
            spinner_msg = f"🤖 Analyzing {num_images} image{'s' if num_images > 1 else ''}... This may take {15 * num_images}-{25 * num_images} seconds"
            with st.spinner(spinner_msg):
                try:
                    # Extract recipe from all images
                    from lib.vision import extract_recipe_from_images

                    # Reset all file pointers
                    for f in uploaded_files:
                        f.seek(0)

                    # Extract recipe from all images in order
                    extracted_recipe = extract_recipe_from_images(uploaded_files)

                    if extracted_recipe:
                        # Add metadata
                        extracted_recipe['source'] = RECIPE_SOURCE_CAPTURED
                        extracted_recipe['rating'] = 0
                        extracted_recipe['cook_count'] = 0
                        extracted_recipe['tags'] = ['captured']

                        # Convert ingredients to canonical format
                        # Vision extraction returns simple list - convert to canonical with status="needed"
                        from lib.ingredient_schema import from_string_list

                        if extracted_recipe.get('ingredients') and isinstance(extracted_recipe['ingredients'], list):
                            # Check if already in canonical format
                            if not (len(extracted_recipe['ingredients']) > 0 and
                                    isinstance(extracted_recipe['ingredients'][0], dict) and
                                    'status' in extracted_recipe['ingredients'][0]):
                                # Convert from string list to canonical format
                                # Default to "needed" since captured recipes are for future cooking
                                extracted_recipe['ingredients'] = from_string_list(
                                    extracted_recipe['ingredients'],
                                    status="needed"
                                )
                                logger.info(
                                    "Converted captured recipe ingredients to canonical format",
                                    extra={"recipe_name": extracted_recipe.get("name"),
                                           "ingredient_count": len(extracted_recipe['ingredients'])}
                                )

                        # Store in session state
                        st.session_state.captured_recipe = extracted_recipe
                        st.session_state.capture_chat = []

                        logger.info(
                            "Recipe extracted successfully",
                            extra={
                                "recipe_name": extracted_recipe.get("name"),
                                "total_images": num_images
                            }
                        )

                        st.success("✅ Recipe extracted! Review and refine below.")
                        st.rerun()
                    else:
                        st.warning("⚠️ Could not extract recipe from images. Please try clearer images.")
                        logger.warning("Recipe extraction returned None")

                except LLMAPIError as e:
                    st.error(f"❌ Error: {e}")
                    logger.error(f"Recipe extraction failed: {e}", exc_info=True)
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
                    logger.error(f"Unexpected error during extraction: {e}", exc_info=True)

# ============================================================================
# RECIPE REVIEW AND REFINEMENT SECTION
# ============================================================================

if st.session_state.captured_recipe:
    recipe = st.session_state.captured_recipe

    st.markdown("---")
    st.markdown(f"## 📋 {recipe.get('name', 'Captured Recipe')}")

    # Display recipe details in expandable sections
    with st.expander("📝 Recipe Details", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Description:**")
            st.markdown(f"*{recipe.get('description', 'No description')}*")
            st.markdown(f"**Time:** {recipe.get('time_minutes', '?')} minutes")
            st.markdown(f"**Difficulty:** {recipe.get('difficulty', 'medium').capitalize()}")

        with col2:
            st.markdown("**Ingredients:**")
            ingredients = recipe.get('ingredients', [])
            if ingredients:
                # Import schema utilities for display
                from lib.ingredient_schema import validate_ingredients_list, split_by_status

                # Check if in canonical format
                if validate_ingredients_list(ingredients):
                    # Canonical format - show available vs needed
                    available, needed = split_by_status(ingredients)

                    if available:
                        st.markdown("*✅ Have:*")
                        for ing in available:
                            st.markdown(f"- {ing.get('item', 'Unknown')}")

                    if needed:
                        st.markdown("*🛒 Need:*")
                        for ing in needed:
                            st.markdown(f"- {ing.get('item', 'Unknown')}")

                    if not available and not needed:
                        st.markdown("*No ingredients listed*")
                else:
                    # Legacy format - simple list
                    for ing in ingredients:
                        if isinstance(ing, str):
                            st.markdown(f"- {ing}")
                        elif isinstance(ing, dict):
                            st.markdown(f"- {ing.get('item', str(ing))}")
            else:
                st.markdown("*No ingredients listed*")

    with st.expander("👨‍🍳 Cooking Instructions", expanded=False):
        instructions = recipe.get('instructions', 'No instructions')
        st.markdown(instructions)

    # ========================================================================
    # AI REFINEMENT SECTION
    # ========================================================================

    st.markdown("---")
    st.markdown("### 💬 Refine with AI")
    st.markdown("*Chat to adjust the recipe, then click 'Apply Changes' to update*")

    # Display chat history
    if st.session_state.capture_chat:
        st.markdown("**Conversation:**")
        for msg in st.session_state.capture_chat:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                st.markdown(f"**You:** {content}")
            else:
                st.markdown(f"**Assistant:** {content}")
        st.markdown("---")

    # Chat input
    col_input, col_send, col_apply = st.columns([3, 1, 1])

    with col_input:
        chat_input = st.text_input(
            "Your message",
            key="capture_chat_input",
            placeholder="e.g., 'make this vegetarian' or 'simplify the instructions'",
            label_visibility="collapsed"
        )

    with col_send:
        send_clicked = st.button("💬 Send", key="capture_send")

    with col_apply:
        apply_clicked = st.button("✨ Apply Changes", key="capture_apply", type="primary")

    # Handle Send - conversational chat
    if send_clicked and chat_input:
        with st.spinner("💬 Chatting..."):
            try:
                provider = get_smart_model()
                generator = RecipeGenerator(provider)

                # Add user message to chat history
                st.session_state.capture_chat.append({"role": "user", "content": chat_input})

                # Get AI response
                response = generator.chat_about_recipe(
                    recipe=recipe,
                    user_message=chat_input,
                    chat_history=st.session_state.capture_chat[:-1]  # Exclude the just-added message
                )

                # Add assistant response to chat history
                st.session_state.capture_chat.append({"role": "assistant", "content": response})

                logger.info(
                    "Chat message sent",
                    extra={"recipe_name": recipe.get("name"), "user_message": chat_input}
                )

                st.rerun()

            except Exception as e:
                st.error(f"❌ Chat error: {e}")
                logger.error(f"Chat failed: {e}", exc_info=True)

    # Handle Apply - regenerate recipe with all chat feedback
    if apply_clicked and st.session_state.capture_chat:
        with st.spinner("✨ Updating recipe..."):
            try:
                provider = get_smart_model()
                generator = RecipeGenerator(provider)

                # Combine all user messages into one refinement request
                all_changes = "\n".join([
                    msg["content"] for msg in st.session_state.capture_chat
                    if msg["role"] == "user"
                ])

                # Refine the recipe
                updated_recipe = generator.refine_recipe(
                    recipe=recipe,
                    user_message=all_changes,
                    chat_history=st.session_state.capture_chat
                )

                # Preserve captured recipe metadata
                if isinstance(updated_recipe, dict):
                    updated_recipe['source'] = RECIPE_SOURCE_CAPTURED
                    updated_recipe['tags'] = recipe.get('tags', ['captured'])
                    updated_recipe['rating'] = recipe.get('rating', 0)
                    updated_recipe['cook_count'] = recipe.get('cook_count', 0)

                    # Convert refined recipe ingredients to canonical format
                    from lib.ingredient_schema import from_comma_separated

                    canonical_ingredients = from_comma_separated(
                        updated_recipe.get('ingredients_available'),
                        updated_recipe.get('ingredients_needed')
                    )
                    if canonical_ingredients:
                        updated_recipe['ingredients'] = canonical_ingredients
                        logger.info(
                            "Converted refined recipe ingredients to canonical format",
                            extra={"recipe_name": updated_recipe.get("name"),
                                   "ingredient_count": len(canonical_ingredients)}
                        )

                    # Update session state
                    st.session_state.captured_recipe = updated_recipe
                    st.session_state.capture_chat = []

                    logger.info(
                        "Recipe updated successfully",
                        extra={"recipe_name": updated_recipe.get("name")}
                    )

                    st.success("✅ Recipe updated!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update recipe. Please try again.")

            except Exception as e:
                st.error(f"❌ Update error: {e}")
                logger.error(f"Recipe update failed: {e}", exc_info=True)

    # ========================================================================
    # ACTION BUTTONS
    # ========================================================================

    st.markdown("---")
    st.markdown("### 🎯 What would you like to do?")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save to Library", key="save_captured", type="primary", use_container_width=True):
            try:
                if save_recipe(recipe):
                    st.success("✅ Saved to recipe library!")
                    logger.info(
                        "Recipe saved to library",
                        extra={"recipe_name": recipe.get("name")}
                    )

                    # Clear session state
                    st.session_state.captured_recipe = None
                    st.session_state.capture_chat = []

                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to save recipe. Please try again.")

            except Exception as e:
                st.error(f"❌ Save error: {e}")
                logger.error(f"Failed to save recipe: {e}", exc_info=True)

    with col2:
        if st.button("📅 Add to Plan", key="plan_captured", use_container_width=True):
            try:
                # Save recipe first if not already saved
                save_recipe(recipe)

                # Add to weekly plan
                if add_recipe_to_plan(recipe):
                    st.success("✅ Added to weekly plan!")
                    logger.info(
                        "Recipe added to plan",
                        extra={"recipe_name": recipe.get("name")}
                    )
                else:
                    st.error("❌ Failed to add to plan. Please try again.")

            except Exception as e:
                st.error(f"❌ Plan error: {e}")
                logger.error(f"Failed to add to plan: {e}", exc_info=True)

    with col3:
        # Check if recipe is in Recipe Book
        recipe_id = recipe.get('id')
        if recipe_id and is_in_recipe_book(recipe_id):
            st.button("✅ In Book", key="in_book_captured", disabled=True, use_container_width=True)
        else:
            if st.button("📚 Recipe Book", key="save_book_captured", use_container_width=True):
                try:
                    # Ensure recipe has an ID
                    if not recipe_id:
                        import uuid
                        recipe['id'] = str(uuid.uuid4())

                    # Save to library first
                    save_recipe(recipe)

                    if add_to_recipe_book(recipe):
                        st.success("✅ Saved to Recipe Book!")
                        logger.info(
                            "Recipe added to book",
                            extra={"recipe_name": recipe.get("name")}
                        )
                        st.rerun()
                    else:
                        st.error("❌ Failed to save to Recipe Book")

                except Exception as e:
                    st.error(f"❌ Book error: {e}")
                    logger.error(f"Failed to add to book: {e}", exc_info=True)

    with col4:
        if st.button("🗑️ Discard", key="discard_captured", use_container_width=True):
            # Clear session state
            st.session_state.captured_recipe = None
            st.session_state.capture_chat = []

            logger.info("Recipe discarded by user")
            st.info("Recipe discarded. Upload a new image to start over.")
            st.rerun()

# ============================================================================
# FOOTER / HELP TEXT
# ============================================================================

if not st.session_state.captured_recipe and not uploaded_files:
    st.markdown("---")
    st.markdown("### 📱 Tips for Best Results")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Good Images:**
        - Clear screenshots from recipe websites
        - High-resolution photos
        - Full recipe visible (ingredients + instructions)
        - Good lighting and focus
        - **Multi-page?** Upload all pages in order!
        """)

    with col2:
        st.markdown("""
        **What AI Extracts:**
        - Recipe name and description
        - Complete ingredients list with quantities (from all pages)
        - Step-by-step cooking instructions (from all pages)
        - Cooking time and difficulty level
        - **Multi-page recipes are automatically combined!**
        """)
