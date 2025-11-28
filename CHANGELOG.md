# Changelog

All notable changes to the AI Recipe Planner will be documented in this file.

## [Unreleased]

### Added - 2025-11-28

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

### Technical Details
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
