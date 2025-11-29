"""Recipe Generation Page for AI Recipe Planner.

Streamlit page for generating recipe suggestions using Claude API.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime

from lib.auth import require_authentication
from lib.exceptions import DataFileNotFoundError, LLMAPIError, RecipeParsingError
from lib.llm_agents import ClaudeProvider, RecipeGenerator
from lib.logging_config import get_logger, setup_logging
from lib.file_manager import get_data_file_path
from lib.weekly_plan_manager import add_recipe_to_plan

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def add_ingredients_to_shopping_list(recipe_name: str, ingredients: str) -> bool:
    """Add ingredients to shopping list file.

    Args:
        recipe_name: Name of the recipe
        ingredients: Comma-separated list of ingredients needed

    Returns:
        True if successful, False otherwise
    """
    try:
        shopping_path = get_data_file_path("shopping_list")
        content = shopping_path.read_text(encoding="utf-8")

        # Build entry for this recipe
        today = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n## For: {recipe_name} (Added: {today})\n"

        # Add each ingredient as a bullet point
        for item in ingredients.split(','):
            item = item.strip()
            if item:
                entry += f"- {item}\n"

        entry += "\n"

        # Append to shopping list file
        shopping_path.write_text(content + entry, encoding="utf-8")

        logger.info(
            "Added ingredients to shopping list",
            extra={
                "recipe_name": recipe_name,
                "ingredient_count": len([i for i in ingredients.split(',') if i.strip()])
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to add to shopping list",
            extra={"recipe_name": recipe_name, "error": str(e)},
            exc_info=True
        )
        return False


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

# Main content
st.markdown("### What sounds good tonight?")

# Cuisine selection
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Select cuisines:**")
    cuisine_soup = st.checkbox("🍲 Soup")
    cuisine_italian = st.checkbox("🇮🇹 Italian", value=True)
    cuisine_thai = st.checkbox("🇹🇭 Thai", value=True)
    cuisine_korean = st.checkbox("🇰🇷 Korean")
    cuisine_mexican = st.checkbox("🌮 Mexican")
    cuisine_mediterranean = st.checkbox("🫒 Mediterranean")

with col2:
    st.markdown("&nbsp;")  # Spacing
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
                # Initialize Claude provider and recipe generator
                provider = ClaudeProvider()
                generator = RecipeGenerator(provider)

                # Generate recipes
                recipes = generator.suggest_recipes(
                    cuisines=selected_cuisines,
                    meal_type=meal_type,
                    num_suggestions=num_recipes,
                    additional_context=additional_prefs if additional_prefs else None,
                )

                # Store in session state
                st.session_state["generated_recipes"] = recipes
                st.session_state["generation_params"] = {
                    "cuisines": selected_cuisines,
                    "meal_type": meal_type,
                }

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
            st.markdown("---")
            with st.expander("💬 Chat to modify this recipe"):
                st.markdown("*Ask to make changes like 'make it spicier', 'use different vegetables', 'make it faster', etc.*")

                # Initialize chat history for this recipe if not exists
                chat_key = f"recipe_chat_{idx}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []

                # Display chat history
                if st.session_state[chat_key]:
                    st.markdown("**Conversation:**")
                    for msg in st.session_state[chat_key]:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "user":
                            st.markdown(f"**You:** {content}")
                        else:
                            st.markdown(f"**Assistant:** {content}")
                    st.markdown("---")

                # Chat input
                chat_input = st.text_input(
                    "Your message",
                    key=f"chat_input_{idx}",
                    placeholder="e.g., 'make this spicier' or 'what if I don't have bell peppers?'",
                    label_visibility="collapsed"
                )

                if st.button("Send", key=f"send_chat_{idx}", type="primary"):
                    if chat_input and chat_input.strip():
                        with st.spinner("🤖 Refining recipe..."):
                            try:
                                # Initialize provider and generator
                                provider = ClaudeProvider()
                                generator = RecipeGenerator(provider)

                                # Add user message to chat history
                                st.session_state[chat_key].append({
                                    "role": "user",
                                    "content": chat_input
                                })

                                # Call refine_recipe
                                updated_recipe = generator.refine_recipe(
                                    recipe=recipe,
                                    user_message=chat_input,
                                    chat_history=st.session_state[chat_key][:-1]  # Exclude the message we just added
                                )

                                # Add assistant response to chat history
                                st.session_state[chat_key].append({
                                    "role": "assistant",
                                    "content": f"Updated the recipe as requested. Changes: {updated_recipe.get('reason', 'Recipe modified')}"
                                })

                                # Update the recipe in the generated_recipes list
                                st.session_state["generated_recipes"][idx - 1] = updated_recipe

                                logger.info(
                                    "Recipe refined via chat",
                                    extra={
                                        "recipe_name": recipe["name"],
                                        "user_message": chat_input
                                    }
                                )

                                st.success("✅ Recipe updated!")
                                st.rerun()

                            except LLMAPIError as e:
                                st.error(f"❌ API Error: {str(e)}")
                                logger.error("LLM API error during recipe refinement", exc_info=True)
                            except RecipeParsingError as e:
                                st.error(f"❌ Parsing Error: {str(e)}")
                                logger.error("Recipe parsing error during refinement", exc_info=True)
                            except Exception as e:
                                st.error(f"❌ Unexpected Error: {str(e)}")
                                logger.error("Unexpected error during recipe refinement", exc_info=True)
                    else:
                        st.warning("Please enter a message!")

            # Action buttons
            st.markdown("---")
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

            with btn_col1:
                if st.button("👨‍🍳 Cook This", key=f"cook_{idx}"):
                    # Store selected recipe in session state for cooking mode
                    st.session_state['active_recipe'] = recipe
                    st.session_state['active_recipe_idx'] = idx
                    # Clear any existing chat history for new recipe
                    st.session_state['cooking_chat_history'] = []
                    logger.info(
                        "User selected recipe to cook",
                        extra={"recipe_name": recipe["name"]},
                    )
                    # Navigate to cooking mode
                    st.switch_page("pages/cooking_mode.py")

            with btn_col2:
                if st.button("📅 Add to Plan", key=f"plan_{idx}"):
                    # Prepare recipe for weekly planner
                    plan_recipe = {
                        'name': recipe['name'],
                        'source': 'Generated',
                        'time_minutes': recipe.get('time_minutes'),
                        'difficulty': recipe.get('difficulty'),
                        'ingredients_needed': recipe.get('ingredients_needed', ''),
                    }

                    if add_recipe_to_plan(plan_recipe):
                        st.success(f"✅ Added to weekly plan!")
                        logger.info(
                            "Added generated recipe to weekly plan",
                            extra={"recipe_name": recipe["name"]},
                        )
                    # Note: add_recipe_to_plan shows its own warnings/errors

            with btn_col3:
                if st.button("❌ Not Interested", key=f"pass_{idx}"):
                    st.info("Noted! We'll suggest different recipes next time.")
                    # TODO: Implement preference learning
                    logger.info(
                        "User passed on recipe",
                        extra={"recipe_name": recipe["name"]},
                    )

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

    # Generate more button
    st.markdown("---")
    if st.button("🔄 Generate New Suggestions", use_container_width=True):
        # Clear current suggestions
        if "generated_recipes" in st.session_state:
            del st.session_state["generated_recipes"]
        if "generation_params" in st.session_state:
            del st.session_state["generation_params"]
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666;">'
    "💡 <b>Tip:</b> All recipes are vegetarian and tailored to your preferences!"
    "</div>",
    unsafe_allow_html=True,
)
