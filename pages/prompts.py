"""Prompts Management Page - Edit LLM prompts used throughout the app."""

import streamlit as st

from lib.auth import require_authentication
from lib.prompt_manager import (
    get_prompt_variables,
    load_prompts,
    reset_to_defaults,
    save_prompts,
)
from lib.ui import render_header

# Require authentication
require_authentication()

# Header
render_header(
    title="🎯 Prompt Management",
    subtitle="Customize the AI prompts used throughout the application"
)

st.markdown("""
Edit the prompts below to customize how the AI generates recipes, categorizes ingredients, and more.
Variables in `{curly_braces}` will be replaced with actual values when the prompt is used.
""")

# Load current prompts
prompts = load_prompts()

# Tabs for different prompt types
tab1, tab2, tab3, tab4 = st.tabs([
    "🍳 Recipe Generation",
    "✏️ Recipe Refinement", 
    "💬 Recipe Chat",
    "🏷️ Ingredient Categorization"
])

# Track if any changes were made
changes_made = False

with tab1:
    st.subheader("Recipe Generation Prompt")
    st.markdown("Used when generating new recipe suggestions based on your pantry and preferences.")
    
    variables = get_prompt_variables("recipe_generation")
    with st.expander("📋 Available Variables"):
        st.code(", ".join(sorted(variables)), language="text")
    
    new_prompt = st.text_area(
        "Prompt Template",
        value=prompts.get("recipe_generation", ""),
        height=400,
        key="recipe_generation",
        help="Use {variable_name} for dynamic values"
    )
    
    if new_prompt != prompts.get("recipe_generation"):
        changes_made = True
        prompts["recipe_generation"] = new_prompt

with tab2:
    st.subheader("Recipe Refinement Prompt")
    st.markdown("Used when modifying an existing recipe based on user feedback.")
    
    variables = get_prompt_variables("recipe_refinement")
    with st.expander("📋 Available Variables"):
        st.code(", ".join(sorted(variables)), language="text")
    
    new_prompt = st.text_area(
        "Prompt Template",
        value=prompts.get("recipe_refinement", ""),
        height=400,
        key="recipe_refinement",
        help="Use {variable_name} for dynamic values"
    )
    
    if new_prompt != prompts.get("recipe_refinement"):
        changes_made = True
        prompts["recipe_refinement"] = new_prompt

with tab3:
    st.subheader("Recipe Chat Prompt")
    st.markdown("Used for conversational interactions about recipe modifications.")
    
    variables = get_prompt_variables("recipe_chat")
    with st.expander("📋 Available Variables"):
        st.code(", ".join(sorted(variables)), language="text")
    
    new_prompt = st.text_area(
        "Prompt Template",
        value=prompts.get("recipe_chat", ""),
        height=300,
        key="recipe_chat",
        help="Use {variable_name} for dynamic values"
    )
    
    if new_prompt != prompts.get("recipe_chat"):
        changes_made = True
        prompts["recipe_chat"] = new_prompt

with tab4:
    st.subheader("Ingredient Categorization Prompt")
    st.markdown("Used to categorize ingredients into shopping list categories.")
    
    variables = get_prompt_variables("ingredient_categorization")
    with st.expander("📋 Available Variables"):
        st.code(", ".join(sorted(variables)), language="text")
    
    new_prompt = st.text_area(
        "Prompt Template",
        value=prompts.get("ingredient_categorization", ""),
        height=300,
        key="ingredient_categorization",
        help="Use {variable_name} for dynamic values"
    )
    
    if new_prompt != prompts.get("ingredient_categorization"):
        changes_made = True
        prompts["ingredient_categorization"] = new_prompt

# Action buttons
st.divider()
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Save Changes", type="primary", disabled=not changes_made):
        if save_prompts(prompts):
            st.success("✅ Prompts saved successfully!")
            st.rerun()
        else:
            st.error("❌ Failed to save prompts")

with col2:
    if st.button("🔄 Reset to Defaults"):
        if reset_to_defaults():
            st.success("✅ Prompts reset to defaults!")
            st.rerun()
        else:
            st.error("❌ Failed to reset prompts")

with col3:
    if changes_made:
        st.warning("⚠️ You have unsaved changes")

# Help section
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    ### How to Edit Prompts
    
    1. **Variables**: Use `{variable_name}` syntax for dynamic values
    2. **Formatting**: Maintain clear structure and instructions for the AI
    3. **Testing**: After saving, test the changes by generating recipes or adding items
    4. **Reset**: Use "Reset to Defaults" if you want to start over
    
    ### Best Practices
    
    - Be specific and clear in your instructions
    - Include examples of the desired output format
    - Use consistent terminology throughout
    - Test changes incrementally
    
    ### Variable Examples
    
    - `{cuisines}`: List of selected cuisines
    - `{meal_type}`: Type of meal (Dinner, Lunch, etc.)
    - `{num_suggestions}`: Number of recipes to generate
    - `{ingredient_name}`: Name of ingredient to categorize
    """)
