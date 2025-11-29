# Weekly Meal Planner - Feature Plan & Task Breakdown

**Feature Owner:** TBD
**Estimated Time:** 2-3 hours
**Priority:** PHASE 2 - Feature Enhancement
**Dependencies:** Recipe view page (being built by another engineer)

---

## 🎯 Feature Overview

Allow users to plan up to 7 meals for the week by selecting from their saved recipes (loved/liked). Users can view all selected meals in a grid, see recipe details, and open full recipes in the recipe view.

### User Story
> *As a user, I want to plan my meals for the week by selecting from my favorite recipes, so that I can organize my cooking and shopping more efficiently.*

### Key Requirements
- ✅ Select up to 7 meals from saved recipes (loved.md + liked.md)
- ✅ Order doesn't matter (no specific day assignment)
- ✅ View all selected meals in a grid/list format
- ✅ See recipe preview (name, time, difficulty, key info)
- ✅ Open recipe in full recipe view (integration point)
- ✅ Persist weekly plan to markdown file
- ✅ Edit plan (add/remove meals)
- ✅ Clear entire plan

---

## 📐 Architecture & Design

### Data Structure

**File:** `data/weekly_plan.md`

```markdown
# Weekly Meal Plan

Last updated: 2025-11-27

## Current Plan (Week of 2025-11-25)

### 1. Coconut Curry Lentil Soup
**Source:** Loved Recipes
**Time:** 30 minutes
**Difficulty:** Easy
**Added:** 2025-11-27

### 2. Sheet Pan Roasted Vegetables with Tahini
**Source:** Loved Recipes
**Time:** 40 minutes
**Difficulty:** Easy
**Added:** 2025-11-27

### 3. Thai Red Curry with Tofu
**Source:** Liked Recipes
**Time:** 35 minutes
**Difficulty:** Medium
**Added:** 2025-11-27

<!-- Max 7 meals allowed -->

## Plan History

### Week of 2025-11-18
- Ginger Garlic Stir-Fry
- Mediterranean Chickpea Salad
- Black Bean Tacos
<!-- Archived plans for reference -->
```

### Recipe Data Model

Based on existing architecture, recipes have:
```python
{
    'name': str,              # Recipe name
    'time_minutes': int,      # Cooking time
    'difficulty': str,        # easy/medium/hard
    'cuisine': str,           # Optional
    'ingredients_available': str,  # Comma-separated
    'ingredients_needed': str,     # Comma-separated
    'description': str,       # Optional
    'source': str,            # 'loved' or 'liked'
}
```

---

## 🗂️ File Structure

```
Meal-planner-v2/
├── data/
│   └── weekly_plan.md          # NEW: Weekly plan storage
│
├── pages/
│   └── weekly_planner.py       # NEW: Weekly planner page
│
├── lib/
│   ├── file_manager.py         # MODIFY: Add weekly_plan file type
│   └── recipe_parser.py        # NEW: Parse recipes from markdown
│
└── app.py                      # MODIFY: Add navigation button
```

---

## 📋 Detailed Task Breakdown

### **TASK 1: Data Layer - Recipe Parser**
**File:** `lib/recipe_parser.py` (NEW)
**Time:** 30 minutes
**Priority:** HIGH

**Description:**
Create a reusable recipe parser to extract recipe data from markdown files.

**Subtasks:**
1. Create `lib/recipe_parser.py`
2. Implement `parse_recipe_section(content: str) -> dict`:
   - Extract recipe name (## headers)
   - Parse metadata (Last made, Rating, Time, Difficulty, etc.)
   - Extract ingredients list
   - Parse notes/description
   - Return structured recipe dict
3. Implement `parse_all_recipes(content: str) -> list[dict]`:
   - Split markdown by `---` separators
   - Parse each section
   - Return list of recipe dicts
4. Add comprehensive type hints and docstrings
5. Add structured logging
6. Handle malformed entries gracefully

**Testing:**
- Parse loved.md and verify all recipes extracted
- Test with missing fields (should handle gracefully)
- Verify correct data types returned

**Code Example:**
```python
def parse_recipe_section(section: str) -> dict:
    """Parse a single recipe section from markdown.

    Args:
        section: Markdown content for one recipe

    Returns:
        Dictionary with recipe data (name, time, difficulty, etc.)
    """
    recipe = {
        'name': None,
        'time_minutes': None,
        'difficulty': None,
        'cuisine': None,
        'rating': None,
        'last_made': None,
        'ingredients': [],
        'notes': None,
    }

    lines = section.split('\n')

    for line in lines:
        if line.startswith('##'):
            recipe['name'] = line.replace('##', '').strip()
        elif line.startswith('**Time:**'):
            # Extract minutes from "30 minutes"
            time_str = line.replace('**Time:**', '').strip()
            # ... parsing logic

    return recipe
```

---

### **TASK 2: File Manager Integration**
**File:** `lib/file_manager.py` (MODIFY)
**Time:** 15 minutes
**Priority:** HIGH

**Description:**
Add weekly_plan support to the file manager.

**Subtasks:**
1. Add `"weekly_plan"` to `DataFileType` Literal
2. Add file path mapping: `"weekly_plan": "data/weekly_plan.md"`
3. Test file loading with `load_data_file("weekly_plan")`

**Code Changes:**
```python
# Line ~20-29
DataFileType = Literal[
    "staples",
    "fresh",
    "shopping_list",
    "loved_recipes",
    "liked_recipes",
    "not_again_recipes",
    "preferences",
    "meal_history",
    "weekly_plan",  # ADD THIS
]

# Line ~49-58
file_map = {
    "staples": "data/pantry/staples.md",
    # ... existing mappings ...
    "weekly_plan": "data/weekly_plan.md",  # ADD THIS
}
```

---

### **TASK 3: Create Weekly Plan Data File**
**File:** `data/weekly_plan.md` (NEW)
**Time:** 5 minutes
**Priority:** MEDIUM

**Description:**
Create the initial markdown file with template structure.

**Content:**
```markdown
# Weekly Meal Plan

Last updated: 2025-11-27

## Current Plan

*No meals planned yet. Click "Add Meal" to start planning!*

<!-- Instructions:
- Select up to 7 meals for the week
- Order doesn't matter - just collect the meals you want to cook
- Use the shopping list feature to aggregate ingredients
-->

## Plan History

<!-- Past weekly plans will be archived here automatically -->
```

---

### **TASK 4: Weekly Planner Page - UI Skeleton**
**File:** `pages/weekly_planner.py` (NEW)
**Time:** 20 minutes
**Priority:** HIGH

**Description:**
Create the page structure with basic UI layout.

**Subtasks:**
1. Create file with proper imports and logging setup
2. Add page config (title, icon, layout)
3. Add authentication with `require_authentication()`
4. Create tab layout:
   - Tab 1: "📅 Current Plan"
   - Tab 2: "➕ Add Meals"
   - Tab 3: "📊 Plan Overview"
5. Add "Back to Home" navigation

**Code Structure:**
```python
"""Weekly Meal Planner Page.

Allows users to plan up to 7 meals for the week by selecting
from their saved recipes (loved and liked collections).
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import datetime

from lib.auth import require_authentication
from lib.file_manager import load_data_file, get_data_file_path
from lib.recipe_parser import parse_all_recipes  # NEW
from lib.logging_config import get_logger, setup_logging

setup_logging("INFO")
logger = get_logger(__name__)

st.set_page_config(
    page_title="Weekly Planner - AI Recipe Planner",
    page_icon="📅",
    layout="wide",
)

require_authentication()

st.title("📅 Weekly Meal Planner")
st.markdown("*Plan up to 7 meals for the week*")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📅 Current Plan", "➕ Add Meals", "📊 Overview"])

with tab1:
    st.markdown("### Your Meal Plan")
    # TODO: Display current plan

with tab2:
    st.markdown("### Add Meals to Plan")
    # TODO: Recipe selection interface

with tab3:
    st.markdown("### Plan Overview")
    # TODO: Shopping list preview, time estimates
```

---

### **TASK 5: Load and Parse Saved Recipes**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 25 minutes
**Priority:** HIGH

**Description:**
Load loved and liked recipes for selection.

**Subtasks:**
1. Load loved.md and liked.md using file_manager
2. Parse recipes using recipe_parser
3. Combine into single list with source tag
4. Store in session state for reuse
5. Handle file not found errors gracefully

**Code Example:**
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_available_recipes() -> list[dict]:
    """Load all recipes available for meal planning.

    Returns:
        List of recipe dicts from loved and liked collections
    """
    try:
        recipes = []

        # Load loved recipes
        loved_content = load_data_file("loved_recipes")
        loved_recipes = parse_all_recipes(loved_content)
        for recipe in loved_recipes:
            recipe['source'] = 'Loved'
            recipe['source_file'] = 'loved_recipes'
            recipes.append(recipe)

        # Load liked recipes
        liked_content = load_data_file("liked_recipes")
        liked_recipes = parse_all_recipes(liked_content)
        for recipe in liked_recipes:
            recipe['source'] = 'Liked'
            recipe['source_file'] = 'liked_recipes'
            recipes.append(recipe)

        logger.info(
            "Loaded recipes for meal planning",
            extra={"total_recipes": len(recipes)}
        )

        return recipes

    except Exception as e:
        logger.error("Failed to load recipes", exc_info=True)
        st.error("❌ Could not load saved recipes")
        return []
```

---

### **TASK 6: Recipe Selection Interface**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 30 minutes
**Priority:** HIGH

**Description:**
Build the UI for selecting recipes to add to the weekly plan.

**Subtasks:**
1. Display available recipes in searchable/filterable grid
2. Add search box for filtering by name
3. Add filter by source (Loved/Liked)
4. Add filter by time/difficulty
5. Show recipe cards with key info
6. Add "➕ Add to Plan" button for each recipe
7. Disable button if plan already has 7 meals
8. Show feedback when meal added

**UI Design:**
```
┌─────────────────────────────────────────┐
│ 🔍 Search: [               ]            │
│ Filter: [All] [Loved] [Liked]           │
│ Time: [All] [<30min] [30-45] [45+]      │
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────┐ ┌─────────────┐        │
│ │ Recipe 1    │ │ Recipe 2    │        │
│ │ ⭐⭐⭐⭐⭐     │ │ ⭐⭐⭐⭐       │        │
│ │ 30 min      │ │ 45 min      │        │
│ │ Easy        │ │ Medium      │        │
│ │ [Add to Plan] [Add to Plan]│        │
│ └─────────────┘ └─────────────┘        │
│                                         │
└─────────────────────────────────────────┘
```

**Code Example:**
```python
# In tab2
with tab2:
    st.markdown("### Add Meals to Plan")

    # Load available recipes
    available_recipes = load_available_recipes()

    # Check current plan size
    current_plan = load_current_plan()  # Returns list
    plan_full = len(current_plan) >= 7

    if plan_full:
        st.warning("⚠️ Your plan is full (7 meals). Remove a meal to add more.")

    # Filters
    col1, col2 = st.columns([2, 1])

    with col1:
        search = st.text_input("🔍 Search recipes", placeholder="Type to filter...")

    with col2:
        source_filter = st.selectbox("Filter by", ["All", "Loved", "Liked"])

    # Filter recipes
    filtered = available_recipes

    if search:
        filtered = [r for r in filtered if search.lower() in r['name'].lower()]

    if source_filter != "All":
        filtered = [r for r in filtered if r['source'] == source_filter]

    st.markdown(f"**Showing {len(filtered)} recipes**")
    st.markdown("---")

    # Display in columns (3 per row)
    cols_per_row = 3

    for i in range(0, len(filtered), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, col in enumerate(cols):
            if i + j < len(filtered):
                recipe = filtered[i + j]

                with col:
                    with st.container():
                        st.markdown(f"**{recipe['name']}**")

                        # Metadata
                        if recipe.get('rating'):
                            st.caption(f"{'⭐' * recipe['rating']}")

                        meta = []
                        if recipe.get('time_minutes'):
                            meta.append(f"⏱️ {recipe['time_minutes']} min")
                        if recipe.get('difficulty'):
                            meta.append(f"📊 {recipe['difficulty'].title()}")

                        if meta:
                            st.caption(" • ".join(meta))

                        # Add button
                        if st.button(
                            "➕ Add to Plan",
                            key=f"add_{recipe['name']}",
                            disabled=plan_full,
                            use_container_width=True
                        ):
                            success = add_recipe_to_plan(recipe)
                            if success:
                                st.success(f"✅ Added {recipe['name']}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to add recipe")
```

---

### **TASK 7: Current Plan Display**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 25 minutes
**Priority:** HIGH

**Description:**
Show the current weekly plan with meal cards and actions.

**Subtasks:**
1. Load current plan from weekly_plan.md
2. Parse plan entries
3. Display meals in numbered list/grid
4. Show recipe preview for each meal
5. Add "View Recipe" button (integration point)
6. Add "Remove" button for each meal
7. Add "Clear Plan" button
8. Show empty state if no meals planned

**UI Design:**
```
┌─────────────────────────────────────────┐
│ Your Weekly Plan (3/7 meals)            │
│                                         │
│ 1. Coconut Curry Lentil Soup           │
│    ⏱️ 30 min • 📊 Easy • ⭐⭐⭐⭐⭐        │
│    [View Recipe] [Remove]              │
│                                         │
│ 2. Sheet Pan Vegetables                │
│    ⏱️ 40 min • 📊 Easy • ⭐⭐⭐⭐⭐        │
│    [View Recipe] [Remove]              │
│                                         │
│ 3. Thai Red Curry                      │
│    ⏱️ 35 min • 📊 Medium • ⭐⭐⭐⭐        │
│    [View Recipe] [Remove]              │
│                                         │
│ [Clear Entire Plan]                    │
└─────────────────────────────────────────┘
```

**Code Example:**
```python
# In tab1
with tab1:
    st.markdown("### Your Weekly Plan")

    current_plan = load_current_plan()

    if not current_plan:
        st.info("📭 No meals planned yet. Go to the 'Add Meals' tab to start planning!")
    else:
        # Header with count
        st.markdown(f"**{len(current_plan)}/7 meals planned**")

        # Progress bar
        st.progress(len(current_plan) / 7)

        st.markdown("---")

        # Display each meal
        for idx, meal in enumerate(current_plan, 1):
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    st.markdown(f"**{idx}. {meal['name']}**")

                    meta = []
                    if meal.get('time_minutes'):
                        meta.append(f"⏱️ {meal['time_minutes']} min")
                    if meal.get('difficulty'):
                        meta.append(f"📊 {meal['difficulty'].title()}")
                    if meal.get('rating'):
                        meta.append(f"{'⭐' * meal['rating']}")

                    if meta:
                        st.caption(" • ".join(meta))

                with col2:
                    if st.button("👁️ View", key=f"view_{idx}"):
                        # TODO: Open recipe in recipe view
                        # This is the integration point with the recipe view page
                        st.session_state['view_recipe'] = meal
                        st.switch_page("pages/recipe_view.py")  # Placeholder

                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{idx}"):
                        success = remove_meal_from_plan(idx - 1)
                        if success:
                            st.success("✅ Removed")
                            st.rerun()

                st.markdown("---")

        # Clear plan button
        if st.button("🗑️ Clear Entire Plan", use_container_width=True):
            if st.session_state.get('confirm_clear'):
                clear_weekly_plan()
                st.session_state['confirm_clear'] = False
                st.success("✅ Plan cleared")
                st.rerun()
            else:
                st.session_state['confirm_clear'] = True
                st.warning("⚠️ Click again to confirm")
```

---

### **TASK 8: Plan Overview Tab**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 20 minutes
**Priority:** MEDIUM

**Description:**
Show aggregated stats and shopping list preview.

**Subtasks:**
1. Calculate total cooking time for the week
2. Show difficulty distribution
3. Show cuisine variety
4. Preview ingredients needed
5. Add "Export Shopping List" button

**UI Design:**
```
┌─────────────────────────────────────────┐
│ Week Overview                           │
│                                         │
│ ⏱️ Total Cook Time: 3.5 hours           │
│ 📊 Difficulty: 5 Easy, 2 Medium         │
│ 🌍 Cuisines: Asian, Mediterranean, etc.│
│                                         │
│ Shopping List Preview:                  │
│ • Coconut milk (2 cans)                │
│ • Tofu (3 blocks)                      │
│ • ... (showing top 10 items)           │
│                                         │
│ [View Full Shopping List]              │
└─────────────────────────────────────────┘
```

---

### **TASK 9: Backend Helper Functions**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 30 minutes
**Priority:** HIGH

**Description:**
Implement core functions for plan management.

**Functions to implement:**

1. **`load_current_plan() -> list[dict]`**
   - Load weekly_plan.md
   - Parse current plan section
   - Return list of recipe dicts

2. **`add_recipe_to_plan(recipe: dict) -> bool`**
   - Validate plan not full (< 7 meals)
   - Format recipe entry
   - Append to weekly_plan.md
   - Return success/failure

3. **`remove_meal_from_plan(index: int) -> bool`**
   - Load current plan
   - Remove meal at index
   - Rewrite file
   - Return success/failure

4. **`clear_weekly_plan() -> bool`**
   - Archive current plan to history section
   - Clear current plan section
   - Return success/failure

**Code Example:**
```python
def add_recipe_to_plan(recipe: dict) -> bool:
    """Add a recipe to the weekly meal plan.

    Args:
        recipe: Recipe dictionary with name, time, difficulty, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load current plan
        plan_path = get_data_file_path("weekly_plan")
        content = plan_path.read_text(encoding="utf-8")

        # Check if plan is full
        current_plan = load_current_plan()
        if len(current_plan) >= 7:
            logger.warning("Cannot add recipe - plan is full")
            return False

        # Build entry
        entry = f"\n### {len(current_plan) + 1}. {recipe['name']}\n"
        entry += f"**Source:** {recipe.get('source', 'Unknown')}\n"

        if recipe.get('time_minutes'):
            entry += f"**Time:** {recipe['time_minutes']} minutes\n"

        if recipe.get('difficulty'):
            entry += f"**Difficulty:** {recipe['difficulty'].title()}\n"

        entry += f"**Added:** {datetime.now().strftime('%Y-%m-%d')}\n"
        entry += "\n"

        # Find insertion point (after "## Current Plan")
        lines = content.split('\n')
        insert_index = -1

        for i, line in enumerate(lines):
            if line.startswith('## Current Plan'):
                insert_index = i + 1
                # Skip empty state message if present
                if i + 2 < len(lines) and lines[i + 2].startswith('*No meals'):
                    insert_index = i + 2
                break

        if insert_index == -1:
            logger.error("Could not find insertion point in weekly plan")
            return False

        # Insert entry
        lines.insert(insert_index, entry)

        # Write back
        plan_path.write_text('\n'.join(lines), encoding="utf-8")

        logger.info(
            "Added recipe to weekly plan",
            extra={"recipe_name": recipe['name'], "plan_size": len(current_plan) + 1}
        )

        return True

    except Exception as e:
        logger.error("Failed to add recipe to plan", exc_info=True)
        return False
```

---

### **TASK 10: Integration with Recipe View Page**
**File:** `pages/weekly_planner.py` (MODIFY)
**Time:** 15 minutes
**Priority:** MEDIUM (depends on other engineer)
**Dependencies:** Recipe view page must exist

**Description:**
Integrate with the recipe view page being built by another engineer.

**Integration Points:**

1. **Pass recipe data via session state**
```python
# In weekly_planner.py
if st.button("👁️ View Recipe"):
    # Store recipe data for recipe view page
    st.session_state['selected_recipe'] = meal
    st.session_state['recipe_source'] = meal['source_file']
    st.switch_page("pages/recipe_view.py")
```

2. **Recipe view page should handle**
```python
# In recipe_view.py (being built by other engineer)
if 'selected_recipe' in st.session_state:
    recipe = st.session_state['selected_recipe']
    # Display full recipe details
```

**Coordination needed:**
- Agree on session state variable names
- Agree on recipe data structure
- Test integration when recipe view is ready

---

### **TASK 11: Navigation Integration**
**File:** `app.py` (MODIFY)
**Time:** 10 minutes
**Priority:** MEDIUM

**Description:**
Add Weekly Planner to main navigation.

**Changes:**

1. **Add button to Quick Actions** (around line 66-84)
```python
# Change from 3 columns to 4
col1, col2, col3, col4 = st.columns(4)

# ... existing buttons ...

with col4:
    if st.button("📅 Weekly Planner", use_container_width=True):
        st.switch_page("pages/weekly_planner.py")
    st.caption("Plan up to 7 meals for the week")
```

2. **Add to sidebar** (around line 128-134)
```python
with st.sidebar:
    # ... existing nav ...
    st.page_link("pages/weekly_planner.py", label="📅 Weekly Planner", icon="📅")
```

---

### **TASK 12: Testing & Polish**
**File:** All weekly planner files
**Time:** 30 minutes
**Priority:** HIGH

**Description:**
Test end-to-end and fix any issues.

**Test Cases:**

1. **Add Meals Flow**
   - [ ] Can load saved recipes from loved/liked
   - [ ] Search/filter works correctly
   - [ ] Can add meals (up to 7)
   - [ ] Cannot add 8th meal (shows error)
   - [ ] Success messages appear

2. **View Plan Flow**
   - [ ] Empty state shows when no meals
   - [ ] Meals display with correct info
   - [ ] Progress bar updates
   - [ ] Can view recipe details (once integrated)

3. **Remove Meals Flow**
   - [ ] Can remove individual meals
   - [ ] Plan renumbers correctly
   - [ ] Can add meals after removing
   - [ ] Can clear entire plan
   - [ ] Clear requires confirmation

4. **Persistence**
   - [ ] Plan survives page reload
   - [ ] Plan data saved to weekly_plan.md
   - [ ] Markdown file is well-formatted

5. **Edge Cases**
   - [ ] Handles empty recipe collections
   - [ ] Handles malformed recipe data
   - [ ] Handles file permissions errors
   - [ ] Mobile responsive layout

**Polish:**
- Add loading spinners for slow operations
- Improve error messages
- Add helpful tooltips
- Optimize for mobile view

---

## 📊 Time Estimates Summary

| Task | Time | Priority | Status |
|------|------|----------|--------|
| 1. Recipe Parser | 30 min | HIGH | Not Started |
| 2. File Manager Integration | 15 min | HIGH | Not Started |
| 3. Create Data File | 5 min | MEDIUM | Not Started |
| 4. UI Skeleton | 20 min | HIGH | Not Started |
| 5. Load Recipes | 25 min | HIGH | Not Started |
| 6. Recipe Selection UI | 30 min | HIGH | Not Started |
| 7. Current Plan Display | 25 min | HIGH | Not Started |
| 8. Overview Tab | 20 min | MEDIUM | Not Started |
| 9. Backend Functions | 30 min | HIGH | Not Started |
| 10. Recipe View Integration | 15 min | MEDIUM | Blocked (dependency) |
| 11. Navigation Integration | 10 min | MEDIUM | Not Started |
| 12. Testing & Polish | 30 min | HIGH | Not Started |
| **TOTAL** | **3h 15min** | | |

**Critical Path:** Tasks 1 → 2 → 4 → 5 → 6 → 7 → 9 → 12
**Estimated:** 2h 45min (excluding integration and overview)

---

## 🔗 Integration Points

### With Recipe View Page (Other Engineer)

**Session State Contract:**
```python
# Weekly planner sets:
st.session_state['selected_recipe'] = {
    'name': str,
    'time_minutes': int,
    'difficulty': str,
    'cuisine': str,
    'ingredients': list[str],
    'notes': str,
    'source_file': str,  # 'loved_recipes' or 'liked_recipes'
}

# Recipe view page reads:
recipe = st.session_state.get('selected_recipe')
```

**Navigation:**
```python
# From weekly planner:
st.switch_page("pages/recipe_view.py")

# Back to planner (optional):
st.switch_page("pages/weekly_planner.py")
```

---

## 🎨 UI/UX Considerations

### Design Principles
1. **Simple & Clean** - Focus on essential info, no clutter
2. **Quick Actions** - Add/remove meals in 1-2 clicks
3. **Visual Feedback** - Clear success/error messages
4. **Progress Indication** - Show plan fullness (X/7 meals)
5. **Mobile Friendly** - Responsive grid layout

### Visual Hierarchy
```
Primary: Current plan display
Secondary: Add meals interface
Tertiary: Overview/stats
```

### Color Coding (using Streamlit defaults)
- Success: Green (meal added)
- Warning: Yellow (plan full)
- Error: Red (operation failed)
- Info: Blue (empty state, tips)

---

## 🚀 Future Enhancements (Phase 3)

These are OUT OF SCOPE for initial implementation but good to consider:

1. **Day Assignment**
   - Assign meals to specific days (Mon-Sun)
   - Drag-and-drop reordering
   - Calendar view

2. **Smart Suggestions**
   - AI suggests balanced weekly plan
   - Optimize for ingredient reuse
   - Dietary variety scoring

3. **Shopping List Integration**
   - Auto-generate shopping list from plan
   - Check against current pantry
   - Show what to buy

4. **Meal Prep Mode**
   - Group by prep method (roasting, stovetop, etc.)
   - Batch cooking suggestions
   - Prep order optimization

5. **Plan Templates**
   - Save favorite weekly plans
   - Load template plans
   - Share plans with others

6. **Nutritional Overview**
   - Calorie estimates
   - Macro breakdown
   - Dietary balance score

---

## ✅ Success Criteria

The feature is complete when:

- [ ] Users can select up to 7 recipes from saved collections
- [ ] Selected meals display in a clear, organized view
- [ ] Users can view recipe details (when integration ready)
- [ ] Users can add/remove meals easily
- [ ] Plan persists to markdown file correctly
- [ ] All navigation works smoothly
- [ ] No errors in production logs
- [ ] Mobile layout works well
- [ ] End-to-end testing passes

---

## 📝 Notes for Implementation

### Code Quality Standards
Follow existing patterns from Phase 1:
- ✅ Type hints on all functions
- ✅ Google-style docstrings
- ✅ Structured logging with context
- ✅ Error handling with specific exceptions
- ✅ Session state management
- ✅ Reusable helper functions

### File Naming Conventions
- Page files: `pages/weekly_planner.py`
- Library files: `lib/recipe_parser.py`
- Data files: `data/weekly_plan.md`

### Git Commit Strategy
Group related changes:
1. Commit 1: Backend (parser + file manager)
2. Commit 2: UI skeleton + data file
3. Commit 3: Recipe selection + plan display
4. Commit 4: Integration + testing

---

**Last Updated:** 2025-11-27
**Document Owner:** Development Team
**Review Date:** After Phase 2 completion
