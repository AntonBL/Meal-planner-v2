"""Cooking Mode - Interactive Recipe Assistant.

Display active recipe and provide AI chat for cooking questions.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime

from lib.auth import require_authentication
from lib.llm_agents import ClaudeProvider
from lib.logging_config import get_logger, setup_logging
from lib.file_manager import get_data_file_path
from lib.active_recipe_manager import load_active_recipe, clear_active_recipe

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_staple_ingredient(ingredient_name: str) -> bool:
    """Check if an ingredient is a staple that shouldn't be removed after one use.

    Args:
        ingredient_name: Name of the ingredient

    Returns:
        True if it's a staple (keep), False if consumable (remove)
    """
    ingredient_lower = ingredient_name.lower()

    # Staple keywords - these items are NOT removed after cooking
    staple_keywords = [
        # Oils and fats
        'oil', 'olive oil', 'vegetable oil', 'canola oil', 'sesame oil',
        'coconut oil', 'butter', 'ghee',

        # Sauces and condiments
        'soy sauce', 'tamari', 'vinegar', 'hot sauce', 'sriracha',
        'ketchup', 'mustard', 'mayo', 'mayonnaise',

        # Spices and herbs (dried)
        'salt', 'pepper', 'cumin', 'paprika', 'oregano', 'basil',
        'thyme', 'rosemary', 'cinnamon', 'ginger powder', 'garlic powder',
        'onion powder', 'chili powder', 'curry powder', 'turmeric',
        'coriander', 'cayenne', 'nutmeg', 'cloves',

        # Baking and cooking basics
        'flour', 'sugar', 'brown sugar', 'baking soda', 'baking powder',
        'yeast', 'cornstarch', 'vanilla extract',

        # Grains and pasta (dried/shelf-stable)
        'rice', 'pasta', 'noodles', 'quinoa', 'couscous', 'lentils',
        'beans', 'chickpeas',

        # Other shelf-stable items
        'stock', 'broth', 'tomato paste', 'tomato sauce', 'canned tomatoes',
        'honey', 'maple syrup', 'peanut butter', 'tahini',
    ]

    # Check if any staple keyword matches
    for keyword in staple_keywords:
        if keyword in ingredient_lower:
            return True

    return False


def update_pantry_after_cooking(recipe: dict) -> bool:
    """Update pantry by removing consumable ingredients used in recipe.

    Staples like oil, soy sauce, and spices are kept in pantry.
    Fresh items and consumables are removed.

    Args:
        recipe: Recipe dictionary with ingredients

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all ingredients from recipe
        ingredients = []

        if recipe.get('ingredients_available'):
            ingredients.extend([i.strip() for i in recipe['ingredients_available'].split(',')])

        if recipe.get('ingredients_needed'):
            ingredients.extend([i.strip() for i in recipe['ingredients_needed'].split(',')])

        if not ingredients:
            logger.warning("No ingredients to update pantry with")
            return True

        # Categorize ingredients
        items_to_remove = []
        staples_kept = []

        for ingredient in ingredients:
            if is_staple_ingredient(ingredient):
                staples_kept.append(ingredient)
            else:
                items_to_remove.append(ingredient)

        # Remove consumable items from pantry files
        removed_count = 0

        for file_name in ['staples', 'fresh']:
            file_path = get_data_file_path(file_name)
            content = file_path.read_text(encoding="utf-8")
            lines = content.split('\n')
            new_lines = []

            for line in lines:
                line_stripped = line.strip().lower()

                # Check if this line contains an ingredient to remove
                should_remove = False
                for item in items_to_remove:
                    if line_stripped.startswith('-') and item.lower() in line_stripped:
                        should_remove = True
                        removed_count += 1
                        logger.info(f"Removing from pantry: {item}")
                        break

                if not should_remove:
                    new_lines.append(line)

            # Write back
            file_path.write_text('\n'.join(new_lines), encoding="utf-8")

        # Add usage note
        today = datetime.now().strftime("%Y-%m-%d")
        note = f"\n<!-- Cooked {recipe['name']} on {today}"
        if staples_kept:
            note += f" | Staples used (not removed): {', '.join(staples_kept)}"
        if items_to_remove:
            note += f" | Removed: {', '.join(items_to_remove)}"
        note += " -->\n"

        # Add note to staples file
        staples_path = get_data_file_path("staples")
        staples_content = staples_path.read_text(encoding="utf-8")
        staples_path.write_text(staples_content + note, encoding="utf-8")

        logger.info(
            "Updated pantry after cooking",
            extra={
                "recipe_name": recipe['name'],
                "removed_count": removed_count,
                "staples_kept": len(staples_kept)
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to update pantry after cooking",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False


def save_recipe_feedback(
    recipe: dict,
    rating: int,
    make_again: str,
    notes: str
) -> bool:
    """Save recipe feedback to meal history and recipe files.

    Args:
        recipe: Recipe dictionary with name, ingredients, etc.
        rating: Star rating (1-5)
        make_again: "Yes", "No", or "Maybe"
        notes: User notes

    Returns:
        True if successful, False otherwise
    """
    try:
        # 1. Add to meal history
        history_path = get_data_file_path("meal_history")
        history_content = history_path.read_text(encoding="utf-8")

        # Build meal entry
        today = datetime.now()
        date_str = today.strftime("%A, %Y-%m-%d")
        stars = "⭐" * rating

        new_entry = f"\n### {date_str}\n"
        new_entry += f"**{recipe['name']}** {stars}\n"
        new_entry += f"- Rating: {rating}/5\n"

        if notes:
            new_entry += f"- Notes: {notes}\n"

        # Add ingredients
        ingredients_list = []
        if recipe.get('ingredients_available'):
            ingredients_list.append(recipe['ingredients_available'])
        if recipe.get('ingredients_needed'):
            ingredients_list.append(recipe['ingredients_needed'])

        if ingredients_list:
            all_ingredients = ', '.join(ingredients_list)
            new_entry += f"- Ingredients used: {all_ingredients}\n"

        new_entry += "\n"

        # Find where to insert (after most recent month header or at end)
        lines = history_content.split('\n')

        # Find first month header (## November 2025)
        insert_index = -1
        for i, line in enumerate(lines):
            if line.startswith('## '):
                # Insert after this line
                insert_index = i + 1
                break

        if insert_index == -1:
            # No month header found, create one
            month_year = today.strftime("%B %Y")
            new_entry = f"\n## {month_year}\n" + new_entry
            lines.append(new_entry)
        else:
            # Insert after month header
            lines.insert(insert_index, new_entry)

        # Write back
        history_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info(
            "Saved meal to history",
            extra={"recipe_name": recipe['name'], "rating": rating}
        )

        # 2. Save to appropriate recipe file based on rating
        if rating >= 5:
            recipe_file = "loved_recipes"
        elif rating >= 3:
            recipe_file = "liked_recipes"
        else:
            recipe_file = "not_again_recipes"

        recipe_path = get_data_file_path(recipe_file)
        recipe_content = recipe_path.read_text(encoding="utf-8")

        # Build recipe entry
        recipe_entry = f"\n---\n\n"
        recipe_entry += f"## {recipe['name']}\n"
        recipe_entry += f"**Last made:** {today.strftime('%Y-%m-%d')}\n"
        recipe_entry += f"**Rating:** {rating}/5 {stars}\n"

        if recipe.get('time_minutes'):
            recipe_entry += f"**Time:** {recipe['time_minutes']} minutes\n"

        if recipe.get('difficulty'):
            recipe_entry += f"**Difficulty:** {(recipe['difficulty'] or 'unknown').title()}\n"

        recipe_entry += "\n**Ingredients:**\n"

        # Combine all ingredients
        if recipe.get('ingredients_available'):
            for item in recipe['ingredients_available'].split(','):
                recipe_entry += f"- {item.strip()}\n"

        if recipe.get('ingredients_needed'):
            for item in recipe['ingredients_needed'].split(','):
                recipe_entry += f"- {item.strip()}\n"

        if notes:
            recipe_entry += f"\n**Notes:** {notes}\n"

        if make_again:
            recipe_entry += f"\n**Make again:** {make_again}\n"

        recipe_entry += "\n"

        # Append to recipe file
        recipe_path.write_text(recipe_content + recipe_entry, encoding="utf-8")

        logger.info(
            "Saved recipe to file",
            extra={"recipe_name": recipe['name'], "file": recipe_file}
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to save recipe feedback",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False


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

# Title
st.title("👨‍🍳 Cooking Mode")

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

# Initialize chat history in session state
if 'cooking_chat_history' not in st.session_state:
    st.session_state['cooking_chat_history'] = []

# Display recipe details
st.markdown("---")
st.markdown(f"## 🍽️ {recipe['name']}")

# Recipe metadata
col1, col2 = st.columns(2)
with col1:
    st.metric("⏱️ Time", f"{recipe.get('time_minutes', '?')} min")
with col2:
    st.metric("📊 Difficulty", (recipe.get('difficulty') or 'medium').title())

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
    logger.info("Cooking chat history cleared")
    st.rerun()

# Handle user question
if submit and user_input:
    # Add user message to history
    st.session_state['cooking_chat_history'].append({
        'role': 'user',
        'content': user_input
    })

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
