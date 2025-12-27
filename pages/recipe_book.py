"""Recipe Book Page - Curated recipe collection browser.

Displays recipes saved to the recipe book with collection-based browsing
by cuisine, rating, and special filters.
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from lib.active_recipe_manager import save_active_recipe
from lib.auth import require_authentication
from lib.logging_config import get_logger, setup_logging
from lib.mobile_ui import add_mobile_styles
from lib.recipe_book_helpers import (
    calculate_avg_rating,
    filter_recipes,
    get_recipe_collections,
    get_unique_cuisines,
    sort_recipes,
)
from lib.recipe_book_manager import (
    load_recipe_book,
    remove_from_recipe_book,
    update_recipe_book_recipe,
)
from lib.shopping_list_manager import add_items_to_list
from lib.weekly_plan_manager import add_recipe_to_plan

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Recipe Book - AI Recipe Planner",
    page_icon="📚",
    layout="wide",
)

# Authentication
require_authentication()
add_mobile_styles()

st.title("📚 Recipe Book")
st.markdown("*Your curated recipe collection*")


# Load recipes
try:
    all_recipes = load_recipe_book()

    if not all_recipes:
        st.info("📭 Your Recipe Book is empty!")
        st.markdown("""
        **Save recipes to your Recipe Book from:**
        - 🎲 Recipe Generator - Find recipes you love
        - 📸 Capture Recipe - Save recipes from photos
        - 👨‍🍳 Cooking Mode - After cooking, save your favorites (4-5 stars)
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Generate Recipes", use_container_width=True, type="primary"):
                st.switch_page("pages/generate_recipes.py")
        with col2:
            if st.button("📸 Capture Recipe", use_container_width=True):
                st.switch_page("pages/capture_recipe.py")

        logger.info("Recipe book is empty")

    else:
        # Initialize session state for filters
        if 'rb_selected_cuisine' not in st.session_state:
            st.session_state.rb_selected_cuisine = "All"
        if 'rb_selected_rating' not in st.session_state:
            st.session_state.rb_selected_rating = "All"
        if 'rb_selected_special' not in st.session_state:
            st.session_state.rb_selected_special = None
        if 'rb_search_query' not in st.session_state:
            st.session_state.rb_search_query = ""

        # Create collections
        collections = get_recipe_collections(all_recipes)
        unique_cuisines = get_unique_cuisines(all_recipes)

        # Sidebar filters
        with st.sidebar:
            st.markdown("## 📂 Collections")

            # Search box
            search_query = st.text_input(
                "🔍 Search recipes",
                value=st.session_state.rb_search_query,
                placeholder="Search by name, description, or tags...",
                key="search_input"
            )
            st.session_state.rb_search_query = search_query

            st.markdown("---")

            # By Cuisine
            with st.expander("🌍 By Cuisine", expanded=True):
                cuisine_options = ["All"] + unique_cuisines
                selected_cuisine = st.radio(
                    "Select cuisine",
                    cuisine_options,
                    index=cuisine_options.index(st.session_state.rb_selected_cuisine) if st.session_state.rb_selected_cuisine in cuisine_options else 0,
                    label_visibility="collapsed",
                    key="cuisine_radio"
                )
                st.session_state.rb_selected_cuisine = selected_cuisine

            # By Rating
            with st.expander("⭐ By Rating", expanded=False):
                rating_options = ["All", "5 Stars", "4+ Stars", "3+ Stars"]
                selected_rating = st.radio(
                    "Minimum rating",
                    rating_options,
                    index=rating_options.index(st.session_state.rb_selected_rating) if st.session_state.rb_selected_rating in rating_options else 0,
                    label_visibility="collapsed",
                    key="rating_radio"
                )
                st.session_state.rb_selected_rating = selected_rating

            # Special Collections
            with st.expander("✨ Special", expanded=False):
                special_options = {
                    f"Recent Additions ({len(collections['special']['recent'])})": 'recent',
                    f"Most Cooked ({len(collections['special']['popular'])})": 'popular',
                    f"Never Cooked ({len(collections['special']['never_cooked'])})": 'never_cooked',
                    f"Quick < 30 min ({len(collections['special']['quick'])})": 'quick'
                }

                for label, key in special_options.items():
                    if st.button(label, key=f"special_{key}", use_container_width=True):
                        st.session_state.rb_selected_special = key
                        st.session_state.rb_selected_cuisine = "All"
                        st.session_state.rb_selected_rating = "All"
                        st.rerun()

                if st.session_state.rb_selected_special:
                    if st.button("Clear Special Filter", use_container_width=True):
                        st.session_state.rb_selected_special = None
                        st.rerun()

        # Main content area
        # Apply filters
        filtered_recipes = all_recipes

        # Special filter takes precedence
        if st.session_state.rb_selected_special:
            filtered_recipes = collections['special'][st.session_state.rb_selected_special]
            collection_name = {
                'recent': 'Recent Additions',
                'popular': 'Most Cooked',
                'never_cooked': 'Never Cooked',
                'quick': 'Quick Meals (< 30 min)'
            }.get(st.session_state.rb_selected_special, 'Special')
        else:
            # Apply cuisine filter
            if selected_cuisine and selected_cuisine != "All":
                filtered_recipes = filter_recipes(
                    filtered_recipes,
                    cuisine=selected_cuisine
                )
                collection_name = f"{selected_cuisine} Recipes"
            else:
                collection_name = "All Recipes"

            # Apply rating filter
            if selected_rating != "All":
                rating_map = {"5 Stars": 5, "4+ Stars": 4, "3+ Stars": 3}
                min_rating = rating_map[selected_rating]
                filtered_recipes = filter_recipes(
                    filtered_recipes,
                    min_rating=min_rating
                )

        # Apply search query
        if search_query:
            filtered_recipes = filter_recipes(
                filtered_recipes,
                search_query=search_query
            )

        # Stats
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📖 Total Recipes", len(all_recipes))

        with col2:
            st.metric("👁️ Showing", len(filtered_recipes))

        with col3:
            avg_rating = calculate_avg_rating(filtered_recipes)
            st.metric("⭐ Avg Rating", f"{avg_rating:.1f}" if avg_rating > 0 else "N/A")

        st.markdown("---")

        # Sort options
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {collection_name}")
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Recently Added", "Name (A-Z)", "Rating (High-Low)", "Cook Count"],
                label_visibility="collapsed"
            )

        sorted_recipes = sort_recipes(filtered_recipes, sort_by)

        if not sorted_recipes:
            st.info("🔍 No recipes found matching your filters")
            st.markdown("**Try:**")
            st.markdown("- Clearing your search")
            st.markdown("- Selecting a different collection")
            st.markdown("- Browsing 'All Recipes'")

            if st.button("🔄 Clear All Filters", use_container_width=True):
                st.session_state.rb_selected_cuisine = "All"
                st.session_state.rb_selected_rating = "All"
                st.session_state.rb_selected_special = None
                st.session_state.rb_search_query = ""
                st.rerun()

        # Display recipes
        for idx, recipe in enumerate(sorted_recipes):
            stars = "⭐" * recipe.get('rating', 0)

            with st.expander(
                f"**{recipe['name']}** {stars}",
                expanded=False
            ):
                # Metadata row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    time_val = recipe.get('time_minutes', '?')
                    st.markdown(f"⏱️ **{time_val} min**")
                with col2:
                    difficulty = recipe.get('difficulty', 'medium')
                    st.markdown(f"📊 **{difficulty.title()}**")
                with col3:
                    cook_count = recipe.get('cook_count', 0)
                    st.markdown(f"🍳 **Cooked {cook_count}x**")
                with col4:
                    added_date = recipe.get('added_to_book', '')
                    if added_date:
                        try:
                            from datetime import datetime
                            added_dt = datetime.fromisoformat(added_date)
                            st.markdown(f"📅 **{added_dt.strftime('%b %d, %Y')}**")
                        except:
                            pass

                # Description
                if recipe.get('description'):
                    st.markdown(f"**Description:** {recipe['description']}")

                # Cuisine and tags
                info_parts = []
                if recipe.get('cuisine'):
                    info_parts.append(f"🌍 {recipe['cuisine']}")
                if recipe.get('tags'):
                    info_parts.append(f"🏷️ {', '.join(recipe['tags'])}")
                if info_parts:
                    st.markdown(" • ".join(info_parts))

                # Ingredients
                if recipe.get('ingredients'):
                    with st.expander("📋 Ingredients", expanded=False):
                        from lib.ingredient_schema import validate_ingredients_list, to_string_list

                        ingredients = recipe['ingredients']

                        # Handle both canonical and legacy formats
                        if validate_ingredients_list(ingredients):
                            # Canonical format - convert to string list for display
                            ing_strings = to_string_list(ingredients)
                            for ing in ing_strings:
                                st.markdown(f"- {ing}")
                        else:
                            # Legacy format - display as-is
                            for ing in ingredients:
                                if isinstance(ing, str):
                                    st.markdown(f"- {ing}")
                                elif isinstance(ing, dict):
                                    st.markdown(f"- {ing.get('item', str(ing))}")

                # Instructions
                if recipe.get('instructions'):
                    with st.expander("👨‍🍳 Instructions", expanded=False):
                        st.markdown(recipe['instructions'])

                # Notes
                if recipe.get('notes'):
                    st.info(f"📝 **Notes:** {recipe['notes']}")

                # Action buttons
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button(
                        "👨‍🍳 Cook",
                        key=f"cook_{recipe['id']}_{idx}",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.session_state['active_recipe'] = recipe
                        save_active_recipe(recipe)
                        logger.info(
                            "Started cooking from recipe book",
                            extra={"recipe_name": recipe['name']}
                        )
                        st.switch_page("pages/cooking_mode.py")

                with col2:
                    if st.button(
                        "📅 Plan",
                        key=f"plan_{recipe['id']}_{idx}",
                        use_container_width=True
                    ):
                        if add_recipe_to_plan(recipe):
                            st.success("✅ Added to weekly plan!")
                            logger.info(
                                "Added recipe to plan from book",
                                extra={"recipe_name": recipe['name']}
                            )

                with col3:
                    if st.button(
                        "🛒 Shop",
                        key=f"shop_{recipe['id']}_{idx}",
                        use_container_width=True
                    ):
                        ingredients = recipe.get('ingredients', [])
                        if not ingredients:
                            st.warning("⚠️ No ingredients to add!")
                        else:
                            # Convert canonical format to string list for shopping list
                            from lib.ingredient_schema import validate_ingredients_list, to_string_list

                            if validate_ingredients_list(ingredients):
                                ing_strings = to_string_list(ingredients)
                            else:
                                # Legacy format - already strings or convert dicts
                                ing_strings = []
                                for ing in ingredients:
                                    if isinstance(ing, str):
                                        ing_strings.append(ing)
                                    elif isinstance(ing, dict):
                                        ing_strings.append(ing.get('item', str(ing)))

                            if add_items_to_list(recipe['name'], ing_strings):
                                st.success("✅ Added to shopping list!")
                                logger.info(
                                    "Added recipe ingredients to shopping list",
                                    extra={"recipe_name": recipe['name']}
                                )
                            else:
                                st.error("❌ Failed to add to shopping list. Check logs.")
                                logger.error(
                                    "Failed to add to shopping list",
                                    extra={"recipe_name": recipe['name']}
                                )

                with col4:
                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{recipe['id']}_{idx}",
                        use_container_width=True
                    ):
                        st.session_state['editing_recipe'] = recipe
                        st.rerun()

                with col5:
                    if st.button(
                        "🗑️ Remove",
                        key=f"remove_{recipe['id']}_{idx}",
                        use_container_width=True
                    ):
                        st.session_state['removing_recipe'] = recipe
                        st.rerun()

        # Edit recipe modal
        if 'editing_recipe' in st.session_state:
            recipe = st.session_state['editing_recipe']

            st.markdown("---")
            st.markdown(f"## ✏️ Editing: {recipe['name']}")

            with st.form("edit_recipe_form"):
                # Editable fields
                name = st.text_input("Recipe Name", value=recipe.get('name', ''))
                description = st.text_area("Description", value=recipe.get('description', ''))

                col1, col2, col3 = st.columns(3)
                with col1:
                    time_minutes = st.number_input(
                        "Time (minutes)",
                        value=int(recipe.get('time_minutes', 30)),
                        min_value=1
                    )
                with col2:
                    difficulty_options = ["easy", "medium", "hard"]
                    difficulty = st.selectbox(
                        "Difficulty",
                        difficulty_options,
                        index=difficulty_options.index(recipe.get('difficulty', 'medium'))
                    )
                with col3:
                    cuisine = st.text_input("Cuisine", value=recipe.get('cuisine') or '')

                rating = st.select_slider(
                    "Rating",
                    options=[0, 1, 2, 3, 4, 5],
                    value=recipe.get('rating', 0)
                )

                # Tags
                tags_str = st.text_input(
                    "Tags (comma-separated)",
                    value=', '.join(recipe.get('tags', []))
                )

                # Ingredients
                ingredients_str = st.text_area(
                    "Ingredients (one per line)",
                    value='\n'.join(recipe.get('ingredients', [])),
                    height=150
                )

                # Instructions
                instructions = st.text_area(
                    "Instructions",
                    value=recipe.get('instructions', ''),
                    height=200
                )

                # Notes
                notes = st.text_area("Notes", value=recipe.get('notes', ''))

                # Submit buttons
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button(
                        "💾 Save Changes",
                        type="primary",
                        use_container_width=True
                    )
                with col2:
                    cancel_btn = st.form_submit_button(
                        "❌ Cancel",
                        use_container_width=True
                    )

                if save_btn:
                    # Build updated recipe
                    updated_recipe = {
                        **recipe,
                        'name': name,
                        'description': description,
                        'time_minutes': time_minutes,
                        'difficulty': difficulty,
                        'cuisine': cuisine if cuisine else None,
                        'rating': rating,
                        'tags': [tag.strip() for tag in tags_str.split(',') if tag.strip()],
                        'ingredients': [ing.strip() for ing in ingredients_str.split('\n') if ing.strip()],
                        'instructions': instructions,
                        'notes': notes
                    }

                    if update_recipe_book_recipe(updated_recipe):
                        st.success("✅ Recipe updated successfully!")
                        logger.info(
                            "Recipe updated in book",
                            extra={"recipe_name": name}
                        )
                        del st.session_state['editing_recipe']
                        st.rerun()
                    else:
                        st.error("❌ Failed to save recipe")

                if cancel_btn:
                    del st.session_state['editing_recipe']
                    st.rerun()

        # Remove confirmation modal
        if 'removing_recipe' in st.session_state:
            recipe = st.session_state['removing_recipe']

            st.markdown("---")
            st.warning(f"### ⚠️ Remove '{recipe['name']}' from Recipe Book?")
            st.markdown(
                "This will remove the recipe from your curated collection. "
                "It won't delete the recipe entirely - you can always add it back later."
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Remove", use_container_width=True, type="primary"):
                    if remove_from_recipe_book(recipe['id']):
                        st.success(f"✅ Removed '{recipe['name']}' from Recipe Book")
                        logger.info(
                            "Recipe removed from book",
                            extra={"recipe_name": recipe['name']}
                        )
                        del st.session_state['removing_recipe']
                        st.rerun()
                    else:
                        st.error("❌ Failed to remove recipe")

            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state['removing_recipe']
                    st.rerun()

        logger.info(
            "Recipe book displayed",
            extra={
                "total_recipes": len(all_recipes),
                "filtered": len(filtered_recipes)
            }
        )

except Exception as e:
    st.error(f"❌ Error loading recipe book: {str(e)}")
    logger.error("Error loading recipe book", exc_info=True)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
