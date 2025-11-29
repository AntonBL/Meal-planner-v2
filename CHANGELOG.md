# Changelog

All notable changes to the AI Recipe Planner will be documented in this file.

## [Unreleased]

### Added - 2025-11-29

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
