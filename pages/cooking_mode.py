"""Cooking Mode - Interactive Recipe Assistant.

Display active recipe and provide AI chat for cooking questions.
"""

from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from lib.active_recipe_manager import clear_active_recipe, load_active_recipe
from lib.auth import require_authentication
from lib.chat_manager import clear_chat_history, load_chat_history, save_chat_history
from lib.llm_agents import ClaudeProvider
from lib.logging_config import get_logger, setup_logging
from lib.recipe_feedback import (
    save_recipe_feedback,
    update_pantry_after_cooking,
)
from lib.recipe_store import update_recipe_stats
from lib.ui import apply_styling, render_header, render_metric_card

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
# Note: Feedback and pantry functions now imported from lib/recipe_feedback.py


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="Cooking Mode - AI Recipe Planner",
    page_icon="👨‍🍳",
    layout="wide",
)

# Apply custom styling
apply_styling()

# Authentication
require_authentication()

render_header(
    title="Cooking Mode",
    subtitle="Your interactive AI cooking assistant",
    icon="👨‍🍳"
)

# Check if a recipe is active - try session state first, then persistent storage
if 'active_recipe' not in st.session_state or st.session_state['active_recipe'] is None:
    # Try loading from persistent storage
    persisted_recipe = load_active_recipe()

    if persisted_recipe:
        # Restore to session state
        st.session_state['active_recipe'] = persisted_recipe
        logger.info(
            "Restored active recipe from persistent storage",
            extra={"recipe_name": persisted_recipe.get('name')}
        )
    else:
        # No recipe found anywhere
        st.warning("⚠️ No active recipe selected!")
        st.info("Please go to **Recipe Generator** or **Weekly Planner** and click '👨‍🍳 Cook' on a recipe to start cooking mode.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Go to Recipe Generator", use_container_width=True):
                st.switch_page("pages/generate_recipes.py")
        with col2:
            if st.button("📅 Go to Weekly Planner", use_container_width=True):
                st.switch_page("pages/weekly_planner.py")

        st.stop()

# Get active recipe
recipe = st.session_state['active_recipe']

# Initialize chat history - try session state, then persistent storage
if 'cooking_chat_history' not in st.session_state or not st.session_state['cooking_chat_history']:
    # Try loading from disk
    persisted_history = load_chat_history()
    if persisted_history:
        st.session_state['cooking_chat_history'] = persisted_history
    else:
        st.session_state['cooking_chat_history'] = []

# Display recipe details
st.markdown("---")
st.markdown(f"## 🍽️ {recipe['name']}")

# Recipe metadata
col1, col2 = st.columns(2)
with col1:
    render_metric_card("⏱️ Time", f"{recipe.get('time_minutes', '?')} min")
with col2:
    render_metric_card("📊 Difficulty", (recipe.get('difficulty') or 'medium').title())

# Recipe description
if recipe.get('description'):
    st.markdown(f"*{recipe['description']}*")

# Ingredients (just what you have - you're already cooking!)
st.markdown("### 📋 Ingredients")
available = recipe.get("ingredients_available", "")
needed = recipe.get("ingredients_needed", "")

# Combine all ingredients
all_ingredients = []
if available:
    all_ingredients.extend([item.strip() for item in available.split(",")])
if needed and needed.strip():
    all_ingredients.extend([item.strip() for item in needed.split(",")])

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

# Cooking instructions (prominently displayed for active cooking)
if "instructions" in recipe and recipe["instructions"]:
    st.markdown("---")
    st.markdown("### 👨‍🍳 Cooking Instructions")
    st.markdown(recipe["instructions"])

# Reason for suggestion
if "reason" in recipe:
    st.info(f"**Why this recipe:** {recipe['reason']}")

st.markdown("---")

# Chat interface
st.markdown("### 💬 Ask Me Anything About This Recipe")
st.caption("I'm here to help while you cook! Ask about substitutions, techniques, timing, or troubleshooting.")

# Chat history display
chat_container = st.container()

with chat_container:
    if st.session_state['cooking_chat_history']:
        for message in st.session_state['cooking_chat_history']:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**AI Chef:** {message['content']}")
            st.markdown("")
    else:
        st.info("💡 **Example questions:**\n- Can I use X instead of Y?\n- How do I know when it's done?\n- Can I prepare this ahead of time?\n- My sauce is too thick, what should I do?")

# Chat input
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Your question:",
        placeholder="Type your question here...",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        submit = st.form_submit_button("Send 💬", use_container_width=True, type="primary")

    with col2:
        clear_chat = st.form_submit_button("Clear Chat", use_container_width=True)

# Handle clear chat
if clear_chat:
    st.session_state['cooking_chat_history'] = []
    clear_chat_history()
    logger.info("Cooking chat history cleared")
    st.rerun()

# Handle user question
if submit and user_input:
    # Add user message to history
    st.session_state['cooking_chat_history'].append({
        'role': 'user',
        'content': user_input
    })

    # Save to disk
    save_chat_history(st.session_state['cooking_chat_history'])

    logger.info(
        "User asked cooking question",
        extra={"question": user_input, "recipe": recipe['name']}
    )

    # Generate AI response
    with st.spinner("🤔 Thinking..."):
        try:
            # Initialize Claude provider
            provider = ClaudeProvider()

            # Get last 10 messages for context (5 exchanges)
            recent_history = st.session_state['cooking_chat_history'][-10:]

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
            st.session_state['cooking_chat_history'].append({
                'role': 'assistant',
                'content': response
            })

            # Save to disk
            save_chat_history(st.session_state['cooking_chat_history'])

            logger.info(
                "AI response generated",
                extra={"response_length": len(response), "history_size": len(st.session_state['cooking_chat_history'])}
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

# Show feedback modal or action buttons
st.markdown("---")

# Check if we should show feedback modal
if st.session_state.get('show_cooking_feedback', False):
    st.markdown(f"## 🎉 You cooked: {recipe.get('name', 'Unknown')}")
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

        # Submit buttons
        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("✅ Save Rating", use_container_width=True, type="primary")

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            # Save the feedback
            success = save_recipe_feedback(
                recipe=recipe,
                rating=rating,
                make_again=make_again,
                notes=notes
            )

            if success:
                # Update recipe stats in recipe store
                if recipe.get('id'):
                    update_recipe_stats(recipe['id'], cooked=True)
                    logger.info(f"Updated recipe stats for {recipe.get('name')}")

                st.success("✅ Feedback saved! Meal logged to history.")
                # Set flag to show pantry update prompt
                st.session_state['show_cooking_feedback'] = False
                st.session_state['feedback_saved_show_pantry_prompt'] = True
                st.rerun()
            else:
                st.error("❌ Failed to save feedback. Please try again.")

        if cancel:
            # Clear modal state
            st.session_state['show_cooking_feedback'] = False
            logger.info("Feedback cancelled")
            st.rerun()

# Show pantry update prompt after feedback is saved
elif st.session_state.get('feedback_saved_show_pantry_prompt', False):
    st.markdown("---")
    st.markdown("## 🥫 Update Pantry")
    st.info("**Would you like to update your pantry by removing the ingredients you used?**\n\n"
            "We'll keep staples like oil and spices, but remove fresh items and consumables.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Yes, Update Pantry", key="update_pantry_yes", use_container_width=True, type="primary"):
            # Call pantry update function
            update_success = update_pantry_after_cooking(recipe)

            if update_success:
                st.success("✅ Pantry updated!")
                logger.info("Pantry updated after cooking", extra={"recipe_name": recipe['name']})
            else:
                st.warning("⚠️ Could not update pantry automatically. You can do it manually in the Pantry page.")

            # Clear all modal state and redirect
            st.session_state['feedback_saved_show_pantry_prompt'] = False
            if 'active_recipe' in st.session_state:
                del st.session_state['active_recipe']
            if 'cooking_chat_history' in st.session_state:
                del st.session_state['cooking_chat_history']

            # Clear persistent storage
            clear_active_recipe()
            clear_chat_history()

            import time
            time.sleep(1.5)
            st.switch_page("app.py")

    with col2:
        if st.button("❌ No Thanks", key="update_pantry_no", use_container_width=True):
            # Clear all modal state and redirect
            st.session_state['feedback_saved_show_pantry_prompt'] = False
            if 'active_recipe' in st.session_state:
                del st.session_state['active_recipe']
            if 'cooking_chat_history' in st.session_state:
                del st.session_state['cooking_chat_history']

            # Clear persistent storage
            clear_active_recipe()
            clear_chat_history()

            logger.info("User declined pantry update")
            st.switch_page("app.py")

else:
    # Show normal action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Finished Cooking", use_container_width=True, type="primary"):
            # Set flag to show feedback modal
            st.session_state['show_cooking_feedback'] = True
            logger.info(
                "User finished cooking",
                extra={"recipe_name": recipe['name']}
            )
            st.rerun()

    with col2:
        if st.button("🔙 Back to Recipes", use_container_width=True):
            # Clear active recipe but keep it in session for potential return
            logger.info("User returned to recipe list")
            st.switch_page("pages/generate_recipes.py")

    with col3:
        if st.button("🏠 Home", use_container_width=True):
            logger.info("User returned to home from cooking mode")
            st.switch_page("app.py")

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">'
        "💡 <b>Tip:</b> Keep this page open while cooking and ask questions anytime!"
        "</div>",
        unsafe_allow_html=True,
    )
