# Changelog

All notable changes to the AI Recipe Planner will be documented in this file.

## [Unreleased]

### Added - 2025-11-29 (Latest)

#### Two-Stage Conversational Recipe Chat
- **Restructured Chat Workflow**: Split recipe modification into two separate actions
  - **💬 Send Button**: Discuss potential changes conversationally without modifying recipe
    - AI responds to questions and suggestions
    - Explore ideas freely ("Can I make this spicier?", "What if I use tofu instead?")
    - AI prompts user to click "Update Recipe" when ready to apply changes
  - **✨ Update Recipe Button**: Apply all discussed changes at once
    - Regenerates recipe based on full conversation history
    - Clears chat after successful update
  - **Benefits**: Safer UX - users can explore options before committing changes

- **New LLM Method**: `RecipeGenerator.chat_about_recipe()`
  - Conversational responses that acknowledge user requests
  - Discusses feasibility and suggests alternatives
  - Concise 2-3 sentence responses (max 300 tokens)
  - Reminds users to click "Update Recipe" button to apply changes

#### Active Recipe Persistence
- **New Module**: `lib/active_recipe_manager.py`
  - JSON-based persistent storage for currently cooking recipe
  - Three core functions: `save_active_recipe()`, `load_active_recipe()`, `clear_active_recipe()`
- **Session Survival**: Active recipes now persist across:
  - Page refreshes
  - Browser restarts
  - Server restarts
- **Cooking Mode Enhancement**:
  - Automatically checks persistent storage if session state is empty
  - Recipe restored seamlessly on page load
  - Cleared when cooking is marked complete
- **Integration Points**:
  - Recipe generator's "Cook This" button
  - Weekly planner's "Cook" button
  - Both save to persistent storage AND session state

#### Generated Recipe Storage
- **New Recipe File Type**: `data/recipes/generated.md`
  - Stores full recipe details for AI-generated recipes added to weekly plan
  - Preserves ingredients, instructions, time, difficulty, and description
  - Prevents data loss when generated recipes move from session state to plan
- **Automatic Saving**:
  - Triggered when generated recipe is added to weekly plan
  - Deduplicates ingredients from "available" and "needed" lists
  - Adds timestamp and "Why this recipe" rationale
- **Weekly Planner Integration**:
  - Loads generated recipes alongside loved and liked recipes
  - Added "Generated" option to source filter dropdown
  - Full recipe details available for cooking mode
- **New Function**: `weekly_plan_manager.save_generated_recipe()`
  - 92 lines of recipe formatting and storage logic
  - Intelligent ingredient list merging
  - Markdown formatting with sections

#### Session State Initialization Fix
- **Fixed Double-Click Bug**: Resolved issue where Send button required two clicks
- **Root Cause**: Chat state keys initialized mid-render, consuming first button click
- **Solution**: Pre-initialize ALL session state before rendering loop
  - Chat history keys (`recipe_chat_{idx}`)
  - Clear input flag keys (`clear_chat_input_{idx}`)
- **Flag-Based Input Clearing**: Prevents "cannot modify widget after instantiation" error
  - Set flag on one render cycle
  - Act on flag before widget creation on next render cycle

### Technical Details - Latest
- **Files Modified**:
  - `lib/active_recipe_manager.py` - NEW (140 lines)
  - `lib/llm_agents.py` - Added `chat_about_recipe()` method
  - `pages/generate_recipes.py` - Two-button chat UI, pre-initialization
  - `lib/file_manager.py` - Added "generated_recipes" file type
  - `lib/weekly_plan_manager.py` - Added `save_generated_recipe()`
  - `pages/cooking_mode.py` - Persistence integration, fallback loading
  - `pages/weekly_planner.py` - Generated recipe loading and filtering
  - `.gitignore` - Excluded `active_recipe.json` session data

- **Logging Fix**: Changed from reserved "message" field to "user_message" in logging extras

### Added - 2025-11-29 (Earlier)

#### Pantry UI Improvements
- **Enhanced Category Organization**: Pantry now displays items grouped by meaningful categories instead of just "Staples" and "Fresh"
  - 10 distinct category sections with custom icons:
    - 🌾 Grains & Pasta
    - 🫘 Beans & Legumes
    - 🫗 Oils & Condiments
    - 🥫 Canned Goods
    - 🌿 Spices & Herbs (Dried)
    - 🥚 Proteins (Vegetarian)
    - 🧈 Dairy & Alternatives
    - 🥬 Vegetables
    - 🌱 Fresh Herbs
    - 🍋 Fruits
  - Sections automatically populated from existing markdown structure in pantry files
  - Empty sections are hidden to reduce clutter

- **Improved Visual Cleanliness**:
  - All category sections now collapse by default (`expanded=False`)
  - Added "🗑️ Delete mode" toggle to hide/show delete buttons
  - Clean view by default - delete buttons only appear when needed
  - Reduces visual noise by ~20% when browsing pantry

- **Fixed Auto-Scroll Issue**: Reorganized page layout to prevent unwanted scrolling
  - Pantry inventory now displays at the top of the page
  - Photo upload and chat interfaces moved to collapsible expanders below
  - Page loads showing pantry contents instead of scrolling to chat input
  - Follows "content first, actions second" UX principle

#### Expanded Cuisine Options
- **Added New Cuisines**:
  - 🍲 **Soup** - Now available as a cuisine/meal type option (positioned at top)
  - 🇰🇷 **Korean** - Added Korean cuisine option
  - 🇹🇭 **Thai** - Added Thai cuisine option (defaults to checked)
- **Reorganized Cuisine Selection**:
  - Soup moved to top position for visibility
  - Thai set as default selection alongside Italian
  - "Asian" renamed to "Asian (General)" for clarity
  - Balanced layout: 6 cuisines in left column, 5 in right column

### Changed
- **Pantry Display Logic**:
  - New `parse_pantry_by_sections()` function replaces `parse_pantry_items()`
  - Section-based parsing respects markdown headers in data files
  - Dynamic icon mapping via `category_icons` dictionary
  - Unified display for both staples and fresh items in single view

- **Recipe Generation UI**:
  - Default cuisines updated: Italian and Thai (previously Italian and Asian)
  - Cuisine checkbox order reorganized for better UX

### Technical Details
- **Files Modified**:
  - `pages/pantry.py` - Complete UI reorganization and section-based parsing
  - `pages/generate_recipes.py` - Added cuisine options and reordered checkboxes

### Added - 2025-11-28

#### Conversational Recipe Generation
- **Free-Form Preference Input**: Added text input field for custom preferences during recipe generation
  - Users can specify requirements like "spicy", "quick", "low carb", "one pot meal", etc.
  - Preferences are incorporated into AI prompt for all generated recipes
  - Simple, unobtrusive single-line input field below meal type selector

- **Per-Recipe Chat Interface**: Added expandable chat section to each generated recipe
  - **Real-Time Refinement**: Modify recipes through natural conversation
  - **Conversation History**: Full chat history maintained per recipe in session state
  - **In-Place Updates**: Recipes update directly based on conversation (no duplicates)
  - **Smart Context**: AI maintains context of original recipe and conversation history
  - **Example Use Cases**:
    - Adjust spice levels ("make this spicier" / "make this milder")
    - Ingredient substitutions ("what if I don't have bell peppers?")
    - Time constraints ("can you make this in 20 minutes?")
    - Dietary modifications ("make this oil-free", "add more protein")
    - Ingredient swaps ("use mushrooms instead of tofu")

- **New LLM Agent Methods**:
  - `RecipeGenerator.refine_recipe()` - Handles chat-based recipe refinement
  - `_build_refinement_prompt()` - Constructs prompts with conversation context
  - `_parse_single_recipe()` - Parses refined recipe responses
  - Added `additional_context` parameter to `suggest_recipes()`

### Added - 2025-11-28 (Earlier)

#### Weekly Planner & Shopping List Integration
- **Automatic Shopping List Sync**: Adding meals to weekly planner now automatically adds needed ingredients to shopping list
- **Bidirectional Sync**: Removing meals from weekly planner automatically removes their ingredients from shopping list
- **Recipe Source Tracking**: Shopping list sections labeled with recipe names (e.g., "For: Garlic Butter Pasta")
- Created `lib/weekly_plan_manager.py` shared library for plan and shopping list management

#### Smart Pantry Updates After Cooking
- **Intelligent Ingredient Removal**: After cooking and rating, users can opt to update pantry
- **Staple Preservation**: System automatically keeps staples (oils, spices, sauces, shelf-stable items)
- **Consumable Removal**: Removes fresh items and consumables that were used
- **Usage Logging**: Adds comments to pantry files documenting what was cooked and what was removed
- **Staple Detection**: Keyword-based categorization for 50+ common staples including:
  - Oils & fats (olive oil, butter, ghee, etc.)
  - Sauces & condiments (soy sauce, vinegar, hot sauce, etc.)
  - Spices & herbs (salt, pepper, cumin, paprika, etc.)
  - Baking basics (flour, sugar, baking soda, etc.)
  - Dried grains & pasta (rice, pasta, quinoa, lentils, etc.)
  - Shelf-stable items (stock, broth, tomato paste, etc.)

#### UI/UX Improvements
- Renamed "Update Pantry" page to "Pantry" for cleaner navigation
- Added "📅 Add to Plan" button to generated recipes
- Updated pantry update prompt with clear messaging about staple preservation
- Enhanced user workflow: Plan → Shop → Cook → Rate → Update Pantry

### Changed
- Updated `generate_recipes.py` to include `ingredients_needed` when adding to plan
- Updated `weekly_planner.py` to convert ingredient lists to shopping list format
- Modified cooking mode and recipe generation feedback flows to include pantry update prompt
- Enhanced shopping list format to group ingredients by recipe

### Technical Details - Conversational Features
- **Architecture**:
  - Protocol-based design with dependency injection (LLMProvider protocol)
  - Session state management for per-recipe chat history
  - Unique keys per recipe (`recipe_chat_{idx}`) for parallel conversations
  - In-place recipe updates without creating duplicates

- **UI/UX**:
  - Expandable chat section (hidden by default, user opt-in)
  - Text input with placeholder examples
  - Visual chat history with user/assistant message distinction
  - Real-time recipe refresh on update

- **Error Handling**:
  - Comprehensive try/catch for LLMAPIError, RecipeParsingError
  - User-friendly error messages
  - Structured logging with context

- **Files Modified (Conversational)**:
  - `lib/llm_agents.py` - Added refine_recipe() and helper methods
  - `pages/generate_recipes.py` - Added chat UI and integration
  - `README.md` - Added conversational features documentation
  - `SPEC.md` - Updated Key Features and Sample User Flows
  - `CHANGELOG.md` - Documented new features

### Technical Details - Weekly Planner & Pantry Updates (Earlier)
- **New Functions**:
  - `add_ingredients_to_shopping_list()` - Adds recipe ingredients to shopping list
  - `remove_recipe_from_shopping_list()` - Removes recipe section from shopping list
  - `is_staple_ingredient()` - Categorizes ingredients as staples vs consumables
  - `update_pantry_after_cooking()` - Smart pantry update with staple preservation

- **Files Modified**:
  - `lib/weekly_plan_manager.py` (new file)
  - `pages/generate_recipes.py`
  - `pages/cooking_mode.py`
  - `pages/weekly_planner.py`
  - `pages/pantry.py` (renamed from update_pantry.py)
  - `app.py`
  - `pages/shopping_list.py`
  - Documentation files (README.md, SPEC.md)

### Documentation
- Updated README.md with "How It Works" section explaining integrated workflow
- Updated SPEC.md Key Features with shopping list sync and pantry updates
- Updated SPEC.md Sample User Flows with complete end-to-end examples
- Updated project structure documentation

## Previous Releases

### [1.0.0] - 2025-11-27
- Initial release with core features
- Recipe generation with Claude AI
- Pantry management (manual and photo upload)
- Weekly meal planner
- Shopping list with buy/remove actions
- Cooking mode with interactive AI assistant
- Meal history and recipe ratings
