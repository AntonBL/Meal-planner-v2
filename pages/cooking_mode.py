"""Cooking Mode - Interactive Multi-Recipe Assistant.

Display active recipes with tabs and provide AI chat for cooking questions.
Supports cooking multiple recipes simultaneously with independent chat contexts.
"""

from lib.mobile_ui import add_mobile_styles
from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from lib.active_recipe_manager import (
    add_active_recipe,
    clear_active_recipes,
    load_active_recipes,
    remove_active_recipe,
    save_active_recipes,
)
from lib.auth import require_authentication
from lib.chat_manager import (
    clear_all_recipe_chats,
    clear_recipe_chat_history,
    load_recipe_chat_history,
    save_recipe_chat_history,
)
from lib.exceptions import LLMAPIError, RecipeParsingError
from lib.generated_recipes_manager import load_generated_recipes, save_generated_recipes
from lib.llm_agents import RecipeGenerator
from lib.llm_core import get_smart_model
from lib.logging_config import get_logger, setup_logging
from lib.recipe_book_manager import add_to_recipe_book, is_in_recipe_book
from lib.recipe_feedback import (
    save_recipe_feedback,
    update_pantry_after_cooking,
)
from lib.recipe_store import update_recipe_stats, load_recipes
from lib.ui import apply_styling, render_header, render_metric_card

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="Cooking Mode - AI Recipe Planner",
    page_icon="👨‍🍳",
    layout="wide",
)

# Authentication
require_authentication()

# Apply mobile styles
add_mobile_styles()

render_header(
    title="Cooking Mode",
    subtitle="Your interactive AI cooking assistant - now with multi-recipe support!",
    icon="👨‍🍳"
)

# Add print-friendly CSS
st.markdown("""
<style>
    @media print {
        /* Hide Streamlit elements when printing */
        header, footer, .stApp > header, [data-testid="stSidebar"],
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        .stButton, button, .stTabs, [role="tablist"] {
            display: none !important;
        }

        /* Show only the recipe content */
        .print-recipe {
            display: block !important;
        }

        /* Clean page layout */
        body {
            margin: 0;
            padding: 20px;
        }

        /* Recipe title */
        h1, h2 {
            color: #000 !important;
            page-break-after: avoid;
        }

        /* Ingredient and instruction lists */
        ul, ol {
            page-break-inside: avoid;
        }

        /* Avoid breaking in the middle of instructions */
        p {
            page-break-inside: avoid;
        }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# LOAD ACTIVE RECIPES
# ============================================================================

# Load all active recipes from persistent storage
active_recipes = load_active_recipes()

# If no recipes, show helper UI
if not active_recipes:
    st.warning("⚠️ No active recipes selected!")
    st.info("Please go to **Weekly Planner** or **Recipe Generator** and click '👨‍🍳 Cook' on a recipe to start cooking mode.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Go to Recipe Generator", use_container_width=True):
            st.switch_page("pages/generate_recipes.py")
    with col2:
        if st.button("📅 Go to Weekly Planner", use_container_width=True):
            st.switch_page("pages/weekly_planner.py")

    st.stop()


# Initialize session state for current recipe index
if 'current_recipe_index' not in st.session_state:
    st.session_state['current_recipe_index'] = 0

# Ensure index is valid
if st.session_state['current_recipe_index'] >= len(active_recipes):
    st.session_state['current_recipe_index'] = 0


# ============================================================================
# RECIPE TABS
# ============================================================================

st.markdown("---")

# Create tab labels
tab_labels = []
for i, recipe in enumerate(active_recipes):
    # Emoji based on recipe type or just use cooking emoji
    name = recipe.get('name', 'Recipe')
    # Truncate long names for tabs
    short_name = name[:20] + "..." if len(name) > 20 else name
    tab_labels.append(f"{short_name}")

# Add "+" tab for adding more recipes
tab_labels.append("➕ Add Recipe")

# Create tabs
tabs = st.tabs(tab_labels)

# Process each recipe tab
for tab_idx, tab in enumerate(tabs[:-1]):  # Exclude the "Add Recipe" tab
    with tab:
        recipe = active_recipes[tab_idx]
        recipe_id = recipe.get('id', recipe.get('name', 'unknown'))

        # Display recipe header and close button
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"## 🍽️ {recipe['name']}")
        with col2:
            if st.button("✕ Close", key=f"close_recipe_{tab_idx}", help="Remove this recipe from cooking mode"):
                # Remove this recipe
                if remove_active_recipe(recipe_id):
                    logger.info(f"Removed recipe from cooking mode: {recipe.get('name')}")
                    st.rerun()
                else:
                    st.error("Failed to remove recipe")

        # Recipe metadata
        col1, col2 = st.columns(2)
        with col1:
            render_metric_card("⏱️ Time", f"{recipe.get('time_minutes', '?')} min")
        with col2:
            render_metric_card("📊 Difficulty", (recipe.get('difficulty') or 'medium').title())

        # Recipe description
        if recipe.get('description'):
            st.markdown(f"*{recipe['description']}*")

        st.markdown("---")

        # Section tabs within each recipe
        recipe_section_tabs = st.tabs(["📋 Ingredients", "👨‍🍳 Instructions", "💬 Chat"])

        # ===== INGREDIENTS TAB =====
        with recipe_section_tabs[0]:
            # Use canonical schema to get ingredients
            from lib.ingredient_schema import from_legacy_recipe, to_string_list

            canonical_ingredients = from_legacy_recipe(recipe)
            all_ingredients = to_string_list(canonical_ingredients) if canonical_ingredients else []

            if all_ingredients:
                # Display in 2 columns for better readability
                col1, col2 = st.columns(2)
                mid_point = len(all_ingredients) // 2

                with col1:
                    for item in all_ingredients[:mid_point]:
                        st.markdown(f"- {item}")

                with col2:
                    for item in all_ingredients[mid_point:]:
                        st.markdown(f"- {item}")
            else:
                st.markdown("*No ingredients listed*")

        # ===== INSTRUCTIONS TAB =====
        with recipe_section_tabs[1]:
            if "instructions" in recipe and recipe["instructions"]:
                st.markdown(recipe["instructions"])
            else:
                st.info("No instructions available for this recipe.")

            # Reason for suggestion
            if "reason" in recipe:
                st.info(f"**Why this recipe:** {recipe['reason']}")

        # ===== CHAT TAB =====
        with recipe_section_tabs[2]:
            # Load chat history for this specific recipe
            chat_history_key = f'chat_history_{recipe_id}'

            # Initialize chat history for this recipe
            if chat_history_key not in st.session_state:
                persisted_history = load_recipe_chat_history(recipe_id)
                st.session_state[chat_history_key] = persisted_history

            st.markdown("### 💬 Ask Me About This Recipe")
            st.caption("I'm here to help while you cook! Ask about substitutions, techniques, timing, troubleshooting, or discuss recipe modifications.")

            # Chat history display
            if st.session_state[chat_history_key]:
                for message in st.session_state[chat_history_key]:
                    if message['role'] == 'user':
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**AI Chef:** {message['content']}")
                    st.markdown("")
            else:
                st.info("💡 **Example questions:**\n- Can I use X instead of Y?\n- How do I know when it's done?\n- Can I prepare this ahead of time?\n- My sauce is too thick, what should I do?")

            # Chat input
            with st.form(f"chat_form_{tab_idx}", clear_on_submit=True):
                user_input = st.text_input(
                    "Your question:",
                    placeholder="Ask about cooking or suggest recipe changes...",
                    label_visibility="collapsed",
                    key=f"chat_input_{tab_idx}"
                )

                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    submit = st.form_submit_button("Send 💬", use_container_width=True, type="primary")

                with col2:
                    update_recipe_btn = st.form_submit_button("✨ Update Recipe", use_container_width=True)

                with col3:
                    clear_chat = st.form_submit_button("Clear Chat", use_container_width=True)

            # Handle clear chat
            if clear_chat:
                st.session_state[chat_history_key] = []
                clear_recipe_chat_history(recipe_id)
                logger.info(f"Chat history cleared for recipe: {recipe.get('name')}")
                st.rerun()

            # Handle Update Recipe button
            if update_recipe_btn:
                if st.session_state[chat_history_key]:
                    with st.spinner("✨ Updating recipe with your changes..."):
                        try:
                            # Initialize provider and generator
                            provider = get_smart_model()
                            generator = RecipeGenerator(provider)

                            # Build a summary of all user messages
                            all_changes = "\n".join([
                                msg["content"] for msg in st.session_state[chat_history_key]
                                if msg["role"] == "user"
                            ])

                            # Call refine_recipe with full conversation context
                            updated_recipe = generator.refine_recipe(
                                recipe=recipe,
                                user_message=all_changes,
                                chat_history=st.session_state[chat_history_key]
                            )

                            # Update in active recipes list
                            active_recipes[tab_idx] = updated_recipe
                            save_active_recipes(active_recipes)

                            logger.info(
                                "Recipe updated from cooking chat",
                                extra={
                                    "recipe_name": recipe["name"],
                                    "changes": all_changes
                                }
                            )

                            st.success("✅ Recipe updated successfully!")
                            st.rerun()

                        except LLMAPIError as e:
                            st.error(f"❌ API Error: {str(e)}")
                            logger.error("LLM API error during recipe update", exc_info=True)
                        except RecipeParsingError as e:
                            st.error(f"❌ Parsing Error: {str(e)}")
                            logger.error("Recipe parsing error during update", exc_info=True)
                        except Exception as e:
                            st.error(f"❌ Unexpected Error: {str(e)}")
                            logger.error("Unexpected error during recipe update", exc_info=True)
                else:
                    st.info("💡 Have a conversation about changes you'd like first, then click 'Update Recipe' to apply them!")

            # Handle user question
            if submit and user_input:
                # Add user message to history
                st.session_state[chat_history_key].append({
                    'role': 'user',
                    'content': user_input
                })

                # Save to disk
                save_recipe_chat_history(recipe_id, st.session_state[chat_history_key])

                logger.info(
                    "User asked cooking question",
                    extra={"question": user_input, "recipe": recipe['name']}
                )

                # Generate AI response
                with st.spinner("🤔 Thinking..."):
                    try:
                        # Initialize LLM provider
                        provider = get_smart_model()

                        # Get last 10 messages for context (5 exchanges)
                        recent_history = st.session_state[chat_history_key][-10:]

                        # Get ingredients for context
                        from lib.ingredient_schema import from_legacy_recipe, to_string_list
                        canonical_ingredients = from_legacy_recipe(recipe)
                        all_ingredients = to_string_list(canonical_ingredients) if canonical_ingredients else []

                        # Build conversation history
                        conversation_context = ""
                        if len(recent_history) > 1:  # More than just the current question
                            conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
                            for msg in recent_history[:-1]:  # Exclude current question
                                role_label = "User" if msg['role'] == 'user' else "Assistant"
                                conversation_context += f"{role_label}: {msg['content']}\n"

                        # Build context-aware prompt
                        prompt = f"""You are a helpful cooking assistant. The user is currently cooking the following recipe:

RECIPE: {recipe['name']}
DESCRIPTION: {recipe.get('description', 'N/A')}
TIME: {recipe.get('time_minutes', '?')} minutes
DIFFICULTY: {recipe.get('difficulty', 'medium')}

INGREDIENTS:
{', '.join(all_ingredients) if all_ingredients else 'N/A'}
{conversation_context}

CURRENT QUESTION: {user_input}

Please provide a helpful, practical answer. Be concise but thorough. If suggesting substitutions, consider the ingredients in this recipe. If explaining techniques, be clear and specific.

Keep your response to 2-3 paragraphs maximum."""

                        # Get AI response
                        response = provider.generate(prompt, max_tokens=500)

                        # Add AI response to history
                        st.session_state[chat_history_key].append({
                            'role': 'assistant',
                            'content': response
                        })

                        # Save to disk
                        save_recipe_chat_history(recipe_id, st.session_state[chat_history_key])

                        logger.info(
                            "AI response generated",
                            extra={"response_length": len(response), "history_size": len(st.session_state[chat_history_key])}
                        )

                        # Rerun to display new messages
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to get AI response: {str(e)}")
                        logger.error(
                            "Failed to generate AI response in cooking mode",
                            extra={"error": str(e)},
                            exc_info=True
                        )

        # ===== ACTION BUTTONS (Per Recipe) =====
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Finished This Recipe", key=f"finish_{tab_idx}", use_container_width=True, type="primary"):
                # Store which recipe we're finishing
                st.session_state['finishing_recipe_id'] = recipe_id
                st.session_state['finishing_recipe'] = recipe
                st.session_state['show_cooking_feedback'] = True
                logger.info(f"User finished cooking: {recipe.get('name')}")
                st.rerun()

        with col2:
            # Print button using Streamlit components for proper JavaScript execution
            import streamlit.components.v1 as components

            components.html("""
                <button onclick="window.print()" style="
                    width: 100%;
                    padding: 0.5rem 1rem;
                    background-color: #f0f2f6;
                    border: 1px solid #d3d3d3;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-size: 1rem;
                    font-weight: 400;
                    transition: all 0.2s;
                " onmouseover="this.style.backgroundColor='#e0e2e6'; this.style.borderColor='#b3b3b3';"
                   onmouseout="this.style.backgroundColor='#f0f2f6'; this.style.borderColor='#d3d3d3';">
                    🖨️ Print Recipe
                </button>
            """, height=50)

        with col3:
            # Show recipe book button
            recipe_id_for_book = recipe.get('id')
            if recipe_id_for_book and is_in_recipe_book(recipe_id_for_book):
                st.button("✅ In Recipe Book", key=f"in_book_{tab_idx}", disabled=True, use_container_width=True)
            else:
                if st.button("📚 Add to Recipe Book", key=f"add_book_{tab_idx}", use_container_width=True):
                    if recipe_id_for_book:
                        if add_to_recipe_book(recipe):
                            st.success("✅ Added to Recipe Book!")
                            st.rerun()
                        else:
                            st.error("Failed to add to Recipe Book")
                    else:
                        st.warning("Recipe missing ID")


# ===== ADD RECIPE TAB =====
with tabs[-1]:
    st.markdown("### ➕ Add Another Recipe to Cook")
    st.info("Select a recipe from your collection to add to your cooking session")

    # Load available recipes
    all_recipes = load_recipes()

    # Filter out recipes already in active cooking
    active_recipe_ids = {r.get('id') for r in active_recipes}
    active_recipe_names = {r.get('name') for r in active_recipes}

    available_recipes = [
        r for r in all_recipes
        if r.get('id') not in active_recipe_ids and r.get('name') not in active_recipe_names
    ]

    if not available_recipes:
        st.warning("No more recipes available. You've already added all your saved recipes to cooking mode!")
    else:
        # Search filter
        search = st.text_input("🔍 Search recipes", placeholder="Type to filter...", key="add_recipe_search")

        # Filter by search
        if search:
            available_recipes = [r for r in available_recipes if search.lower() in r['name'].lower()]

        st.markdown(f"**{len(available_recipes)} recipes available**")
        st.markdown("---")

        # Display in cards
        for recipe in available_recipes[:10]:  # Limit to first 10
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{recipe['name']}**")
                meta = []
                if recipe.get('time_minutes'):
                    meta.append(f"⏱️ {recipe['time_minutes']} min")
                if recipe.get('difficulty'):
                    meta.append(f"📊 {recipe['difficulty'].title()}")
                if meta:
                    st.caption(" • ".join(meta))

            with col2:
                if st.button("➕ Add", key=f"add_{recipe.get('id', recipe['name'])}", use_container_width=True):
                    if add_active_recipe(recipe):
                        st.success(f"✅ Added {recipe['name']}!")
                        logger.info(f"Added recipe to cooking mode: {recipe['name']}")
                        st.rerun()
                    else:
                        st.error("Failed to add recipe")

            st.markdown("")


# ============================================================================
# FEEDBACK MODAL (Shown After Finishing a Recipe)
# ============================================================================

st.markdown("---")

# Check if we should show feedback modal
if st.session_state.get('show_cooking_feedback', False):
    finishing_recipe = st.session_state.get('finishing_recipe')

    if finishing_recipe:
        st.markdown(f"## 🎉 You cooked: {finishing_recipe.get('name', 'Unknown')}")
        st.markdown("**How was it? Please rate your experience:**")

        with st.form("cooking_feedback_form"):
            # Star rating
            rating = st.radio(
                "Rating:",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: "⭐" * x,
                horizontal=True,
                index=4  # Default to 5 stars
            )

            # Make again?
            make_again = st.radio(
                "Would you make this again?",
                options=["Yes", "No", "Maybe"],
                horizontal=True
            )

            # Notes
            notes = st.text_area(
                "Notes (optional):",
                placeholder="What did you think? Any changes you'd make?",
                height=100
            )

            # Save to Recipe Book checkbox (only show for high ratings)
            save_to_book = False
            if rating >= 4:
                recipe_id = finishing_recipe.get('id')
                if recipe_id and is_in_recipe_book(recipe_id):
                    st.info("✅ This recipe is already in your Recipe Book!")
                else:
                    save_to_book = st.checkbox(
                        "📚 Save to Recipe Book",
                        value=False,
                        help="Add this recipe to your curated collection"
                    )

            # Submit buttons
            col1, col2 = st.columns(2)

            with col1:
                submit = st.form_submit_button("✅ Save Rating", use_container_width=True, type="primary")

            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit:
                # Save the feedback
                success = save_recipe_feedback(
                    recipe=finishing_recipe,
                    rating=rating,
                    make_again=make_again,
                    notes=notes
                )

                if success:
                    # Update recipe stats in recipe store
                    if finishing_recipe.get('id'):
                        update_recipe_stats(finishing_recipe.get('id'), cooked=True)

                    # Save to Recipe Book if checkbox was checked
                    if save_to_book and finishing_recipe.get('id'):
                        if add_to_recipe_book(finishing_recipe):
                            st.success("✅ Feedback saved and added to Recipe Book!")
                        else:
                            st.success("✅ Feedback saved! (Recipe Book save failed)")
                    else:
                        st.success("✅ Feedback saved! Meal logged to history.")

                    # Remove this recipe from active recipes
                    finishing_recipe_id = st.session_state.get('finishing_recipe_id')
                    if finishing_recipe_id:
                        remove_active_recipe(finishing_recipe_id)
                        # Clear chat history for this recipe
                        clear_recipe_chat_history(finishing_recipe_id)

                    # Clear feedback state
                    st.session_state['show_cooking_feedback'] = False
                    st.session_state['finishing_recipe_id'] = None
                    st.session_state['finishing_recipe'] = None

                    # Set flag to show pantry update prompt
                    st.session_state['feedback_saved_show_pantry_prompt'] = True
                    st.session_state['finished_recipe'] = finishing_recipe
                    st.rerun()
                else:
                    st.error("❌ Failed to save feedback. Please try again.")

            if cancel:
                # Clear modal state
                st.session_state['show_cooking_feedback'] = False
                st.session_state['finishing_recipe_id'] = None
                st.session_state['finishing_recipe'] = None
                st.rerun()

# Show pantry update prompt after feedback is saved
elif st.session_state.get('feedback_saved_show_pantry_prompt', False):
    finished_recipe = st.session_state.get('finished_recipe')

    if finished_recipe:
        st.markdown("## 🥫 Update Pantry")
        st.info("**Would you like to update your pantry by removing the ingredients you used?**\n\n"
                "We'll keep staples like oil and spices, but remove fresh items and consumables.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Yes, Update Pantry", key="update_pantry_yes", use_container_width=True, type="primary"):
                # Call pantry update function
                update_success = update_pantry_after_cooking(finished_recipe)

                if update_success:
                    st.success("✅ Pantry updated!")
                else:
                    st.warning("⚠️ Could not update pantry automatically. You can do it manually in the Pantry page.")

                # Clear pantry prompt state
                st.session_state['feedback_saved_show_pantry_prompt'] = False
                st.session_state['finished_recipe'] = None

                # Check if there are still active recipes
                remaining_recipes = load_active_recipes()
                if not remaining_recipes:
                    # All done, go home
                    import time
                    time.sleep(1.5)
                    st.switch_page("app.py")
                else:
                    # Still cooking other recipes
                    st.rerun()

        with col2:
            if st.button("❌ No Thanks", key="update_pantry_no", use_container_width=True):
                # Clear pantry prompt state
                st.session_state['feedback_saved_show_pantry_prompt'] = False
                st.session_state['finished_recipe'] = None

                # Check if there are still active recipes
                remaining_recipes = load_active_recipes()
                if not remaining_recipes:
                    # All done, go home
                    st.switch_page("app.py")
                else:
                    # Still cooking other recipes
                    st.rerun()

else:
    # Show global action buttons
    st.markdown("### 🎯 Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Finish All Recipes", use_container_width=True, type="primary", help="Mark all recipes as finished"):
            # This would be complex - for now, direct user to finish individually
            st.info("💡 Please finish each recipe individually using the '✅ Finished This Recipe' button in each tab.")

    with col2:
        if st.button("🔙 Back to Planner", use_container_width=True):
            logger.info("User returned to weekly planner")
            st.switch_page("pages/weekly_planner.py")

    with col3:
        if st.button("🏠 Home", use_container_width=True):
            logger.info("User returned to home from cooking mode")
            st.switch_page("app.py")

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">'
        "💡 <b>Tip:</b> Keep this page open while cooking and switch between recipe tabs as needed!"
        "</div>",
        unsafe_allow_html=True,
    )
