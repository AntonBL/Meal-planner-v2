# START HERE - Engineering Onboarding Guide
## Phase 1: GROUP 1 & GROUP 2 Implementation

**For:** Next engineer implementing Update Pantry and Meal History pages
**Time Required:** 1.5-2 hours
**Difficulty:** Beginner-Intermediate
**Last Updated:** 2025-11-27

---

## 🎯 Your Mission

You're going to fix the two critical navigation errors in the app by creating:
1. **Update Pantry Page** (`pages/update_pantry.py`) - 45 minutes
2. **Meal History Page** (`pages/meal_history.py`) - 30 minutes

After you're done:
- ✅ All navigation will work without errors
- ✅ Users can add items to their pantry
- ✅ Users can view their cooking history
- ✅ Foundation is set for Phase 2 features

---

## 📍 Current State

### What's Working
- ✅ Server deployed on Akamai Cloud (Ubuntu)
- ✅ HTTPS with password authentication
- ✅ Claude Haiku 4.5 API configured
- ✅ Home dashboard displays correctly
- ✅ Recipe generation page works (generates recipes via AI)
- ✅ All data files exist in `data/` directory

### What's Broken (Your Job)
- ❌ Clicking "Update Pantry" from home → 404 error (file doesn't exist)
- ❌ Clicking "Meal History" from home → 404 error (file doesn't exist)
- ❌ Sidebar navigation to these pages fails

### Current Error Messages
If you access the app now, clicking these buttons shows:
```
Could not find page: `pages/update_pantry.py`.
Must be the file path relative to the main script...
```

**Your job:** Create these missing files with full functionality.

---

## 🔐 Prerequisites

### 1. Access to Server
```bash
# SSH into the server
ssh root@50.116.63.56

# You should land in /root
# Navigate to project directory
cd /root/Meal-planner-v2

# Confirm you're in the right place
pwd
# Should output: /root/Meal-planner-v2
```

### 2. Verify App is Running
```bash
# Check Streamlit service status
supervisorctl status meal-planner

# Should show:
# meal-planner    RUNNING   pid XXXXX, uptime X:XX:XX
```

If not running:
```bash
supervisorctl start meal-planner
```

### 3. Check Current File Structure
```bash
# List existing pages
ls -la pages/

# Should show:
# generate_recipes.py  <- exists
# __init__.py         <- exists
# (update_pantry.py and meal_history.py are MISSING - you'll create them)
```

### 4. Access the App in Browser
- URL: `https://50.116.63.56`
- Username: `roger`
- Password: (you should have this)
- Accept self-signed SSL certificate warning

You should see the home dashboard with buttons for:
- 🎲 Generate Recipes (works)
- 📝 Update Pantry (broken - your job to fix)
- 📅 Meal History (broken - your job to fix)

---

## 🚀 GROUP 1: Create Update Pantry Page

**Time:** 45 minutes
**File:** `pages/update_pantry.py`

---

### STEP 1: Create the File (5 minutes)

```bash
# Make sure you're in the project directory
cd /root/Meal-planner-v2

# Create the new file
nano pages/update_pantry.py
```

**Paste this complete starter code:**

```python
"""Update Pantry Page for AI Recipe Planner.

Allows users to manually add, view, edit, and remove pantry items.
Supports both pantry staples and fresh items with expiry tracking.
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

from lib.file_manager import load_data_file, get_data_file_path
from lib.exceptions import DataFileNotFoundError
from lib.logging_config import get_logger, setup_logging

# Set up logging
setup_logging("INFO")
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Update Pantry - AI Recipe Planner",
    page_icon="📝",
    layout="wide",
)

# Title
st.title("📝 Update Pantry")
st.markdown("*Manage your pantry staples and fresh items*")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def parse_pantry_items(content: str, category: str) -> list[dict]:
    """Parse pantry markdown content into structured items.

    Args:
        content: Markdown file content
        category: "Pantry Staple" or "Fresh Item"

    Returns:
        List of item dictionaries
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


# ============================================================================
# MAIN PAGE LAYOUT
# ============================================================================

# Create tabs
tab1, tab2, tab3 = st.tabs(["➕ Add Items", "📦 View Pantry", "🗑️ Manage Items"])

# ----------------------------------------------------------------------------
# TAB 1: ADD ITEMS
# ----------------------------------------------------------------------------
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

        if submitted:
            # Validate inputs
            if not item_name or not item_name.strip():
                st.error("⚠️ Please enter an item name")
            elif not quantity or not quantity.strip():
                st.error("⚠️ Please enter a quantity")
            else:
                # Add item to pantry
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

# ----------------------------------------------------------------------------
# TAB 2: VIEW PANTRY
# ----------------------------------------------------------------------------
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

            # Display items
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

                    # Display item
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

                    # Show metadata
                    metadata = []
                    if item.get('added_date'):
                        metadata.append(f"Added: {item['added_date']}")
                    if item.get('expiry_date'):
                        if show_warning and days_until_expiry is not None:
                            if days_until_expiry == 0:
                                metadata.append(f"⚠️ **Expires TODAY**")
                            elif days_until_expiry < 0:
                                metadata.append(f"❌ **EXPIRED {abs(days_until_expiry)} days ago**")
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

    except DataFileNotFoundError as e:
        st.error(f"❌ Could not load pantry data: {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logger.error("Error displaying pantry", exc_info=True)

# ----------------------------------------------------------------------------
# TAB 3: MANAGE ITEMS (Placeholder for now)
# ----------------------------------------------------------------------------
with tab3:
    st.markdown("### 🗑️ Manage Items")
    st.info("📝 Item management coming soon! For now, edit items directly in the data files.")

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter`

---

### STEP 2: Test Update Pantry Page (10 minutes)

```bash
# Restart the application to pick up the new file
supervisorctl restart meal-planner

# Check logs for errors
tail -20 /var/log/meal-planner.err.log

# If you see errors, check for syntax issues
# If no errors, continue to browser testing
```

**In Browser:**
1. Go to `https://50.116.63.56`
2. Click "Update Pantry" button
3. **Expected:** Page loads without error
4. **You should see:** Three tabs (Add Items, View Pantry, Manage Items)

**Test Adding an Item:**
1. Select "Pantry Staple"
2. Enter "Olive Oil" as item name
3. Enter "1 bottle" as quantity
4. Click "Add Item"
5. **Expected:** Success message appears
6. Switch to "View Pantry" tab
7. **Expected:** "Olive Oil" appears in the list

**Test Adding a Fresh Item:**
1. Go back to "Add Items" tab
2. Select "Fresh Item"
3. Enter "Milk" as item name
4. Enter "1 gallon" as quantity
5. Select tomorrow's date for expiry
6. Click "Add Item"
7. **Expected:** Success message
8. View Pantry tab should show "Milk" with expiry warning

**Verify Data Files Updated:**
```bash
# Check staples file
cat data/pantry/staples.md | grep "Olive Oil"
# Should show: - Olive Oil - 1 bottle - Added: 2025-11-27

# Check fresh file
cat data/pantry/fresh.md | grep "Milk"
# Should show: - Milk - 1 gallon - Added: 2025-11-27 - Expires: [tomorrow's date]
```

---

### STEP 3: Troubleshooting (if needed)

**Problem: Page not found error still appears**
```bash
# Check file was created
ls -la pages/update_pantry.py

# Should show file exists
# If not, you may be in wrong directory

# Restart app again
supervisorctl restart meal-planner

# Check for Python syntax errors in logs
tail -50 /var/log/meal-planner.err.log | grep -i error
```

**Problem: Import errors**
```bash
# Verify lib modules exist
ls -la lib/

# Should show:
# file_manager.py
# exceptions.py
# logging_config.py
# llm_agents.py

# If missing, something is wrong with project structure
```

**Problem: Items not saving**
```bash
# Check file permissions
ls -la data/pantry/

# Should show files owned by root with write permissions
# If not, fix permissions:
chmod 644 data/pantry/*.md
```

**Problem: TypeError about date**
- Make sure you're using `date` not `datetime` for expiry_date
- Check imports at top of file include `from datetime import date`

---

## 🚀 GROUP 2: Create Meal History Page

**Time:** 30 minutes
**File:** `pages/meal_history.py`

---

### STEP 1: Create the File (5 minutes)

```bash
# Create the new file
nano pages/meal_history.py
```

**Paste this complete starter code:**

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

# Page configuration
st.set_page_config(
    page_title="Meal History - AI Recipe Planner",
    page_icon="📅",
    layout="wide",
)

st.title("📅 Meal History")
st.markdown("*Your cooking journal and recipe ratings*")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
                    try:
                        current_meal['rating'] = int(rating_str.split('/')[0])
                    except:
                        pass

        # Notes line
        elif line.startswith('- Notes:'):
            if current_meal:
                current_meal['notes'] = line.replace('- Notes:', '').strip()

        # Ingredients line
        elif line.startswith('- Ingredients used:'):
            if current_meal:
                current_meal['ingredients'] = line.replace('- Ingredients used:', '').strip()

    # Don't forget last meal
    if current_meal and current_meal['name']:
        meals.append(current_meal)

    return meals


# ============================================================================
# MAIN PAGE LAYOUT
# ============================================================================

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
            ratings = [m['rating'] for m in meals if m['rating'] > 0]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                st.metric("⭐ Average Rating", f"{avg_rating:.1f}/5")
            else:
                st.metric("⭐ Average Rating", "N/A")

        with col3:
            five_star = sum(1 for m in meals if m['rating'] == 5)
            st.metric("🌟 5-Star Meals", five_star)

        st.markdown("---")

        # Filter options
        col1, col2 = st.columns([2, 1])

        with col1:
            search = st.text_input(
                "🔍 Search meals",
                placeholder="Search by name or ingredients...",
                key="search_meals"
            )

        with col2:
            min_rating = st.selectbox(
                "Filter by rating",
                ["All", "5 stars", "4+ stars", "3+ stars"]
            )

        # Filter meals
        filtered_meals = meals

        if search:
            search_lower = search.lower()
            filtered_meals = [
                m for m in filtered_meals
                if (search_lower in (m['name'] or '').lower()
                    or search_lower in (m['ingredients'] or '').lower())
            ]

        if min_rating != "All":
            rating_map = {"5 stars": 5, "4+ stars": 4, "3+ stars": 3}
            min_val = rating_map[min_rating]
            filtered_meals = [m for m in filtered_meals if m['rating'] >= min_val]

        st.markdown(f"### Showing {len(filtered_meals)} of {len(meals)} meals")

        # Display meals
        for meal in filtered_meals:
            with st.expander(
                f"**{meal['date']}** - {meal['name']} {meal['stars']}",
                expanded=False
            ):
                if meal['rating']:
                    st.markdown(f"**Rating:** {meal['rating']}/5 {meal['stars']}")

                if meal['notes']:
                    st.markdown(f"**Notes:** {meal['notes']}")

                if meal['ingredients']:
                    st.markdown("**Ingredients used:**")
                    st.caption(meal['ingredients'])

except DataFileNotFoundError:
    st.warning("⚠️ Meal history file not found. It will be created when you log your first meal.")
    logger.warning("Meal history file not found")

except Exception as e:
    st.error(f"❌ Error loading meal history: {str(e)}")
    logger.error("Error loading meal history", exc_info=True)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("app.py")
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

---

### STEP 2: Test Meal History Page (10 minutes)

```bash
# Restart application
supervisorctl restart meal-planner

# Check for errors
tail -20 /var/log/meal-planner.err.log
```

**In Browser:**
1. Go to home page
2. Click "Meal History" button
3. **Expected:** Page loads without error
4. **You should see:** Stats and meal list (or empty state if no meals yet)

**Test with Existing Data:**
```bash
# Check if meal history has data
cat data/meal_history.md | head -50
```

If you see meal entries, they should display on the page.

**Test Search:**
1. If meals exist, try searching for a meal name
2. Filter by rating should work
3. Expandable sections should show details

**Test Empty State:**
If no meals exist yet, you should see:
```
📭 No meals logged yet. Cook a recipe and rate it to start your history!
```

---

### STEP 3: Final Verification (5 minutes)

**Complete Navigation Test:**
1. Start at home page (`https://50.116.63.56`)
2. Click "Update Pantry" → should work ✅
3. Click "Back to Home" → should return to home ✅
4. Click "Meal History" → should work ✅
5. Click "Back to Home" → should return to home ✅
6. Click "Generate Recipes" → should work ✅
7. Use sidebar navigation → all links should work ✅

**Check Logs for Errors:**
```bash
# Should see INFO level messages, not ERRORS
tail -50 /var/log/meal-planner.out.log

# Check error log is clean
tail -50 /var/log/meal-planner.err.log
```

**Verify Files Created:**
```bash
# List pages directory
ls -la pages/

# Should now show:
# - generate_recipes.py
# - meal_history.py      <- NEW!
# - update_pantry.py     <- NEW!
# - __init__.py
```

---

## ✅ Success Criteria

You're done with GROUP 1 & 2 when ALL of these are true:

- [ ] File `pages/update_pantry.py` exists and has ~350+ lines
- [ ] File `pages/meal_history.py` exists and has ~200+ lines
- [ ] No errors when clicking "Update Pantry" from home
- [ ] No errors when clicking "Meal History" from home
- [ ] Can add a pantry staple successfully
- [ ] Can add a fresh item with expiry date
- [ ] Added items appear in "View Pantry" tab
- [ ] Items are saved to data files (`staples.md` or `fresh.md`)
- [ ] Meal history shows existing meals (or empty state if none)
- [ ] Search and filter work on meal history page
- [ ] "Back to Home" buttons work on both pages
- [ ] No errors in `/var/log/meal-planner.err.log`
- [ ] All navigation (home → pages → home) works smoothly

---

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'lib'"

**Solution:**
```bash
# Make sure you're running from the project root
cd /root/Meal-planner-v2

# Check lib directory exists
ls -la lib/

# Restart app
supervisorctl restart meal-planner
```

---

### Issue: "File not found" when loading data

**Solution:**
```bash
# Check data files exist
ls -la data/pantry/
ls -la data/recipes/

# Verify files have content
cat data/pantry/staples.md | head -20
cat data/meal_history.md | head -20

# If files are missing or empty, check git
git status
```

---

### Issue: Items added but not appearing in View Pantry

**Solution:**
1. Check if file was actually updated:
   ```bash
   tail -10 data/pantry/staples.md
   ```

2. Check for parsing errors in logs:
   ```bash
   grep -i "error" /var/log/meal-planner.err.log | tail -20
   ```

3. Verify the `parse_pantry_items()` function is working:
   - Items must start with `-`
   - Must have at least 2 parts: `Name - Quantity`

---

### Issue: Expiry dates not showing warnings

**Solution:**
1. Make sure you entered a date within 3 days
2. Check date format in file:
   ```bash
   grep "Expires:" data/pantry/fresh.md
   ```
3. Should be: `Expires: YYYY-MM-DD`

---

### Issue: Page crashes when accessing

**Check Python syntax errors:**
```bash
# Try to import the page manually
cd /root/Meal-planner-v2
source venv/bin/activate
python3 -c "import pages.update_pantry"

# Should have no output if successful
# If error, it will show the syntax issue
```

---

## 📚 Next Steps After GROUP 1 & 2

Once you've successfully completed these tasks:

1. **Test the complete flow:**
   - Add items to pantry
   - Generate recipes (should use your pantry items)
   - View meal history

2. **Review TASKS.md:**
   - Look at GROUP 3: Recipe Feedback System
   - This is the next priority

3. **Git Commit (Optional but Recommended):**
   ```bash
   cd /root/Meal-planner-v2
   git add pages/update_pantry.py pages/meal_history.py
   git commit -m "Add Update Pantry and Meal History pages

   - Created pages/update_pantry.py with add items and view pantry functionality
   - Created pages/meal_history.py with meal viewing and filtering
   - Fixed navigation errors from home dashboard
   - All core navigation now working

   Closes navigation issues for MVP Phase 1"
   ```

4. **Update Progress:**
   - Mark GROUP 1 and GROUP 2 as complete in PLAN.md
   - Update TASKS.md with completion dates

---

## 🆘 Getting Help

### Check Documentation
- **PLAN.md** - High-level overview and phases
- **TASKS.md** - Detailed task breakdown for all groups
- **SPEC.md** - Product specification
- **README.md** - Project overview

### Check Logs
```bash
# Application logs
tail -100 /var/log/meal-planner.out.log

# Error logs
tail -100 /var/log/meal-planner.err.log

# Nginx logs (if web server issues)
tail -100 /var/log/nginx/error.log
```

### Verify System Health
```bash
# Check all services
supervisorctl status
systemctl status nginx

# Check disk space
df -h

# Check memory
free -h
```

### Test from Command Line
```bash
# Activate virtual environment
cd /root/Meal-planner-v2
source venv/bin/activate

# Test imports
python3 -c "from lib.file_manager import load_data_file; print(load_data_file('staples')[:100])"

# Should print first 100 chars of staples.md
```

---

## 📝 Handoff Checklist

Before you consider this complete and hand off to the next engineer:

- [ ] Both files created and working
- [ ] All navigation works
- [ ] Forms submit successfully
- [ ] Data persists to files
- [ ] No errors in logs
- [ ] Tested on multiple browsers (if possible)
- [ ] Code follows existing patterns
- [ ] Functions have docstrings
- [ ] Error handling in place
- [ ] Logging statements added
- [ ] Git commit created (optional)
- [ ] PLAN.md updated with progress (optional)

---

## 🎯 Time Breakdown Estimate

If you follow this guide linearly:

| Task | Time |
|------|------|
| Prerequisites & Setup | 10 min |
| Create Update Pantry File | 5 min |
| Test Update Pantry | 10 min |
| Troubleshoot (if needed) | 10-20 min |
| Create Meal History File | 5 min |
| Test Meal History | 10 min |
| Final Verification | 5 min |
| **TOTAL** | **55-75 min** |

**Expected completion:** 1-1.5 hours for an experienced developer

---

---

## 🔧 Code Flexibility & Design Principles

**IMPORTANT:** This code is designed to be flexible for changing customer requirements.

### Design Patterns Used

**1. Separation of Concerns**
```
- Helper functions at top (add_item_to_pantry, parse_pantry_items)
- Main page layout separate from business logic
- Easy to modify UI without touching data logic
```

**2. Configuration Over Hardcoding**
```python
# GOOD - Easy to change
category_options = ["Pantry Staple", "Fresh Item"]
category = st.radio("Item Category:", category_options)

# BAD - Hardcoded
# category = st.radio("Item Category:", ["Pantry Staple", "Fresh Item"])
```

**3. Reusable Functions**
```python
# parse_pantry_items() works for both staples and fresh
# add_item_to_pantry() handles both categories
# Just pass different parameters, no code duplication
```

### Making Changes Easy

**If customer wants to add a new item category:**
```python
# 1. Update the category options
category_options = ["Pantry Staple", "Fresh Item", "Frozen Item"]  # Add new

# 2. Add new file mapping in lib/file_manager.py
file_map = {
    "staples": "data/pantry/staples.md",
    "fresh": "data/pantry/fresh.md",
    "frozen": "data/pantry/frozen.md",  # Add new
}

# 3. Create new data file
# data/pantry/frozen.md

# That's it! The rest of the code adapts automatically
```

**If customer wants additional fields:**
```python
# Current: Name, Quantity, Expiry Date, Notes
# Add: Brand, Store Location

# Just extend the form:
with col2:
    brand = st.text_input("Brand (Optional)")
    location = st.text_input("Storage Location (Optional)")

# Update add_item_to_pantry() to include new fields:
if brand:
    new_line += f" - Brand: {brand}"
if location:
    new_line += f" - Location: {location}"

# Update parse_pantry_items() to extract new fields:
elif part.startswith('Brand:'):
    item['brand'] = part.replace('Brand:', '').strip()
elif part.startswith('Location:'):
    item['location'] = part.replace('Location:', '').strip()
```

**If customer wants different date format:**
```python
# All dates are in one place
today = datetime.now().strftime("%Y-%m-%d")  # Change format here

# For expiry dates:
expiry_date.strftime('%Y-%m-%d')  # Change format here
```

### What Makes This Flexible

✅ **Data in Markdown Files** - Customer can manually edit anytime
✅ **Helper Functions** - Easy to extend without breaking UI
✅ **Streamlit Forms** - Easy to add/remove fields
✅ **Parse Functions** - Handle missing fields gracefully
✅ **Type Hints** - Clear what each function expects
✅ **Docstrings** - New developers understand intent quickly
✅ **Error Handling** - Fails gracefully when data changes
✅ **Logging** - Easy to debug when requirements change

### Future-Proofing Checklist

When adding new features:
- [ ] Will this work if we add more categories?
- [ ] Will this work if we add more fields?
- [ ] Will this work if data format changes slightly?
- [ ] Is configuration separate from logic?
- [ ] Can customer request changes without code rewrite?
- [ ] Are functions reusable for similar features?

### Example: Easy Changes

**Customer says:** "I want to track whether items are organic"

**Solution (5 minutes):**
1. Add checkbox to form:
   ```python
   organic = st.checkbox("Organic")
   ```

2. Save to file:
   ```python
   if organic:
       new_line += " - Organic: Yes"
   ```

3. Parse and display:
   ```python
   elif part.startswith('Organic:'):
       item['organic'] = part.replace('Organic:', '').strip() == "Yes"

   # In display:
   if item.get('organic'):
       st.markdown("🌱 Organic")
   ```

Done! No architecture changes needed.

---

**Good luck! You've got this! 🚀**

**Questions? Check TASKS.md for even more detailed steps.**
