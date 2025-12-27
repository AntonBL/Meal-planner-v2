"""Recipe Generation Page for AI Recipe Planner.

Streamlit page for generating recipe suggestions using Claude API.
"""

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime

import streamlit as st

from lib.active_recipe_manager import add_active_recipe
from lib.auth import require_authentication
from lib.chat_manager import clear_chat_history
from lib.constants import RECIPE_SOURCE_GENERATED
from lib.exceptions import DataFileNotFoundError, LLMAPIError, RecipeParsingError
from lib.file_manager import get_data_file_path
from lib.generated_recipes_manager import (
    clear_generated_recipes,
    load_generated_recipes,
    save_generated_recipes,
)
from lib.llm_agents import RecipeGenerator
from lib.llm_core import get_smart_model
from lib.logging_config import get_logger, setup_logging
from lib.recipe_book_manager import add_to_recipe_book, is_in_recipe_book
from lib.recipe_feedback import (
    save_recipe_feedback,
    update_pantry_after_cooking,
)
from lib.recipe_store import save_recipe
from lib.weekly_plan_manager import add_recipe_to_plan

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
# Note: Feedback and pantry functions now imported from lib/recipe_feedback.py


from lib.shopping_list_manager import add_items_to_list

def add_ingredients_to_shopping_list(recipe_name: str, ingredients: str) -> bool:
    """Add ingredients to shopping list.

    Args:
        recipe_name: Name of the recipe
        ingredients: Comma-separated list of ingredients needed

    Returns:
        True if successful, False otherwise
    """
    if not ingredients:
        return True
        
    ing_list = [i.strip() for i in ingredients.split(',') if i.strip()]
    return add_items_to_list(recipe_name, ing_list)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="Generate Recipes - AI Recipe Planner",
    page_icon="🎲",
    layout="wide",
)

# Authentication
require_authentication()

# Title
st.title("🎲 Recipe Generator")
st.markdown("*Let AI suggest delicious vegetarian recipes based on your pantry*")

# Load persisted generated recipes if not in session state
if "generated_recipes" not in st.session_state:
    # First check if generated recipes have expired
    from lib.generated_recipes_manager import are_generated_recipes_expired, get_generated_recipes_age

    if are_generated_recipes_expired():
        age = get_generated_recipes_age()
        logger.info(
            "Generated recipes expired, clearing them",
            extra={"age_days": age}
        )
        clear_generated_recipes()
        st.session_state["expired_recipes_cleared"] = True
    else:
        # Load valid recipes
        persisted_data = load_generated_recipes()
        if persisted_data:
            st.session_state["generated_recipes"] = persisted_data.get("recipes", [])
            st.session_state["generation_params"] = persisted_data.get("generation_params", {})
            logger.info(
                "Restored generated recipes from persistent storage",
                extra={"count": len(st.session_state["generated_recipes"])}
            )

# Sidebar with instructions
with st.sidebar:
    st.markdown("## How It Works")
    st.markdown(
        """
        1. **Select cuisines** you're in the mood for
        2. **Choose meal type** (dinner, lunch, or quick)
        3. **Click generate** and let AI suggest recipes
        4. **Review suggestions** with ingredients you have vs. need to buy
        """
    )
    st.markdown("---")
    st.markdown("**💡 Tip:** The AI considers your vegetarian preferences and recent meals for variety!")

# Show message if expired recipes were cleared
if st.session_state.get("expired_recipes_cleared", False):
    st.info("🧹 Your previous recipe suggestions expired (7+ days old) and were cleared. Generate new ones below!")
    # Clear the flag so message doesn't persist
    del st.session_state["expired_recipes_cleared"]

# Main content
st.markdown("### What sounds good tonight?")

# Cuisine selection
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Select cuisines:**")
    cuisine_soup = st.checkbox("🍲 Soup")
    cuisine_italian = st.checkbox("🇮🇹 Italian")
    cuisine_thai = st.checkbox("🇹🇭 Thai")
    cuisine_korean = st.checkbox("🇰🇷 Korean")
    cuisine_mexican = st.checkbox("🌮 Mexican")
    cuisine_mediterranean = st.checkbox("🫒 Mediterranean")
    cuisine_middle_eastern = st.checkbox("🧆 Middle Eastern")
    cuisine_indian = st.checkbox("🍛 Indian")
    cuisine_asian = st.checkbox("🥡 Asian (General)")
    cuisine_american = st.checkbox("🍔 American (Vegetarian)")
    cuisine_other = st.checkbox("🌍 Other")

# Build cuisine list
selected_cuisines = []
if cuisine_soup:
    selected_cuisines.append("Soup")
if cuisine_italian:
    selected_cuisines.append("Italian")
if cuisine_thai:
    selected_cuisines.append("Thai")
if cuisine_korean:
    selected_cuisines.append("Korean")
if cuisine_mexican:
    selected_cuisines.append("Mexican")
if cuisine_mediterranean:
    selected_cuisines.append("Mediterranean")
if cuisine_middle_eastern:
    selected_cuisines.append("Middle Eastern")
if cuisine_indian:
    selected_cuisines.append("Indian")
if cuisine_asian:
    selected_cuisines.append("Asian (General)")
if cuisine_american:
    selected_cuisines.append("American")
if cuisine_other:
    selected_cuisines.append("Other")

# Meal type selection
st.markdown("**Meal type:**")
meal_type = st.radio(
    "Meal type",
    ["Dinner", "Lunch", "Quick & Easy"],
    horizontal=True,
    label_visibility="collapsed",
)

# Number of suggestions
num_recipes = st.slider(
    "Number of suggestions",
    min_value=2,
    max_value=6,
    value=4,
    help="How many recipe suggestions do you want?",
)

# Additional preferences (free-form text)
additional_prefs = st.text_input(
    "Additional preferences (optional)",
    placeholder="e.g., 'make it spicy', 'low carb', 'under 30 minutes', 'one pot meal'",
    help="Add any specific requirements or preferences for your recipes",
)

# Generate button
st.markdown("---")

if st.button("✨ Generate Recipe Suggestions", type="primary", use_container_width=True):
    # Validate inputs
    if not selected_cuisines:
        st.error("⚠️ Please select at least one cuisine!")
        logger.warning("Recipe generation attempted with no cuisines selected")
    else:
        logger.info(
            "Recipe generation requested",
            extra={
                "cuisines": selected_cuisines,
                "meal_type": meal_type,
                "num_recipes": num_recipes,
            },
        )

        try:
            with st.spinner("🤖 AI is thinking... This may take 10-15 seconds"):
                # Initialize LLM provider and recipe generator
                provider = get_smart_model()
                generator = RecipeGenerator(provider)

                # Generate recipes
                recipes = generator.suggest_recipes(
                    cuisines=selected_cuisines,
                    meal_type=meal_type,
                    num_suggestions=num_recipes,
                    additional_context=additional_prefs if additional_prefs else None,
                )

                # Prepare recipe metadata (but don't save to main library yet)
                from lib.ingredient_schema import from_comma_separated

                for recipe in recipes:
                    recipe['source'] = RECIPE_SOURCE_GENERATED
                    recipe['rating'] = 0  # Not rated yet
                    recipe['cook_count'] = 0
                    recipe['tags'] = ['vegetarian']

                    # Convert ingredients to canonical format
                    # This preserves both the available/needed distinction AND provides a unified list
                    canonical_ingredients = from_comma_separated(
                        recipe.get('ingredients_available'),
                        recipe.get('ingredients_needed')
                    )
                    recipe['ingredients'] = canonical_ingredients

                    # Keep the original comma-separated strings for backward compatibility
                    # This allows both old and new code to work during migration

                logger.info(f"Generated {len(recipes)} recipes (not saved to library yet)")

                # Store in session state
                st.session_state["generated_recipes"] = recipes
                st.session_state["generation_params"] = {
                    "cuisines": selected_cuisines,
                    "meal_type": meal_type,
                }

                # Save to persistent storage
                save_generated_recipes(
                    recipes=recipes,
                    params=st.session_state["generation_params"]
                )

                st.success(f"✅ Generated {len(recipes)} recipe suggestions!")

        except LLMAPIError as e:
            st.error(
                "❌ **API Error**\n\n"
                "Could not connect to Claude API. Please check:\n"
                "- Your API key is set in the `.env` file\n"
                "- You have an internet connection\n\n"
                f"Error: {str(e)}"
            )
            logger.error("LLM API error during recipe generation", exc_info=True)

        except DataFileNotFoundError as e:
            st.error(
                "❌ **Data Error**\n\n"
                "Could not load pantry or preference data. Please check that "
                "all data files exist in the `data/` directory.\n\n"
                f"Error: {str(e)}"
            )
            logger.error("Data file not found during recipe generation", exc_info=True)

        except RecipeParsingError as e:
            st.error(
                "❌ **Parsing Error**\n\n"
                "Could not parse the AI's response. This is unusual. "
                "Please try again.\n\n"
                f"Error: {str(e)}"
            )
            logger.error("Recipe parsing error", exc_info=True)

        except Exception as e:
            st.error(
                "❌ **Unexpected Error**\n\n"
                "Something went wrong. Please try again or check the logs.\n\n"
                f"Error: {str(e)}"
            )
            logger.error("Unexpected error during recipe generation", exc_info=True)

# Display results if available
if "generated_recipes" in st.session_state:
    st.markdown("---")

    # Display feedback modal if triggered
    if st.session_state.get('show_feedback_modal', False):
        recipe = st.session_state.get('cooking_recipe', {})

        st.markdown(f"## 🎉 You cooked: {recipe.get('name', 'Unknown')}")
        st.markdown("**How was it? Please rate your experience:**")

        with st.form("recipe_feedback_form"):
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
                    st.session_state['feedback_saved_show_pantry_prompt'] = True
                    st.rerun()
                else:
                    st.error("❌ Failed to save feedback. Please try again.")

            if cancel:
                # Clear modal state
                st.session_state['show_feedback_modal'] = False
                if 'cooking_recipe' in st.session_state:
                    del st.session_state['cooking_recipe']
                if 'cooking_recipe_idx' in st.session_state:
                    del st.session_state['cooking_recipe_idx']
                st.rerun()

        # Show pantry update prompt after feedback is saved
        if st.session_state.get('feedback_saved_show_pantry_prompt', False):
            st.markdown("---")
            st.info("🥫 **Smart Pantry Update**\n\nWould you like to update your pantry by removing the ingredients you used?\n\nWe'll keep staples like oil and spices, but remove fresh items and consumables.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Yes, Update Pantry", key="update_pantry_yes", use_container_width=True):
                    # Call pantry update function
                    update_success = update_pantry_after_cooking(recipe)

                    if update_success:
                        st.success("✅ Pantry updated!")
                    else:
                        st.warning("⚠️ Could not update pantry automatically. You can do it manually.")

                    # Clear all modal state
                    st.session_state['show_feedback_modal'] = False
                    st.session_state['feedback_saved_show_pantry_prompt'] = False
                    if 'cooking_recipe' in st.session_state:
                        del st.session_state['cooking_recipe']
                    if 'cooking_recipe_idx' in st.session_state:
                        del st.session_state['cooking_recipe_idx']
                    st.rerun()

            with col2:
                if st.button("❌ No Thanks", key="update_pantry_no", use_container_width=True):
                    # Clear all modal state
                    st.session_state['show_feedback_modal'] = False
                    st.session_state['feedback_saved_show_pantry_prompt'] = False
                    if 'cooking_recipe' in st.session_state:
                        del st.session_state['cooking_recipe']
                    if 'cooking_recipe_idx' in st.session_state:
                        del st.session_state['cooking_recipe_idx']
                    st.rerun()

        st.markdown("---")

    st.markdown("## 🍽️ Recipe Suggestions")

    params = st.session_state.get("generation_params", {})
    st.caption(
        f"Suggestions for: {', '.join(params.get('cuisines', []))} • {params.get('meal_type', 'Dinner')}"
    )

    recipes = st.session_state["generated_recipes"]

    # Initialize chat state for all recipes BEFORE rendering to avoid first-click issues
    for idx in range(1, len(recipes) + 1):
        chat_key = f"recipe_chat_{idx}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Also initialize the clear flag to prevent first-click consumption
        clear_input_key = f"clear_chat_input_{idx}"
        if clear_input_key not in st.session_state:
            st.session_state[clear_input_key] = False

    for idx, recipe in enumerate(recipes, 1):
        with st.expander(
            f"**{idx}. {recipe['name']}** ({recipe.get('time_minutes', '?')} min • {(recipe.get('difficulty') or 'medium').title()})",
            expanded=(idx == 1),  # Expand first recipe by default
        ):
            # Description
            st.markdown(f"*{recipe.get('description', 'No description available')}*")

            # Ingredients section
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ Ingredients You Have:**")
                available = recipe.get("ingredients_available", "")
                if available:
                    for item in available.split(","):
                        st.markdown(f"- {item.strip()}")
                else:
                    st.markdown("*None listed*")

            with col2:
                st.markdown("**🛒 Ingredients to Buy:**")
                needed = recipe.get("ingredients_needed", "")
                if needed and needed.strip():
                    for item in needed.split(","):
                        st.markdown(f"- {item.strip()}")
                else:
                    st.success("**You have everything!**")

            # Cooking instructions
            if "instructions" in recipe and recipe["instructions"]:
                st.markdown("---")
                st.markdown("**📝 Cooking Instructions:**")
                st.markdown(recipe["instructions"])

            # Reason for suggestion
            if "reason" in recipe:
                st.info(f"**Why this recipe:** {recipe['reason']}")

            # Chat interface for recipe refinement
            chat_key = f"recipe_chat_{idx}"  # Already initialized above
            st.markdown("---")
            st.markdown("💬 **Chat to modify this recipe**")
            st.markdown("*Discuss changes you'd like to make, then click 'Update Recipe' to apply them.*")

            # Display chat history
            if st.session_state[chat_key]:
                for msg in st.session_state[chat_key]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        st.markdown(f"**You:** {content}")
                    else:
                        st.markdown(f"**Assistant:** {content}")
                st.markdown("---")

            # Check if we need to clear the input (must be before creating the widget)
            clear_input_key = f"clear_chat_input_{idx}"
            if clear_input_key in st.session_state and st.session_state[clear_input_key]:
                # Reset the input value before widget creation
                if f"chat_input_{idx}" in st.session_state:
                    st.session_state[f"chat_input_{idx}"] = ""
                st.session_state[clear_input_key] = False

            # Chat input and buttons
            col_input, col_send, col_update = st.columns([3, 1, 1])

            with col_input:
                chat_input = st.text_input(
                    "Your message",
                    key=f"chat_input_{idx}",
                    placeholder="e.g., 'make this spicier' or 'use mushrooms instead'",
                    label_visibility="collapsed"
                )

            with col_send:
                send_clicked = st.button("💬 Send", key=f"send_chat_{idx}")

            with col_update:
                update_clicked = st.button("✨ Update Recipe", key=f"update_recipe_{idx}", type="primary")

            # Handle Send button - conversational chat
            if send_clicked:
                if chat_input and chat_input.strip():
                    with st.spinner("💬 Chatting..."):
                        try:
                            # Initialize provider and generator
                            provider = get_smart_model()
                            generator = RecipeGenerator(provider)

                            # Add user message to chat history
                            st.session_state[chat_key].append({
                                "role": "user",
                                "content": chat_input
                            })

                            # Get conversational response (not regenerating recipe yet)
                            assistant_response = generator.chat_about_recipe(
                                recipe=recipe,
                                user_message=chat_input,
                                chat_history=st.session_state[chat_key][:-1]  # Exclude the message we just added
                            )

                            # Add assistant response to chat history
                            st.session_state[chat_key].append({
                                "role": "assistant",
                                "content": assistant_response
                            })

                            logger.info(
                                "Chat message sent",
                                extra={
                                    "recipe_name": recipe["name"],
                                    "user_message": chat_input
                                }
                            )

                            # Set flag to clear input on next render
                            st.session_state[f"clear_chat_input_{idx}"] = True

                            st.rerun()

                        except LLMAPIError as e:
                            st.error(f"❌ API Error: {str(e)}")
                            logger.error("LLM API error during chat", exc_info=True)
                        except Exception as e:
                            st.error(f"❌ Unexpected Error: {str(e)}")
                            logger.error("Unexpected error during chat", exc_info=True)
                else:
                    st.warning("Please enter a message!")

            # Handle Update Recipe button - regenerate with all changes
            if update_clicked:
                if st.session_state[chat_key]:
                    with st.spinner("✨ Updating recipe with your changes..."):
                        try:
                            # Initialize provider and generator
                            provider = get_smart_model()
                            generator = RecipeGenerator(provider)

                            # Build a summary of all requested changes from chat
                            all_changes = "\n".join([
                                msg["content"] for msg in st.session_state[chat_key]
                                if msg["role"] == "user"
                            ])

                            # Call refine_recipe with full conversation context
                            updated_recipe = generator.refine_recipe(
                                recipe=recipe,
                                user_message=all_changes,
                                chat_history=st.session_state[chat_key]
                            )

                            # Update the recipe in the generated_recipes list
                            st.session_state["generated_recipes"][idx - 1] = updated_recipe

                            # Save updated recipes to persistent storage
                            save_generated_recipes(
                                recipes=st.session_state["generated_recipes"],
                                params=st.session_state.get("generation_params", {})
                            )

                            # Clear chat history after successful update
                            st.session_state[chat_key] = []

                            logger.info(
                                "Recipe updated from chat conversation",
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
                    st.info("💡 Start a conversation about changes you'd like, then click 'Update Recipe' to apply them!")

            # Action buttons
            st.markdown("---")

            # Check if recipe is already in library
            from lib.recipe_store import get_recipe_by_id
            in_library = get_recipe_by_id(recipe.get('id')) is not None

            btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)

            with btn_col1:
                if st.button("👨‍🍳 Cook This", key=f"cook_{idx}"):
                    # Auto-save to library if not already there
                    if not in_library:
                        save_recipe(recipe)
                        logger.info(f"Auto-saved recipe to library when cooking: {recipe.get('name')}")

                    # Add to multi-recipe cooking mode
                    if add_active_recipe(recipe):
                        logger.info(
                            "User added recipe to cooking mode",
                            extra={"recipe_name": recipe["name"]},
                        )
                        # Navigate to cooking mode
                        st.switch_page("pages/cooking_mode.py")
                    else:
                        st.error("❌ Failed to add recipe to cooking mode")

            with btn_col2:
                if st.button("📅 Add to Plan", key=f"plan_{idx}"):
                    # Auto-save to library if not already there
                    if not in_library:
                        save_recipe(recipe)
                        logger.info(f"Auto-saved recipe to library when adding to plan: {recipe.get('name')}")

                    # Prepare recipe for weekly planner with FULL details
                    plan_recipe = recipe.copy()  # Copy full recipe
                    plan_recipe['source'] = RECIPE_SOURCE_GENERATED  # Mark as generated

                    if add_recipe_to_plan(plan_recipe):
                        st.success("✅ Added to weekly plan!")
                        logger.info(
                            "Added generated recipe to weekly plan",
                            extra={"recipe_name": recipe["name"]},
                        )
                    # Note: add_recipe_to_plan shows its own warnings/errors

            with btn_col3:
                if in_library:
                    st.button("✅ In Library", key=f"library_{idx}", disabled=True)
                else:
                    if st.button("💾 Save to Library", key=f"save_{idx}", type="primary"):
                        if save_recipe(recipe):
                            st.success("✅ Saved to your recipe library!")
                            logger.info(
                                "User explicitly saved recipe to library",
                                extra={"recipe_name": recipe["name"]},
                            )
                            st.rerun()
                        else:
                            st.error("❌ Failed to save recipe. Check logs.")

            with btn_col4:
                if st.button("🛒 Shopping List", key=f"shop_{idx}"):
                    if needed and needed.strip():
                        # Add ingredients to shopping list
                        success = add_ingredients_to_shopping_list(
                            recipe_name=recipe['name'],
                            ingredients=needed
                        )

                        if success:
                            st.success("✅ Added ingredients to shopping list!")
                            logger.info(
                                "User added ingredients to shopping list",
                                extra={"recipe_name": recipe["name"]},
                            )
                        else:
                            st.error("❌ Failed to add to shopping list. Check logs.")
                    else:
                        st.info("No ingredients to add - you have everything!")

            with btn_col5:
                # Check if recipe is in Recipe Book
                recipe_id = recipe.get('id')
                if recipe_id and is_in_recipe_book(recipe_id):
                    st.button("✅ In Book", key=f"in_book_{idx}", disabled=True)
                else:
                    if st.button("📚 Recipe Book", key=f"save_book_{idx}"):
                        # Ensure recipe has an ID before adding
                        if not recipe_id:
                            import uuid
                            recipe['id'] = str(uuid.uuid4())

                        # Auto-save to library if not already there
                        if not in_library:
                            save_recipe(recipe)
                            logger.info(f"Auto-saved recipe to library when adding to book: {recipe.get('name')}")

                        if add_to_recipe_book(recipe):
                            st.success("✅ Saved to Recipe Book!")
                            logger.info(
                                "Added recipe to book",
                                extra={"recipe_name": recipe["name"]},
                            )
                            st.rerun()
                        else:
                            st.error("❌ Failed to save to Recipe Book")

    # Generate more button
    st.markdown("---")
    if st.button("🔄 Generate New Suggestions", use_container_width=True):
        # Clear current suggestions from both session state and persistent storage
        if "generated_recipes" in st.session_state:
            del st.session_state["generated_recipes"]
        if "generation_params" in st.session_state:
            del st.session_state["generation_params"]
        clear_generated_recipes()
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666;">'
    "💡 <b>Tip:</b> All recipes are vegetarian and tailored to your preferences! "
    "Generated suggestions expire after 7 days unless saved to your library."
    "</div>",
    unsafe_allow_html=True,
)
