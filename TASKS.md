# AI Recipe Planner - Detailed Task Breakdown

**Last Updated:** 2025-11-27
**Status:** Ready for Implementation

---

## ⚠️ IMPORTANT: Code Flexibility Principles

**All code in this project MUST be flexible for changing customer requirements.**

### Core Design Rules

1. **Configuration Over Hardcoding**
   - Use variables for options that might change
   - Keep magic numbers/strings in constants
   - Make it easy to add new categories/fields

2. **Separation of Concerns**
   - Helper functions for business logic
   - UI code separate from data logic
   - Reusable functions with clear parameters

3. **Graceful Degradation**
   - Handle missing fields (use `.get()` for dicts)
   - Parse functions should skip malformed lines
   - Error messages guide user to fix issues

4. **DRY (Don't Repeat Yourself)**
   - One function for adding items (works for all categories)
   - One parser for pantry items (works for all types)
   - Shared patterns across pages

5. **Clear Extension Points**
   - Want new category? Update list + add file
   - Want new field? Add to form + parser + display
   - Want new page? Copy pattern from existing pages

### Example: Future-Proof Design

```python
# GOOD - Easy to extend
CATEGORIES = ["Pantry Staple", "Fresh Item"]  # Easy to add "Frozen Item"
category = st.radio("Category:", CATEGORIES)

# BAD - Hardcoded
category = st.radio("Category:", ["Pantry Staple", "Fresh Item"])
```

```python
# GOOD - Handles missing data
if item.get('expiry_date'):  # Won't crash if field missing
    display_expiry(item['expiry_date'])

# BAD - Will crash
display_expiry(item['expiry_date'])  # KeyError if field doesn't exist
```

**When implementing tasks, always ask:**
- What if customer wants to add another field here?
- What if they want to change this category list?
- Will this break if data format changes slightly?

---

## 📖 How to Use This Document

Each task is broken down into:
- **File Path:** Exact location where work is needed
- **Function/Component:** What to create or modify
- **Implementation Details:** Step-by-step instructions
- **Dependencies:** What must be done first
- **Testing:** How to verify it works
- **Estimated Time:** Approximate duration

---

# PHASE 1: MVP - Complete Core Loop

**Total Estimated Time:** 2-3 hours
**Goal:** Functional meal planning system with all navigation working

---

## GROUP 1: Pantry Page (Foundation)
**Estimated Time:** 45 minutes
**Priority:** CRITICAL (Blocking navigation errors)

### Task 1.1: Create Pantry Page File
**File:** `pages/pantry.py`
**Time:** 5 minutes
**Dependencies:** None

**Steps:**
1. Create new file `pages/pantry.py`
2. Add module docstring:
   ```python
   """Pantry Page for AI Recipe Planner.

   Allows users to manually add, view, edit, and remove pantry items.
   Supports both pantry staples and fresh items with expiry tracking.
   """
   ```
3. Add dotenv imports at top:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```
4. Import required modules:
   ```python
   import streamlit as st
   from pathlib import Path
   from datetime import datetime, date
   from typing import Optional

   from lib.file_manager import load_data_file, get_data_file_path
   from lib.exceptions import DataFileNotFoundError
   from lib.logging_config import get_logger, setup_logging
   ```
5. Set up logging:
   ```python
   setup_logging("INFO")
   logger = get_logger(__name__)
   ```
6. Configure page:
   ```python
   st.set_page_config(
       page_title="Pantry - AI Recipe Planner",
       page_icon="📝",
       layout="wide",
   )
   ```
7. Add title and description:
   ```python
   st.title("📝 Pantry")
   st.markdown("*Manage your pantry staples and fresh items*")
   ```

**Testing:**
- Access `https://50.116.63.56` and click "Pantry"
- Should load without errors (even if empty)
- Check logs: `tail -f /var/log/meal-planner.out.log`

---

### Task 1.2: Add Manual Entry Form (Pantry Staples)
**File:** `pages/pantry.py`
**Time:** 15 minutes
**Dependencies:** Task 1.1

**Steps:**
1. Create tabs for organization:
   ```python
   tab1, tab2, tab3 = st.tabs(["➕ Add Items", "📦 View Pantry", "🗑️ Manage Items"])
   ```

2. In `tab1`, create manual entry form:
   ```python
   with tab1:
       st.markdown("### Add Items to Pantry")

       # Category selection
       category = st.radio(
           "Item Category:",
           ["Pantry Staple", "Fresh Item"],
           horizontal=True,
           help="Pantry staples: dry goods, canned items, spices. Fresh items: produce, dairy, meat."
       )

       # Item entry form
       with st.form("add_item_form", clear_on_submit=True):
           col1, col2 = st.columns(2)

           with col1:
               item_name = st.text_input(
                   "Item Name *",
                   placeholder="e.g., Olive Oil, Tomatoes, Rice",
                   help="What item are you adding?"
               )

               quantity = st.text_input(
                   "Quantity *",
                   placeholder="e.g., 2 bottles, 1 lb, 500g",
                   help="How much do you have?"
               )

           with col2:
               # Show expiry date picker only for fresh items
               expiry_date = None
               if category == "Fresh Item":
                   expiry_date = st.date_input(
                       "Expiry/Use-by Date (Optional)",
                       value=None,
                       help="When should this be used by?"
                   )
               else:
                   st.info("💡 Pantry staples don't need expiry dates")

           notes = st.text_area(
               "Notes (Optional)",
               placeholder="Any additional information...",
               height=80
           )

           submitted = st.form_submit_button("➕ Add Item", use_container_width=True)
   ```

3. Add form submission handler:
   ```python
           if submitted:
               # Validate inputs
               if not item_name or not item_name.strip():
                   st.error("⚠️ Please enter an item name")
               elif not quantity or not quantity.strip():
                   st.error("⚠️ Please enter a quantity")
               else:
                   # Call function to add item (will create in next task)
                   success = add_item_to_pantry(
                       item_name=item_name.strip(),
                       quantity=quantity.strip(),
                       category=category,
                       expiry_date=expiry_date,
                       notes=notes.strip() if notes else None
                   )

                   if success:
                       st.success(f"✅ Added {item_name} to {category.lower()}!")
                       logger.info(
                           "Item added to pantry",
                           extra={
                               "item_name": item_name,
                               "category": category,
                               "quantity": quantity
                           }
                       )
                   else:
                       st.error("❌ Failed to add item. Check logs.")
   ```

**Testing:**
- Form should render correctly
- Category radio buttons work
- Expiry date picker only shows for "Fresh Item"
- Submit button disabled until function created (will error - expected)

---

### Task 1.3: Create Add Item Backend Function
**File:** `pages/pantry.py` (helper function section)
**Time:** 15 minutes
**Dependencies:** Task 1.2

**Steps:**
1. Add helper function before the form code:
   ```python
   def add_item_to_pantry(
       item_name: str,
       quantity: str,
       category: str,
       expiry_date: Optional[date] = None,
       notes: Optional[str] = None
   ) -> bool:
       """Add an item to the appropriate pantry file.

       Args:
           item_name: Name of the item
           quantity: Quantity/amount
           category: "Pantry Staple" or "Fresh Item"
           expiry_date: Optional expiry date for fresh items
           notes: Optional additional notes

       Returns:
           True if successful, False otherwise
       """
       try:
           # Determine which file to update
           if category == "Pantry Staple":
               file_path = get_data_file_path("staples")
           else:
               file_path = get_data_file_path("fresh")

           # Read current content
           current_content = file_path.read_text(encoding="utf-8")

           # Build new item line
           today = datetime.now().strftime("%Y-%m-%d")
           new_line = f"- {item_name} - {quantity} - Added: {today}"

           if expiry_date:
               new_line += f" - Expires: {expiry_date.strftime('%Y-%m-%d')}"

           if notes:
               new_line += f" - Notes: {notes}"

           new_line += "\n"

           # Find where to insert (after first section header)
           lines = current_content.split('\n')
           insert_index = -1

           # Find first section (starts with ##)
           for i, line in enumerate(lines):
               if line.startswith('##'):
                   # Insert after this header line
                   insert_index = i + 1
                   break

           if insert_index == -1:
               # No section found, append to end
               lines.append(new_line)
           else:
               # Insert after section header
               lines.insert(insert_index, new_line)

           # Write back to file
           updated_content = '\n'.join(lines)
           file_path.write_text(updated_content, encoding="utf-8")

           logger.info(
               "Successfully added item to pantry file",
               extra={
                   "item_name": item_name,
                   "file_path": str(file_path),
                   "category": category
               }
           )

           return True

       except Exception as e:
           logger.error(
               "Failed to add item to pantry",
               extra={"item_name": item_name, "error": str(e)},
               exc_info=True
           )
           return False
   ```

**Testing:**
- Add a pantry staple: "Olive Oil", "1 bottle"
- Check `data/pantry/staples.md` file contains new item
- Add a fresh item: "Milk", "1 gallon", with expiry date
- Check `data/pantry/fresh.md` file contains new item with date
- Verify timestamps are correct

---

### Task 1.4: Create View Pantry Tab
**File:** `pages/pantry.py`
**Time:** 10 minutes
**Dependencies:** Task 1.1

**Steps:**
1. In `tab2`, add pantry viewer:
   ```python
   with tab2:
       st.markdown("### 📦 Current Pantry Contents")

       # Add filter
       view_category = st.radio(
           "View:",
           ["All Items", "Pantry Staples", "Fresh Items"],
           horizontal=True
       )

       try:
           items_to_display = []

           if view_category in ["All Items", "Pantry Staples"]:
               staples_content = load_data_file("staples")
               staples_items = parse_pantry_items(staples_content, "Pantry Staple")
               items_to_display.extend(staples_items)

           if view_category in ["All Items", "Fresh Items"]:
               fresh_content = load_data_file("fresh")
               fresh_items = parse_pantry_items(fresh_content, "Fresh Item")
               items_to_display.extend(fresh_items)

           if not items_to_display:
               st.info("📭 No items in pantry yet. Add some using the form above!")
           else:
               st.markdown(f"**Total items: {len(items_to_display)}**")

               # Display items in a nice format
               for item in items_to_display:
                   with st.container():
                       col1, col2, col3 = st.columns([3, 2, 1])

                       with col1:
                           st.markdown(f"**{item['name']}**")

                       with col2:
                           st.markdown(f"*{item['quantity']}*")

                       with col3:
                           badge = "🥫" if item['category'] == "Pantry Staple" else "🥬"
                           st.markdown(badge)

                       # Show metadata
                       metadata = []
                       if item.get('added_date'):
                           metadata.append(f"Added: {item['added_date']}")
                       if item.get('expiry_date'):
                           metadata.append(f"Expires: {item['expiry_date']}")
                       if item.get('notes'):
                           metadata.append(f"Notes: {item['notes']}")

                       if metadata:
                           st.caption(" • ".join(metadata))

                       st.markdown("---")

       except DataFileNotFoundError as e:
           st.error(f"❌ Could not load pantry data: {str(e)}")
       except Exception as e:
           st.error(f"❌ Unexpected error: {str(e)}")
           logger.error("Error displaying pantry", exc_info=True)
   ```

2. Add parsing helper function:
   ```python
   def parse_pantry_items(content: str, category: str) -> list[dict]:
       """Parse pantry markdown content into structured items.

       Args:
           content: Markdown file content
           category: "Pantry Staple" or "Fresh Item"

       Returns:
           List of item dictionaries with keys: name, quantity, category, added_date, expiry_date, notes
       """
       items = []
       lines = content.split('\n')

       for line in lines:
           line = line.strip()
           if not line.startswith('-'):
               continue

           # Remove leading dash
           line = line[1:].strip()

           # Parse item (format: Name - Quantity - Added: YYYY-MM-DD - Expires: YYYY-MM-DD - Notes: text)
           parts = line.split(' - ')

           if len(parts) < 2:
               continue  # Malformed line

           item = {
               'name': parts[0].strip(),
               'quantity': parts[1].strip(),
               'category': category,
               'added_date': None,
               'expiry_date': None,
               'notes': None
           }

           # Parse additional fields
           for part in parts[2:]:
               if part.startswith('Added:'):
                   item['added_date'] = part.replace('Added:', '').strip()
               elif part.startswith('Expires:') or part.startswith('Use by:'):
                   item['expiry_date'] = part.replace('Expires:', '').replace('Use by:', '').strip()
               elif part.startswith('Notes:'):
                   item['notes'] = part.replace('Notes:', '').strip()

           items.append(item)

       return items
   ```

**Testing:**
- View tab should display all added items
- Filter by category should work
- Items should show with proper formatting
- Metadata (dates, notes) should display correctly

---

## GROUP 2: Meal History Page
**Estimated Time:** 30 minutes
**Priority:** CRITICAL (Blocking navigation errors)

### Task 2.1: Create Meal History Page File
**File:** `pages/meal_history.py`
**Time:** 5 minutes
**Dependencies:** None

**Steps:**
1. Create new file `pages/meal_history.py`
2. Add module docstring and imports:
   ```python
   """Meal History Page for AI Recipe Planner.

   View past meals, ratings, and cooking notes.
   """

   from dotenv import load_dotenv
   load_dotenv()

   import streamlit as st
   from pathlib import Path
   from datetime import datetime
   from typing import Optional

   from lib.file_manager import load_data_file
   from lib.exceptions import DataFileNotFoundError
   from lib.logging_config import get_logger, setup_logging

   setup_logging("INFO")
   logger = get_logger(__name__)
   ```

3. Configure page:
   ```python
   st.set_page_config(
       page_title="Meal History - AI Recipe Planner",
       page_icon="📅",
       layout="wide",
   )

   st.title("📅 Meal History")
   st.markdown("*Your cooking journal and recipe ratings*")
   ```

**Testing:**
- Click "Meal History" from home page
- Page should load without errors

---

### Task 2.2: Parse and Display Meal History
**File:** `pages/meal_history.py`
**Time:** 20 minutes
**Dependencies:** Task 2.1

**Steps:**
1. Add meal parser function:
   ```python
   def parse_meal_history(content: str) -> list[dict]:
       """Parse meal history markdown into structured data.

       Args:
           content: Meal history markdown content

       Returns:
           List of meals with date, name, rating, notes, ingredients
       """
       meals = []
       lines = content.split('\n')

       current_meal = None

       for i, line in enumerate(lines):
           line = line.strip()

           # Date header (### Monday, 2025-11-25)
           if line.startswith('###'):
               # Save previous meal if exists
               if current_meal:
                   meals.append(current_meal)

               # Start new meal
               date_str = line.replace('###', '').strip()
               current_meal = {
                   'date': date_str,
                   'name': None,
                   'rating': 0,
                   'stars': '',
                   'notes': None,
                   'ingredients': None
               }

           # Recipe name (next line after date, with stars)
           elif current_meal and not current_meal['name'] and '⭐' in line:
               parts = line.split('⭐')
               current_meal['name'] = parts[0].strip('*').strip()
               current_meal['stars'] = '⭐' * (len(parts) - 1)
               current_meal['rating'] = len(parts) - 1

           # Rating line
           elif line.startswith('- Rating:'):
               if current_meal:
                   rating_str = line.replace('- Rating:', '').strip()
                   # Extract number (e.g., "4/5" -> 4)
                   if '/' in rating_str:
                       current_meal['rating'] = int(rating_str.split('/')[0])

           # Notes line
           elif line.startswith('- Notes:'):
               if current_meal:
                   current_meal['notes'] = line.replace('- Notes:', '').strip()

           # Ingredients line
           elif line.startswith('- Ingredients used:'):
               if current_meal:
                   current_meal['ingredients'] = line.replace('- Ingredients used:', '').strip()

       # Don't forget last meal
       if current_meal:
           meals.append(current_meal)

       return meals
   ```

2. Add display logic:
   ```python
   # Load and parse meal history
   try:
       content = load_data_file("meal_history")
       meals = parse_meal_history(content)

       if not meals:
           st.info("📭 No meals logged yet. Cook a recipe and rate it to start your history!")
       else:
           # Stats at top
           col1, col2, col3 = st.columns(3)

           with col1:
               st.metric("🍽️ Total Meals", len(meals))

           with col2:
               avg_rating = sum(m['rating'] for m in meals if m['rating']) / len(meals)
               st.metric("⭐ Average Rating", f"{avg_rating:.1f}/5")

           with col3:
               five_star = sum(1 for m in meals if m['rating'] == 5)
               st.metric("🌟 5-Star Meals", five_star)

           st.markdown("---")

           # Filter options
           col1, col2 = st.columns([2, 1])

           with col1:
               search = st.text_input("🔍 Search meals", placeholder="Search by name or ingredients...")

           with col2:
               min_rating = st.selectbox("Filter by rating", ["All", "5 stars", "4+ stars", "3+ stars"])

           # Filter meals
           filtered_meals = meals

           if search:
               filtered_meals = [
                   m for m in filtered_meals
                   if search.lower() in (m['name'] or '').lower()
                   or search.lower() in (m['ingredients'] or '').lower()
               ]

           if min_rating != "All":
               rating_map = {"5 stars": 5, "4+ stars": 4, "3+ stars": 3}
               min_val = rating_map[min_rating]
               filtered_meals = [m for m in filtered_meals if m['rating'] >= min_val]

           st.markdown(f"### Showing {len(filtered_meals)} meals")

           # Display meals
           for meal in filtered_meals:
               with st.expander(f"**{meal['date']}** - {meal['name']} {meal['stars']}", expanded=False):
                   if meal['rating']:
                       st.markdown(f"**Rating:** {meal['rating']}/5 {meal['stars']}")

                   if meal['notes']:
                       st.markdown(f"**Notes:** {meal['notes']}")

                   if meal['ingredients']:
                       st.markdown("**Ingredients used:**")
                       st.caption(meal['ingredients'])

   except DataFileNotFoundError:
       st.warning("⚠️ Meal history file not found. It will be created when you log your first meal.")
   except Exception as e:
       st.error(f"❌ Error loading meal history: {str(e)}")
       logger.error("Error loading meal history", exc_info=True)
   ```

**Testing:**
- Page should display existing meals from data/meal_history.md
- Stats should calculate correctly
- Search should filter meals
- Rating filter should work
- Expandable sections should show details

---

### Task 2.3: Add "Back to Home" Navigation
**File:** `pages/pantry.py` and `pages/meal_history.py`
**Time:** 5 minutes
**Dependencies:** All previous page tasks

**Steps:**
1. At the bottom of `pages/pantry.py`, add:
   ```python
   # Navigation
   st.markdown("---")
   if st.button("🏠 Back to Home", use_container_width=True):
       st.switch_page("app.py")
   ```

2. At the bottom of `pages/meal_history.py`, add:
   ```python
   # Navigation
   st.markdown("---")
   if st.button("🏠 Back to Home", use_container_width=True):
       st.switch_page("app.py")
   ```

**Testing:**
- Click "Back to Home" on both pages
- Should navigate to home dashboard
- No errors in navigation

---

## GROUP 3: Recipe Feedback System
**Estimated Time:** 45 minutes
**Priority:** HIGH (Core functionality)

### Task 3.1: Create Recipe Feedback Modal
**File:** `pages/generate_recipes.py`
**Time:** 20 minutes
**Dependencies:** GROUP 1 and GROUP 2 complete

**Steps:**
1. Find the "Cook This" button handler (around line 227)

2. Replace the TODO with modal implementation:
   ```python
   with btn_col1:
       if st.button("👨‍🍳 Cook This", key=f"cook_{idx}"):
           # Store selected recipe in session state for feedback
           st.session_state['cooking_recipe'] = recipe
           st.session_state['cooking_recipe_idx'] = idx
           st.session_state['show_feedback_modal'] = True
           logger.info(
               "User selected recipe to cook",
               extra={"recipe_name": recipe["name"]},
           )
           st.rerun()
   ```

3. Add feedback modal above the recipe display section (after line 177):
   ```python
   # Display feedback modal if triggered
   if st.session_state.get('show_feedback_modal', False):
       recipe = st.session_state.get('cooking_recipe', {})

       st.markdown("---")
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
                   # Clear modal state
                   st.session_state['show_feedback_modal'] = False
                   if 'cooking_recipe' in st.session_state:
                       del st.session_state['cooking_recipe']
                   if 'cooking_recipe_idx' in st.session_state:
                       del st.session_state['cooking_recipe_idx']
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

       st.markdown("---")
   ```

**Testing:**
- Click "Cook This" on a recipe
- Feedback modal should appear
- Can select star rating
- Can add notes
- Cancel should close modal
- Submit should save (will implement next)

---

### Task 3.2: Create Save Feedback Backend Function
**File:** `pages/generate_recipes.py`
**Time:** 25 minutes
**Dependencies:** Task 3.1

**Steps:**
1. Add helper function at top of file (after imports):
   ```python
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
       from lib.file_manager import get_data_file_path

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
               recipe_entry += f"**Difficulty:** {recipe['difficulty'].title()}\n"

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
   ```

2. Add datetime import at top:
   ```python
   from datetime import datetime
   ```

**Testing:**
- Cook a recipe and give it 5 stars
- Check `data/meal_history.md` - should have new entry
- Check `data/recipes/loved.md` - should have recipe saved
- Try 3 stars - should go to `liked.md`
- Try 1 star - should go to `not_again.md`
- Verify dates and ratings are correct

---

## GROUP 4: Smart Pantry Updates
**Estimated Time:** 30 minutes
**Priority:** MEDIUM (Nice to have for MVP)

### Task 4.1: Add "Pantry?" Prompt After Cooking
**File:** `pages/generate_recipes.py`
**Time:** 15 minutes
**Dependencies:** Task 3.2

**Steps:**
1. Modify the feedback save success message in Task 3.2:
   ```python
   if submit:
       success = save_recipe_feedback(
           recipe=recipe,
           rating=rating,
           make_again=make_again,
           notes=notes
       )

       if success:
           st.success("✅ Feedback saved! Meal logged to history.")

           # Ask about pantry update
           st.info("🤖 **Smart Pantry Update**\n\nWould you like me to update your pantry by removing the ingredients you used?")

           col1, col2 = st.columns(2)

           with col1:
               if st.button("✅ Yes, Pantry", key="update_pantry_yes", use_container_width=True):
                   # Call pantry update function
                   update_success = update_pantry_after_cooking(recipe)

                   if update_success:
                       st.success("✅ Pantry updated!")
                   else:
                       st.warning("⚠️ Could not update pantry automatically. You can do it manually.")

                   # Clear modal
                   st.session_state['show_feedback_modal'] = False
                   st.rerun()

           with col2:
               if st.button("❌ No Thanks", key="update_pantry_no", use_container_width=True):
                   # Clear modal
                   st.session_state['show_feedback_modal'] = False
                   st.rerun()
       else:
           st.error("❌ Failed to save feedback. Please try again.")
   ```

**Testing:**
- After saving feedback, should see pantry update prompt
- Both buttons should work
- "No Thanks" should just close modal

---

### Task 4.2: Create Pantry Update Backend Function
**File:** `pages/generate_recipes.py`
**Time:** 15 minutes
**Dependencies:** Task 4.1

**Steps:**
1. Add function after `save_recipe_feedback`:
   ```python
   def update_pantry_after_cooking(recipe: dict) -> bool:
       """Update pantry by removing/reducing ingredients used in recipe.

       This is a simple implementation that marks items as potentially used.
       A more sophisticated version would use LLM to intelligently update quantities.

       Args:
           recipe: Recipe dictionary with ingredients

       Returns:
           True if successful, False otherwise
       """
       from lib.file_manager import get_data_file_path

       try:
           # Get all ingredients from recipe
           ingredients = []

           if recipe.get('ingredients_available'):
               ingredients.extend([i.strip().lower() for i in recipe['ingredients_available'].split(',')])

           if recipe.get('ingredients_needed'):
               ingredients.extend([i.strip().lower() for i in recipe['ingredients_needed'].split(',')])

           if not ingredients:
               logger.warning("No ingredients to update pantry with")
               return True

           # Add note to both pantry files about items used
           today = datetime.now().strftime("%Y-%m-%d")
           note = f"\n<!-- Used in {recipe['name']} on {today}: {', '.join(ingredients)} -->\n"

           # Add to staples file
           staples_path = get_data_file_path("staples")
           staples_content = staples_path.read_text(encoding="utf-8")
           staples_path.write_text(staples_content + note, encoding="utf-8")

           # Add to fresh file
           fresh_path = get_data_file_path("fresh")
           fresh_content = fresh_path.read_text(encoding="utf-8")
           fresh_path.write_text(fresh_content + note, encoding="utf-8")

           logger.info(
               "Added usage note to pantry files",
               extra={"recipe_name": recipe['name'], "ingredient_count": len(ingredients)}
           )

           return True

       except Exception as e:
           logger.error(
               "Failed to update pantry after cooking",
               extra={"recipe_name": recipe.get('name'), "error": str(e)},
               exc_info=True
           )
           return False
   ```

**Note:** This is a simple implementation. A more sophisticated version would:
- Use Claude API to intelligently determine what to remove
- Actually remove or reduce quantities
- Handle partial usage (e.g., used half a bottle)

**Testing:**
- Cook a recipe and click "Yes, Pantry"
- Check pantry files for comment with usage note
- Verify ingredients are listed correctly

---

## GROUP 5: Testing & Bug Fixes
**Estimated Time:** 30 minutes
**Priority:** HIGH (Quality assurance)

### Task 5.1: End-to-End User Flow Testing
**Time:** 15 minutes
**Dependencies:** All previous tasks

**Test Scenarios:**
1. **Complete Recipe Flow:**
   - [ ] Go to home page
   - [ ] Click "Generate Recipes"
   - [ ] Select 2+ cuisines
   - [ ] Generate recipes successfully
   - [ ] See 4 recipe suggestions
   - [ ] Click "Cook This" on one recipe
   - [ ] See feedback modal
   - [ ] Rate recipe 5 stars
   - [ ] Add notes
   - [ ] Submit feedback
   - [ ] See pantry update prompt
   - [ ] Click "Yes, Pantry"
   - [ ] Check meal history shows new meal
   - [ ] Check loved.md has recipe saved

2. **Pantry Management Flow:**
   - [ ] Go to "Pantry"
   - [ ] Add pantry staple (Rice, 2 lbs)
   - [ ] Add fresh item (Milk, 1 gallon, expiry: tomorrow)
   - [ ] Switch to "View Pantry" tab
   - [ ] See both items listed
   - [ ] Filter by "Fresh Items" only
   - [ ] See only milk

3. **Meal History Flow:**
   - [ ] Go to "Meal History"
   - [ ] See stats at top (total meals, avg rating)
   - [ ] See logged meal from test 1
   - [ ] Search for recipe name
   - [ ] Filter by 5 stars
   - [ ] Expand meal to see details

**Testing Checklist:**
- [ ] All navigation links work
- [ ] No error messages in UI
- [ ] Logs show INFO level messages (not errors)
- [ ] Data files are updated correctly
- [ ] Forms clear after submission
- [ ] Session state managed properly

---

### Task 5.2: Fix Dashboard "Expiring Soon" Counter
**File:** `app.py`
**Time:** 10 minutes
**Dependencies:** Pantry page complete

**Steps:**
1. Replace the hardcoded `get_expiring_soon()` function in `app.py`:
   ```python
   def get_expiring_soon() -> int:
       """Get count of items expiring soon (next 3 days)."""
       from datetime import datetime, timedelta

       try:
           fresh_content = Path("data/pantry/fresh.md").read_text()

           # Parse expiry dates
           lines = fresh_content.split('\n')
           expiring_count = 0
           today = datetime.now().date()
           threshold = today + timedelta(days=3)

           for line in lines:
               if not line.strip().startswith('-'):
                   continue

               # Look for expiry date
               if 'Expires:' in line or 'Use by:' in line:
                   # Extract date (format: YYYY-MM-DD or ~YYYY-MM-DD)
                   parts = line.split('Expires:') if 'Expires:' in line else line.split('Use by:')
                   if len(parts) > 1:
                       date_str = parts[1].split('-')[0].strip().replace('~', '').strip()

                       try:
                           # Try to parse date
                           if len(date_str) >= 10:  # YYYY-MM-DD
                               expiry_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()

                               # Check if within threshold
                               if today <= expiry_date <= threshold:
                                   expiring_count += 1
                       except ValueError:
                           # Invalid date format, skip
                           continue

           return expiring_count

       except FileNotFoundError:
           return 0
       except Exception:
           return 0
   ```

2. Add datetime import at top of file:
   ```python
   from datetime import datetime, timedelta
   ```

**Testing:**
- Add fresh items with various expiry dates
- Dashboard should show accurate count
- Items expiring in 1-3 days should count
- Items expiring in 4+ days should not count

---

### Task 5.3: Error Handling Review
**Time:** 5 minutes
**Dependencies:** All previous tasks

**Checklist:**
- [ ] All file operations wrapped in try/except
- [ ] User-friendly error messages (no stack traces shown)
- [ ] Errors logged with proper context
- [ ] Empty pantry shows friendly message (not error)
- [ ] Missing data files create helpful warnings
- [ ] API errors show actionable troubleshooting

**Files to Review:**
- `pages/pantry.py`
- `pages/meal_history.py`
- `pages/generate_recipes.py`
- `app.py`

**Action Items:**
- Add missing try/except blocks
- Improve error messages
- Add logging to critical paths

---

# PHASE 2: Enhanced Features

**Total Estimated Time:** 3-4 hours
**Goal:** Photo upload, shopping list, smart features

---

## GROUP 6: Photo Upload (Vision API)
**Estimated Time:** 90 minutes
**Priority:** MEDIUM

### Task 6.1: Create Vision Helper Module
**File:** `lib/vision.py`
**Time:** 30 minutes

**Steps:**
1. Create new file `lib/vision.py`:
   ```python
   """Claude Vision API integration for pantry photo detection.

   Uses Claude's Vision API to detect grocery items from photos.
   """

   import base64
   import logging
   from typing import Optional
   from pathlib import Path

   from lib.llm_agents import ClaudeProvider
   from lib.exceptions import LLMAPIError

   logger = logging.getLogger(__name__)


   def detect_items_from_image(
       image_file,
       provider: Optional[ClaudeProvider] = None
   ) -> list[dict]:
       """Detect grocery items from an uploaded image.

       Args:
           image_file: Streamlit UploadedFile object
           provider: Optional ClaudeProvider instance (creates one if None)

       Returns:
           List of detected items with name, quantity, category

       Raises:
           LLMAPIError: If API call fails
       """
       if provider is None:
           provider = ClaudeProvider()

       try:
           # Read and encode image
           image_bytes = image_file.read()
           image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

           # Determine media type
           file_extension = Path(image_file.name).suffix.lower()
           media_type_map = {
               '.jpg': 'image/jpeg',
               '.jpeg': 'image/jpeg',
               '.png': 'image/png',
               '.gif': 'image/gif',
               '.webp': 'image/webp'
           }
           media_type = media_type_map.get(file_extension, 'image/jpeg')

           # Build prompt
           prompt = """Analyze this image and identify all food and grocery items you can see.

For each item, provide:
1. Item name (be specific, e.g., "red bell peppers" not just "vegetables")
2. Estimated quantity (e.g., "3 peppers", "1 gallon", "2 lbs")
3. Category: either "Pantry Staple" (dry goods, canned items, spices) or "Fresh Item" (produce, dairy, meat)

Format your response as a simple list with one item per line:
- Item name, Quantity, Category

Example:
- Red bell peppers, 3 peppers, Fresh Item
- Olive oil, 1 bottle, Pantry Staple
- Canned tomatoes, 4 cans, Pantry Staple
- Milk (2%), 1 gallon, Fresh Item

Only list items you can clearly identify. Be practical and specific."""

           # Call Claude Vision API
           message = provider.client.messages.create(
               model=provider.model,
               max_tokens=1024,
               messages=[{
                   "role": "user",
                   "content": [
                       {
                           "type": "image",
                           "source": {
                               "type": "base64",
                               "media_type": media_type,
                               "data": image_b64,
                           },
                       },
                       {
                           "type": "text",
                           "text": prompt
                       }
                   ],
               }]
           )

           # Parse response
           response_text = message.content[0].text
           items = parse_vision_response(response_text)

           logger.info(
               "Detected items from image",
               extra={
                   "image_name": image_file.name,
                   "items_detected": len(items)
               }
           )

           return items

       except Exception as e:
           logger.error(
               "Failed to detect items from image",
               extra={"error": str(e)},
               exc_info=True
           )
           raise LLMAPIError(f"Vision API error: {str(e)}") from e


   def parse_vision_response(response_text: str) -> list[dict]:
       """Parse Claude's vision response into structured items.

       Args:
           response_text: Raw text response from Claude

       Returns:
           List of item dictionaries with name, quantity, category
       """
       items = []
       lines = response_text.split('\n')

       for line in lines:
           line = line.strip()

           # Skip empty lines and non-item lines
           if not line or not line.startswith('-'):
               continue

           # Remove leading dash
           line = line[1:].strip()

           # Parse: "Item name, Quantity, Category"
           parts = [p.strip() for p in line.split(',')]

           if len(parts) >= 3:
               items.append({
                   'name': parts[0],
                   'quantity': parts[1],
                   'category': parts[2],
                   'confirmed': True  # User can uncheck
               })
           elif len(parts) == 2:
               # Missing category, default to Fresh Item
               items.append({
                   'name': parts[0],
                   'quantity': parts[1],
                   'category': 'Fresh Item',
                   'confirmed': True
               })

       return items
   ```

**Testing:**
- Unit test with sample image (manually)
- Verify parsing logic works
- Check error handling

---

### Task 6.2: Add Photo Upload Tab to Pantry
**File:** `pages/pantry.py`
**Time:** 40 minutes

**Steps:**
1. Add new tab for photo upload (modify tab creation):
   ```python
   tab1, tab2, tab3, tab4 = st.tabs(["📸 Photo Upload", "➕ Add Items", "📦 View Pantry", "🗑️ Manage Items"])
   ```

2. Implement photo upload tab in `tab1`:
   ```python
   with tab1:
       st.markdown("### 📸 Photo Upload - Auto-detect Items")
       st.markdown("Upload a photo of your groceries, receipt, or pantry to automatically detect items.")

       # File uploader
       uploaded_file = st.file_uploader(
           "Choose an image",
           type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
           help="Supported formats: JPG, PNG, GIF, WebP"
       )

       if uploaded_file:
           # Display image
           col1, col2 = st.columns([1, 1])

           with col1:
               st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

           with col2:
               st.markdown("**Detection Settings:**")

               auto_add = st.checkbox(
                   "Auto-add all detected items",
                   value=False,
                   help="Automatically add all items without confirmation"
               )

               if st.button("🔍 Detect Items", type="primary", use_container_width=True):
                   # Import vision module
                   from lib.vision import detect_items_from_image
                   from lib.llm_agents import ClaudeProvider

                   with st.spinner("🤖 Analyzing image with AI... This may take 10-15 seconds"):
                       try:
                           # Reset file pointer
                           uploaded_file.seek(0)

                           # Detect items
                           provider = ClaudeProvider()
                           detected_items = detect_items_from_image(uploaded_file, provider)

                           # Store in session state
                           st.session_state['detected_items'] = detected_items

                           st.success(f"✅ Detected {len(detected_items)} items!")

                       except Exception as e:
                           st.error(f"❌ Error detecting items: {str(e)}")
                           logger.error("Vision detection error", exc_info=True)

       # Display detected items for confirmation
       if 'detected_items' in st.session_state:
           st.markdown("---")
           st.markdown("### ✅ Detected Items - Review & Confirm")
           st.markdown("Review the detected items below. Uncheck items you don't want to add, or edit quantities.")

           detected_items = st.session_state['detected_items']

           with st.form("confirm_detected_items"):
               # Create editable table
               items_to_add = []

               for idx, item in enumerate(detected_items):
                   col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                   with col1:
                       item_name = st.text_input(
                           "Name",
                           value=item['name'],
                           key=f"name_{idx}",
                           label_visibility="collapsed"
                       )

                   with col2:
                       quantity = st.text_input(
                           "Quantity",
                           value=item['quantity'],
                           key=f"qty_{idx}",
                           label_visibility="collapsed"
                       )

                   with col3:
                       category = st.selectbox(
                           "Category",
                           ["Pantry Staple", "Fresh Item"],
                           index=0 if item['category'] == "Pantry Staple" else 1,
                           key=f"cat_{idx}",
                           label_visibility="collapsed"
                       )

                   with col4:
                       confirmed = st.checkbox(
                           "Add",
                           value=item.get('confirmed', True),
                           key=f"confirm_{idx}",
                           label_visibility="collapsed"
                       )

                   if confirmed:
                       items_to_add.append({
                           'name': item_name,
                           'quantity': quantity,
                           'category': category
                       })

               st.markdown("---")

               col1, col2 = st.columns([1, 1])

               with col1:
                   submit = st.form_submit_button(
                       f"✅ Add {len(items_to_add)} Items to Pantry",
                       use_container_width=True,
                       type="primary"
                   )

               with col2:
                   cancel = st.form_submit_button(
                       "❌ Cancel",
                       use_container_width=True
                   )

               if submit:
                   # Add all confirmed items
                   success_count = 0

                   for item in items_to_add:
                       success = add_item_to_pantry(
                           item_name=item['name'],
                           quantity=item['quantity'],
                           category=item['category']
                       )
                       if success:
                           success_count += 1

                   st.success(f"✅ Successfully added {success_count}/{len(items_to_add)} items!")

                   # Clear session state
                   del st.session_state['detected_items']
                   st.rerun()

               if cancel:
                   # Clear session state
                   del st.session_state['detected_items']
                   st.rerun()
   ```

3. Move manual entry to `tab2` (previously `tab1`)

**Testing:**
- Upload grocery photo
- Click "Detect Items"
- Should see detected items list
- Edit item names/quantities
- Uncheck items
- Click "Add Items"
- Verify items added to pantry

---

### Task 6.3: Add Sample Images for Testing
**Time:** 20 minutes

**Steps:**
1. Create test images directory:
   ```bash
   mkdir -p /root/Meal-planner-v2/test_images
   ```

2. Add documentation in `TASKS.md`:
   ```
   Test with:
   - Photo of grocery bags
   - Photo of receipt
   - Photo of pantry shelf
   - Photo of refrigerator
   ```

3. Test with various image types

**Testing:**
- Different image formats (JPG, PNG)
- Different lighting conditions
- Different item arrangements
- Verify accuracy > 80%

---

## GROUP 7: Shopping List Management
**Estimated Time:** 45 minutes
**Priority:** MEDIUM

### Task 7.1: Add "Add to Shopping List" Backend
**File:** `pages/generate_recipes.py`
**Time:** 20 minutes

**Steps:**
1. Find the "Add to Shopping List" button handler (line ~245)

2. Replace TODO with implementation:
   ```python
   with btn_col3:
       if st.button("🛒 Add to Shopping List", key=f"shop_{idx}"):
           needed = recipe.get('ingredients_needed', '')

           if needed and needed.strip():
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
                   st.error("❌ Failed to add to shopping list")
           else:
               st.info("No ingredients to add - you have everything!")
   ```

3. Add helper function:
   ```python
   def add_ingredients_to_shopping_list(recipe_name: str, ingredients: str) -> bool:
       """Add ingredients to shopping list file.

       Args:
           recipe_name: Name of recipe
           ingredients: Comma-separated list of ingredients

       Returns:
           True if successful
       """
       from lib.file_manager import get_data_file_path

       try:
           shopping_path = get_data_file_path("shopping_list")
           content = shopping_path.read_text(encoding="utf-8")

           # Build entry
           today = datetime.now().strftime("%Y-%m-%d")
           entry = f"\n## For: {recipe_name} (Added: {today})\n"

           for item in ingredients.split(','):
               item = item.strip()
               if item:
                   entry += f"- {item}\n"

           entry += "\n"

           # Append to file
           shopping_path.write_text(content + entry, encoding="utf-8")

           logger.info(
               "Added ingredients to shopping list",
               extra={"recipe_name": recipe_name}
           )

           return True

       except Exception as e:
           logger.error(
               "Failed to add to shopping list",
               extra={"error": str(e)},
               exc_info=True
           )
           return False
   ```

**Testing:**
- Generate recipes
- Click "Add to Shopping List"
- Check `data/pantry/shopping_list.md`
- Verify ingredients added correctly

---

### Task 7.2: Add Shopping List View to Pantry
**File:** `pages/pantry.py`
**Time:** 25 minutes

**Steps:**
1. Add Shopping List tab:
   ```python
   tab1, tab2, tab3, tab4, tab5 = st.tabs([
       "📸 Photo Upload",
       "➕ Add Items",
       "📦 View Pantry",
       "🛒 Shopping List",
       "🗑️ Manage Items"
   ])
   ```

2. Implement shopping list in `tab4`:
   ```python
   with tab4:
       st.markdown("### 🛒 Shopping List")

       try:
           content = load_data_file("shopping_list")

           # Parse shopping list
           lines = content.split('\n')
           items = []
           current_recipe = None

           for line in lines:
               line = line.strip()

               if line.startswith('##'):
                   current_recipe = line.replace('##', '').strip()
               elif line.startswith('-'):
                   item_text = line[1:].strip()
                   items.append({
                       'recipe': current_recipe or "General",
                       'item': item_text,
                       'checked': False
                   })

           if not items:
               st.info("📭 Shopping list is empty. Add ingredients from recipe suggestions!")
           else:
               st.markdown(f"**Total items: {len(items)}**")
               st.markdown("---")

               # Group by recipe
               from itertools import groupby

               for recipe, group in groupby(items, key=lambda x: x['recipe']):
                   st.markdown(f"#### {recipe}")

                   for item in group:
                       checked = st.checkbox(
                           item['item'],
                           key=f"shop_{item['recipe']}_{item['item']}"
                       )

                       if checked:
                           st.caption("✅ Purchased")

                   st.markdown("---")

               # Clear purchased button
               if st.button("🗑️ Clear All Items", use_container_width=True):
                   shopping_path = get_data_file_path("shopping_list")
                   # Reset to template
                   template = "# Shopping List\n\nGenerated: " + datetime.now().strftime("%Y-%m-%d") + "\n\n"
                   shopping_path.write_text(template, encoding="utf-8")
                   st.success("✅ Shopping list cleared!")
                   st.rerun()

       except Exception as e:
           st.error(f"❌ Error loading shopping list: {str(e)}")
   ```

**Testing:**
- View shopping list tab
- Should see items grouped by recipe
- Check items
- Clear list
- Verify file updated

---

## GROUP 8: Expiry Tracking
**Estimated Time:** 45 minutes
**Priority:** MEDIUM

### Task 8.1: Add Expiry Warnings to View Pantry
**File:** `pages/pantry.py`
**Time:** 20 minutes

**Steps:**
1. Modify the View Pantry tab item display loop:
   ```python
   # In the item display loop, add expiry warning
   from datetime import datetime, timedelta

   today = datetime.now().date()
   warning_threshold = today + timedelta(days=3)

   for item in items_to_display:
       with st.container():
           # Check for expiry
           show_warning = False
           days_until_expiry = None

           if item.get('expiry_date'):
               try:
                   expiry_date = datetime.strptime(
                       item['expiry_date'].replace('~', '').strip()[:10],
                       '%Y-%m-%d'
                   ).date()

                   days_until_expiry = (expiry_date - today).days

                   if today <= expiry_date <= warning_threshold:
                       show_warning = True
               except:
                   pass

           # Display item with warning
           col1, col2, col3 = st.columns([3, 2, 1])

           with col1:
               if show_warning:
                   st.markdown(f"⚠️ **{item['name']}**")
               else:
                   st.markdown(f"**{item['name']}**")

           with col2:
               st.markdown(f"*{item['quantity']}*")

           with col3:
               badge = "🥫" if item['category'] == "Pantry Staple" else "🥬"
               st.markdown(badge)

           # Show metadata with warning
           metadata = []
           if item.get('added_date'):
               metadata.append(f"Added: {item['added_date']}")
           if item.get('expiry_date'):
               if show_warning and days_until_expiry is not None:
                   if days_until_expiry == 0:
                       metadata.append(f"⚠️ **Expires TODAY**")
                   else:
                       metadata.append(f"⚠️ **Expires in {days_until_expiry} days**")
               else:
                   metadata.append(f"Expires: {item['expiry_date']}")
           if item.get('notes'):
               metadata.append(f"Notes: {item['notes']}")

           if metadata:
               if show_warning:
                   st.error(" • ".join(metadata))
               else:
                   st.caption(" • ".join(metadata))

           st.markdown("---")
   ```

**Testing:**
- Add fresh items with various expiry dates
- Items expiring today/tomorrow should show warning
- Warning color should be red/orange
- Past expiry items should show as expired

---

### Task 8.2: Add "Use Soon" Recipe Filter
**File:** `pages/generate_recipes.py`
**Time:** 25 minutes

**Steps:**
1. Add checkbox for "use expiring items":
   ```python
   # After meal type selection, add:
   use_expiring = st.checkbox(
       "🚨 Prioritize expiring ingredients",
       value=False,
       help="Suggest recipes that use items expiring in the next 3 days"
   )
   ```

2. Modify recipe generation call:
   ```python
   # Generate recipes
   recipes = generator.suggest_recipes(
       cuisines=selected_cuisines,
       meal_type=meal_type,
       num_suggestions=num_recipes,
       prioritize_expiring=use_expiring  # Add this parameter
   )
   ```

3. Update `RecipeGenerator.suggest_recipes()` in `lib/llm_agents.py`:
   ```python
   def suggest_recipes(
       self,
       cuisines: list[str],
       meal_type: str = "Dinner",
       num_suggestions: int = 4,
       prioritize_expiring: bool = False  # Add parameter
   ) -> list[dict]:
   ```

4. Update prompt generation to include expiring items:
   ```python
   # In the prompt building section, add:
   if prioritize_expiring:
       prompt += "\n\nIMPORTANT: Prioritize using fresh items that are expiring soon (within 3 days). Check the 'Expires' dates in the fresh items list."
   ```

**Testing:**
- Add items expiring soon
- Check "Prioritize expiring" checkbox
- Generate recipes
- Should suggest recipes using expiring items first

---

# PHASE 3: Polish & Optimization

**Total Estimated Time:** 2-3 hours
**Goal:** Better UX, performance, testing

---

## GROUP 9: UI/UX Improvements
**Estimated Time:** 60 minutes

### Task 9.1: Add Loading States
**Time:** 20 minutes

**Steps:**
- Replace all spinners with custom styling
- Add progress bars for long operations
- Add skeleton loaders for data fetching

### Task 9.2: Improve Error Messages
**Time:** 20 minutes

**Steps:**
- Audit all error messages
- Make user-friendly
- Add troubleshooting hints
- Add "Need help?" links

### Task 9.3: Mobile Responsive Design
**Time:** 20 minutes

**Steps:**
- Test on mobile browser
- Adjust column widths
- Make buttons full-width on mobile
- Test all interactions

---

## GROUP 10: Testing & Quality
**Estimated Time:** 60 minutes

### Task 10.1: Add Unit Tests
**Time:** 30 minutes

**Files to Test:**
- `lib/file_manager.py`
- `lib/llm_agents.py`
- Helper functions in pages

### Task 10.2: Run Code Quality Tools
**Time:** 30 minutes

**Steps:**
```bash
# Type checking
mypy lib/ --strict

# Linting
ruff check lib/ pages/ app.py

# Fix auto-fixable issues
ruff check --fix lib/ pages/ app.py
```

---

## Summary

**Total Tasks:** ~50 detailed tasks
**Total Estimated Time:** 6-8 hours across 3 phases
**Completion Criteria:** All tests passing, no navigation errors, complete user flows working

---

## Quick Reference

**Critical Path (MVP - Phase 1):**
1. Create pantry.py (GROUP 1)
2. Create meal_history.py (GROUP 2)
3. Add recipe feedback (GROUP 3)
4. Test end-to-end (GROUP 5)

**After MVP (Phase 2):**
5. Photo upload (GROUP 6)
6. Shopping list (GROUP 7)
7. Expiry tracking (GROUP 8)

**Polish (Phase 3):**
8. UI improvements (GROUP 9)
9. Testing & quality (GROUP 10)

---

**Last Updated:** 2025-11-27
**Status:** Ready for implementation
