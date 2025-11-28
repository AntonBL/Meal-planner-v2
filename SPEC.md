# AI Recipe Planner - Product Specification

## Overview
An AI-powered meal planning application that helps manage ingredients, discover recipes, and plan meals based on what's available in your pantry. Designed for a household of 2 users with an intuitive interface and intelligent automation.

**Built entirely in Python with Streamlit** for simplicity and rapid development.

---

## Core Concept
The system uses an LLM agent as the "brain" that:
- Maintains knowledge of your ingredients (pantry staples + fresh items)
- Learns your recipe preferences (loves/likes/dislikes)
- Suggests recipes based on available ingredients
- Updates inventory through manual input or photo recognition
- Adapts to your cuisine preferences and dietary needs

---

## Data Storage Architecture

### Folder-Based Text Files
All data stored in **human-readable markdown files** organized by folders. The LLM can naturally read and update these files.

```
data/
├── pantry/
│   ├── staples.md          # Long-lasting pantry items
│   ├── fresh.md            # Perishable items with expiry dates
│   └── shopping_list.md    # Items to buy
├── recipes/
│   ├── loved.md            # 5-star favorites
│   ├── liked.md            # 3-4 star recipes
│   └── not_again.md        # 1-2 star or disliked
├── preferences.md          # Cuisines, dietary restrictions, notes
└── meal_history.md         # Log of meals cooked
```

### Example Files

#### `data/pantry/staples.md`
```markdown
# Pantry Staples

Last updated: 2025-11-26

## Grains & Pasta
- White rice - 2 lbs - Added: 2025-11-15
- Brown rice - 1 lb - Added: 2025-11-10
- Spaghetti - 3 boxes - Added: 2025-11-20
- Penne pasta - 2 boxes - Added: 2025-11-18

## Oils & Condiments
- Olive oil - 1 bottle (half full) - Added: 2025-10-01
- Vegetable oil - 1 bottle - Added: 2025-09-15
- Soy sauce - 1 bottle - Added: 2025-09-10
- Balsamic vinegar - 1 bottle - Added: 2025-10-20

## Canned Goods
- Canned tomatoes (crushed) - 4 cans - Added: 2025-11-15
- Chicken broth - 3 cans - Added: 2025-11-15
- Black beans - 2 cans - Added: 2025-11-10

## Spices & Herbs (Dried)
- Garlic powder
- Onion powder
- Italian seasoning
- Cumin
- Paprika
- Black pepper
```

#### `data/pantry/fresh.md`
```markdown
# Fresh Items

Last updated: 2025-11-26

## Proteins
- Chicken breast - 4 pieces (1.5 lbs) - Added: 2025-11-24 - Use by: ~2025-11-28
- Ground beef - 1 lb - Added: 2025-11-25 - Use by: ~2025-11-27

## Dairy & Eggs
- Milk (2%) - 1 gallon - Added: 2025-11-25 - Expires: 2025-12-02
- Eggs - 10 remaining - Added: 2025-11-23 - Expires: 2025-12-15
- Cheddar cheese - 8 oz block - Added: 2025-11-24 - Expires: 2025-12-10
- Butter - 1 stick remaining - Added: 2025-11-20 - Expires: 2025-12-20

## Vegetables
- Onions (yellow) - 3 - Added: 2025-11-20
- Garlic - 1 bulb - Added: 2025-11-20
- Bell peppers (red, yellow) - 3 peppers - Added: 2025-11-24 - Use by: 2025-11-29
- Carrots - 1 lb bag - Added: 2025-11-24 - Use by: 2025-12-05
- Broccoli - 1 head - Added: 2025-11-25 - Use by: 2025-11-28

## Fruits
- Lemons - 3 - Added: 2025-11-23
- Limes - 2 - Added: 2025-11-25
```

#### `data/pantry/shopping_list.md`
```markdown
# Shopping List

Generated: 2025-11-26

## Need to Buy Soon
- Butter (running low - only 1 stick left)
- Ginger root (for stir fry recipes)
- Fresh basil

## For Next Shopping Trip
- Tortillas
- Salsa
- Avocados
- Bananas
```

#### `data/recipes/loved.md`
```markdown
# ⭐⭐⭐⭐⭐ Loved Recipes

Recipes we absolutely love and make regularly.

---

## Chicken Stir Fry
**Cuisine:** Asian
**Last made:** 2025-11-20
**Rating:** 5/5
**Times made:** 12

**Ingredients:**
- Chicken breast (1 lb)
- Soy sauce
- Rice
- Bell peppers
- Onion
- Garlic
- Ginger (fresh)
- Vegetable oil

**Notes:**
Add extra ginger! Wife loves when it's spicy. Takes about 25 minutes total. Great for weeknights. Use whatever vegetables we have on hand.

---

## Pasta Primavera
**Cuisine:** Italian
**Last made:** 2025-11-18
**Rating:** 5/5
**Times made:** 8

**Ingredients:**
- Pasta (any shape)
- Olive oil
- Garlic
- Mixed vegetables (bell peppers, broccoli, carrots)
- Parmesan cheese
- Fresh basil (if available)
- Salt & pepper

**Notes:**
Use fresh basil if available - makes a huge difference! Quick weeknight meal. Can add chicken for more protein. Wife's favorite light dinner.

---

## One-Pan Chicken and Rice
**Cuisine:** American
**Last made:** 2025-11-15
**Rating:** 5/5
**Times made:** 15

**Ingredients:**
- Chicken thighs or breasts
- White rice
- Chicken broth
- Onion
- Garlic
- Mixed vegetables
- Paprika, salt, pepper

**Notes:**
Easy cleanup! Everything cooks in one pan. Very forgiving recipe. Can prep ahead and refrigerate. Leftovers reheat perfectly.
```

#### `data/recipes/liked.md`
```markdown
# 👍 Liked Recipes

Good recipes we enjoy occasionally.

---

## Chicken Tacos
**Cuisine:** Mexican
**Last made:** 2025-11-15
**Rating:** 4/5
**Times made:** 5

**Ingredients:**
- Chicken breast
- Taco seasoning
- Tortillas
- Lettuce
- Cheese
- Salsa
- Sour cream
- Lime

**Notes:**
Good but not amazing. Maybe try different seasoning blend next time. Wife prefers soft tacos. Quick and easy weeknight option.

---

## Garlic Butter Shrimp Pasta
**Cuisine:** Italian
**Last made:** 2025-11-08
**Rating:** 4/5
**Times made:** 3

**Ingredients:**
- Shrimp (fresh or frozen)
- Pasta
- Butter
- Garlic
- Lemon
- Parsley
- Red pepper flakes

**Notes:**
Tasty but shrimp can be pricey. Save for special occasions. Very quick to make (15 min). Don't overcook the shrimp.
```

#### `data/recipes/not_again.md`
```markdown
# 👎 Not Again

Recipes we tried but didn't enjoy.

---

## Quinoa Salad
**Cuisine:** Mediterranean
**Tried:** 2025-11-10
**Rating:** 2/5

**Why we didn't like it:**
Texture was weird for both of us. Neither of us is a fan of quinoa apparently. Too much effort for something we didn't enjoy.

---

## Baked Cod with Lemon
**Cuisine:** American
**Tried:** 2025-10-28
**Rating:** 2/5

**Why we didn't like it:**
Fish was bland and dry even though we followed the recipe. Prefer other fish preparations. Might try pan-seared next time instead of baked.
```

#### `data/preferences.md`
```markdown
# Food Preferences & Settings

Last updated: 2025-11-26

---

## Cuisines We Love
- Italian (pasta, risotto, anything with garlic)
- Asian (Chinese, Japanese, Thai - all good!)
- American comfort food (casseroles, one-pan meals)

## Cuisines We Like
- Mexican (tacos, burritos, but not too spicy)
- Mediterranean (Greek salads, hummus)

## Cuisines - Neutral/Rarely
- Indian (we like it but don't cook it often)
- French (seems intimidating)
- Middle Eastern

---

## Dietary Restrictions & Allergies
- No allergies
- No dietary restrictions
- Wife dislikes cilantro (tastes like soap to her)
- Prefer chicken and fish over red meat
- Trying to eat more vegetables

---

## Cooking Preferences
- **Weeknight meals:** 30 minutes or less preferred
- **Weekend:** Can do more complex recipes (up to 1 hour)
- **Favorite style:** One-pan/one-pot meals (easy cleanup!)
- **Leftovers:** We love recipes that reheat well
- **Servings:** Usually cook for 2, sometimes make extra for leftovers

---

## Ingredient Notes
- Always keep garlic and onions in stock
- Buy fresh vegetables weekly
- Prefer fresh herbs over dried when budget allows
- Keep chicken breast as go-to protein
- Wife loves anything with lemon

---

## Shopping Habits
- Weekly grocery trips (usually Sundays)
- Budget: ~$100-150/week for 2 people
- Shop at: Trader Joe's and local grocery store
- Buy organic when on sale

---

## Meal Frequency Preferences
- Chicken: 2-3 times per week
- Fish/Seafood: Once per week
- Vegetarian: 1-2 times per week
- Red meat: Rarely (maybe once every 2 weeks)
```

#### `data/meal_history.md`
```markdown
# Meal History

Log of meals we've cooked.

---

## November 2025

### Monday, 2025-11-25
**Chicken Stir Fry** ⭐⭐⭐⭐⭐
- Rating: 5/5
- Notes: Perfect! Added extra veggies from the fridge (broccoli and carrots). Used brown rice for a change.
- Ingredients used: chicken breast (1 lb), bell peppers, broccoli, carrots, soy sauce, ginger, garlic, brown rice

### Sunday, 2025-11-24
**Pasta Carbonara** ⭐⭐⭐⭐
- Rating: 4/5
- Notes: Good but a bit heavy. Next time use less cream.
- Ingredients used: spaghetti, eggs, bacon, parmesan, heavy cream

### Friday, 2025-11-22
**Takeout - Thai food**
- Too tired to cook after long work week
- Ordered from Thai Basil restaurant

### Thursday, 2025-11-21
**One-Pan Chicken and Rice** ⭐⭐⭐⭐⭐
- Rating: 5/5
- Notes: Always reliable. Used chicken thighs this time - more flavorful!
- Ingredients used: chicken thighs, white rice, chicken broth, carrots, peas, onion, garlic

### Wednesday, 2025-11-20
**Grilled Cheese & Tomato Soup** ⭐⭐⭐⭐
- Rating: 4/5
- Notes: Simple comfort food. Used canned tomato soup (lazy night).
- Ingredients used: bread, cheddar cheese, butter, canned tomato soup

---

## October 2025

### Monday, 2025-10-28
**Baked Cod with Lemon** ⭐⭐
- Rating: 2/5
- Notes: Didn't love it. Fish was dry and bland. Won't make again.
- Moved to "not_again.md"

*(Earlier entries...)*
```

---

## Key Features

### 1. Recipe Generation
- **Input**: Select cuisine preferences with checkboxes
- **Process**: LLM reads all data files and analyzes:
  - Available ingredients (staples + fresh)
  - User preferences and dietary restrictions
  - Recent meal history (for variety)
  - Recipe ratings and notes
- **Output**: 3-5 recipe suggestions with:
  - Recipe name & description
  - Ingredients needed (✅ available vs. ⚠️ need to buy)
  - Difficulty & time estimate
  - Why this recipe was suggested
- **Actions**:
  - **"Cook This"**: Marks ingredients as used, prompts for rating after
  - **"Not Interested"**: LLM learns to avoid similar suggestions
  - **"Add to Shopping List"**: Adds missing ingredients

### 2. Pantry Management

#### Manual Entry
- Simple form: Item name, quantity, category (staples/fresh/shopping)
- Quick-add common items (milk, eggs, chicken, etc.)
- Bulk entry: Paste shopping list, LLM parses and adds

#### Photo Upload (Vision AI)
- Take/upload photo of:
  - Grocery bags
  - Receipt
  - Refrigerator/pantry contents
- Claude Vision API extracts items and quantities
- User confirms/edits before adding
- Automatically categorizes as staple vs. fresh
- Adds expiry estimates for fresh items

#### Smart Features
- **Expiry warnings**: "3 items expiring in 2 days"
- **Low stock alerts**: "Butter running low"
- **Shopping list generation**: Based on planned meals

### 3. Recipe Feedback System
After marking a meal as "cooked":
- ⭐ Star rating (1-5)
- 👍/👎 Quick feedback
- "Make again?" Yes/No
- Optional notes field
- LLM automatically:
  - Moves recipe to appropriate file (loved/liked/not_again)
  - Updates preferences.md if patterns detected
  - Learns ingredient preferences

### 4. Cooking Mode (Interactive Recipe Assistant)
When actively cooking a recipe:
- View the full recipe you're currently making
- Ask questions about the recipe in real-time
- Get AI assistance with:
  - Ingredient substitutions ("Can I use butter instead of oil?")
  - Technique clarification ("How do I know when it's done?")
  - Timing questions ("Can I prep this ahead?")
  - Troubleshooting ("My sauce is too thick, what should I do?")
- Chat history persists during cooking session
- Easy access to original recipe details
- One-click return to rate and save recipe

### 5. Meal Planning
- View upcoming meals
- Suggest meals for the week
- Generate shopping list for planned meals
- Track variety (avoid repetition)

---

## User Interface Design

### Platform: **Streamlit Web App**

**Why Streamlit:**
- Pure Python (no JavaScript needed)
- Built-in UI components
- Fast development
- Auto-reloads on file changes
- Works on desktop, tablet, mobile browsers
- Easy to deploy (Streamlit Cloud free tier)
- Perfect for 2-user household

### Core Pages

#### 1. Home Dashboard (`app.py`)
```python
import streamlit as st

st.title("🏠 AI Recipe Planner")

# Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Pantry Items", "47")
with col2:
    st.metric("Fresh Items", "12")
with col3:
    st.metric("Expiring Soon", "3", delta="⚠️")

# Main actions
if st.button("🎲 Generate Recipes", use_container_width=True):
    st.switch_page("pages/generate_recipes.py")

if st.button("📝 Pantry", use_container_width=True):
    st.switch_page("pages/pantry.py")

if st.button("📅 View Meal History", use_container_width=True):
    st.switch_page("pages/meal_history.py")
```

#### 2. Recipe Generator
```python
st.title("🎲 Recipe Generator")

st.subheader("What sounds good tonight?")

# Cuisine selection
cuisines = st.multiselect(
    "Select cuisines:",
    ["Italian", "Asian", "Mexican", "American", "Mediterranean", "Indian"],
    default=["Italian", "Asian"]
)

# Meal type
meal_type = st.radio(
    "Meal type:",
    ["Dinner", "Lunch", "Quick & Easy"],
    horizontal=True
)

if st.button("✨ Get Recipe Suggestions", type="primary"):
    with st.spinner("🤖 AI is thinking..."):
        # Call LLM agent
        recipes = generate_recipes(cuisines, meal_type)

    # Display suggestions
    for recipe in recipes:
        with st.expander(f"🍝 {recipe['name']} ({recipe['time']} min)"):
            st.write(recipe['description'])

            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Have: {', '.join(recipe['available'])}")
            with col2:
                if recipe['needed']:
                    st.warning(f"⚠️ Need: {', '.join(recipe['needed'])}")

            # Actions
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("👨‍🍳 Cook This", key=f"cook_{recipe['id']}"):
                    mark_as_cooking(recipe)
            with btn_col2:
                if st.button("❌ Pass", key=f"pass_{recipe['id']}"):
                    learn_dislike(recipe)
            with btn_col3:
                if st.button("🛒 Add to List", key=f"shop_{recipe['id']}"):
                    add_to_shopping_list(recipe['needed'])
```

#### 3. Pantry Update
```python
st.title("📝 Pantry")

tab1, tab2, tab3 = st.tabs(["📸 Photo Upload", "✏️ Manual Entry", "🗑️ Remove Items"])

with tab1:
    uploaded_file = st.file_uploader("Upload photo of groceries", type=['jpg', 'png'])
    if uploaded_file:
        st.image(uploaded_file)
        if st.button("🔍 Detect Items"):
            with st.spinner("Analyzing image..."):
                detected_items = vision_detect_items(uploaded_file)

            st.subheader("Detected items (confirm before adding):")
            for item in detected_items:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text_input("Item", value=item['name'], key=f"name_{item['id']}")
                with col2:
                    st.text_input("Quantity", value=item['quantity'], key=f"qty_{item['id']}")
                with col3:
                    st.checkbox("Add", value=True, key=f"add_{item['id']}")

            if st.button("✅ Confirm & Add to Pantry"):
                add_items_to_pantry(detected_items)
                st.success("Items added!")

with tab2:
    with st.form("manual_entry"):
        item_name = st.text_input("Item name")
        quantity = st.text_input("Quantity (e.g., '2 lbs', '1 bottle')")
        category = st.selectbox("Category", ["Pantry Staple", "Fresh Item"])

        if st.form_submit_button("Add Item"):
            add_item(item_name, quantity, category)
            st.success(f"Added {item_name}!")

with tab3:
    # Show current items with delete buttons
    items = load_pantry_items()
    for item in items:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"{item['name']} - {item['quantity']}")
        with col2:
            if st.button("🗑️", key=f"del_{item['id']}"):
                delete_item(item['id'])
```

---

## Technical Architecture

### Tech Stack (All Python!)

```
┌─────────────────────────────────────┐
│      Streamlit Web UI               │
│   (Python frontend framework)       │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     Application Logic (Python)      │
│  - Recipe agent                     │
│  - Pantry management                │
│  - Preference learning              │
└─────────────┬───────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌──▼──┐ ┌────▼─────┐
│ Claude│ │File │ │Image     │
│  API  │ │ I/O │ │Processing│
│       │ │(.md)│ │(Pillow)  │
└───────┘ └─────┘ └──────────┘
```

#### Core Dependencies
```
anthropic==0.40.0          # Claude API client
streamlit==1.41.0          # Web UI framework
pillow==11.0.0             # Image processing
python-dotenv==1.0.0       # Environment variables
```

#### Optional Dependencies
```
streamlit-authenticator    # Simple auth for 2 users
pandas                     # If we add analytics later
```

### Project Structure

```
meal-planner/
├── app.py                 # Main Streamlit app (home page)
├── requirements.txt       # Python dependencies
├── .env                   # API keys (not committed)
├── .gitignore
├── README.md
├── SPEC.md
│
├── pages/                 # Streamlit multi-page app
│   ├── generate_recipes.py
│   ├── cooking_mode.py    # Active recipe with Q&A chat
│   ├── pantry.py
│   ├── meal_history.py
│   └── preferences.py
│
├── lib/                   # Core application logic
│   ├── __init__.py
│   ├── llm_agents.py      # Claude API interactions
│   ├── file_manager.py    # Read/write markdown files
│   ├── vision.py          # Image processing with Claude
│   └── utils.py           # Helper functions
│
└── data/                  # All user data (text files)
    ├── pantry/
    │   ├── staples.md
    │   ├── fresh.md
    │   └── shopping_list.md
    ├── recipes/
    │   ├── loved.md
    │   ├── liked.md
    │   └── not_again.md
    ├── preferences.md
    └── meal_history.md
```

### LLM Agent Implementation

#### Recipe Suggestion Agent

```python
# lib/llm_agents.py
import anthropic
from pathlib import Path

def load_data_files():
    """Load all relevant data files for context."""
    data = {}
    data['staples'] = Path('data/pantry/staples.md').read_text()
    data['fresh'] = Path('data/pantry/fresh.md').read_text()
    data['loved_recipes'] = Path('data/recipes/loved.md').read_text()
    data['liked_recipes'] = Path('data/recipes/liked.md').read_text()
    data['preferences'] = Path('data/preferences.md').read_text()
    data['meal_history'] = Path('data/meal_history.md').read_text()
    return data

def generate_recipe_suggestions(cuisines, meal_type="Dinner"):
    """Generate recipe suggestions using Claude."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    data = load_data_files()

    prompt = f"""You are a helpful meal planning assistant. Based on the available ingredients and user preferences below, suggest 3-4 recipes.

AVAILABLE PANTRY STAPLES:
{data['staples']}

AVAILABLE FRESH ITEMS:
{data['fresh']}

USER PREFERENCES:
{data['preferences']}

FAVORITE RECIPES:
{data['loved_recipes']}

RECENT MEALS (for variety):
{data['meal_history']}

REQUEST:
- Cuisines: {', '.join(cuisines)}
- Meal type: {meal_type}

INSTRUCTIONS:
1. Suggest 3-4 recipes that:
   - Use mostly available ingredients (minimize shopping needs)
   - Match the requested cuisines
   - Avoid recently cooked meals (check meal history)
   - Respect preferences (avoid cilantro, etc.)
   - Appropriate for {meal_type}

2. For each recipe:
   - Name and brief description
   - List ingredients in two groups: AVAILABLE (already have) and NEEDED (must buy)
   - Estimated time in minutes
   - Difficulty (easy/medium/hard)
   - Why you're suggesting it

3. Format your response as a structured list, one recipe per section.
"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_recipe_response(message.content[0].text)

def parse_recipe_response(response_text):
    """Parse LLM response into structured recipe objects."""
    # Parse the natural language response into structured data
    # This is flexible - LLM can use any format, we parse it
    recipes = []
    # ... parsing logic ...
    return recipes
```

#### Vision Agent (Photo Upload)

```python
# lib/vision.py
import anthropic
import base64

def detect_items_from_image(image_file):
    """Use Claude Vision to detect grocery items."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Read and encode image
    image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

    prompt = """Analyze this image and list all food/grocery items you can see.

For each item, provide:
1. Item name
2. Estimated quantity (if visible)
3. Category (pantry staple or fresh item)

Format as a simple list. Be specific but practical (e.g., "red bell peppers" not just "vegetables").
"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ],
        }]
    )

    return parse_vision_response(message.content[0].text)
```

#### Pantry Update Agent

```python
# lib/file_manager.py
from pathlib import Path
from datetime import datetime

def add_item_to_pantry(item_name, quantity, category="staple"):
    """Add item to appropriate pantry file."""

    file_path = "data/pantry/staples.md" if category == "staple" else "data/pantry/fresh.md"

    # Read current file
    content = Path(file_path).read_text()

    # Add new item with timestamp
    today = datetime.now().strftime("%Y-%m-%d")
    new_line = f"- {item_name} - {quantity} - Added: {today}\n"

    # Append to appropriate section (could use LLM to determine section)
    # For now, append to end of first section
    lines = content.split('\n')
    insert_index = find_first_section_end(lines)
    lines.insert(insert_index, new_line)

    # Write back
    Path(file_path).write_text('\n'.join(lines))

def update_pantry_with_llm(items_used, recipe_name):
    """Use LLM to intelligently update pantry after cooking."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    staples = Path('data/pantry/staples.md').read_text()
    fresh = Path('data/pantry/fresh.md').read_text()

    prompt = f"""We just cooked: {recipe_name}

Ingredients used: {', '.join(items_used)}

CURRENT PANTRY STAPLES:
{staples}

CURRENT FRESH ITEMS:
{fresh}

Please update these files by:
1. Removing or reducing quantities of used items
2. If an item is depleted, remove it entirely
3. If partially used, reduce quantity reasonably

Provide the COMPLETE updated content for both files.

FORMAT:
=== STAPLES.MD ===
[full updated content]

=== FRESH.MD ===
[full updated content]
"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse response and write updated files
    updated_staples, updated_fresh = parse_update_response(message.content[0].text)
    Path('data/pantry/staples.md').write_text(updated_staples)
    Path('data/pantry/fresh.md').write_text(updated_fresh)
```

### Deployment

#### Option 1: Streamlit Cloud (Recommended)
- Free hosting for public or private apps
- Direct GitHub integration
- Automatic deployments on push
- Easy environment variable management
- Perfect for 2-user household

**Steps:**
1. Push code to GitHub (private repo)
2. Connect Streamlit Cloud to repo
3. Add `ANTHROPIC_API_KEY` in secrets
4. Deploy!

#### Option 2: Local/Self-Hosted
```bash
# Run locally
streamlit run app.py

# Or run on home server/Raspberry Pi
# Access via local network
streamlit run app.py --server.address=0.0.0.0
```

### Security

**Simple 2-User Setup:**

```python
# app.py
import streamlit as st
import streamlit_authenticator as stauth

# Hash passwords (do this once, store hashed version)
credentials = {
    "usernames": {
        "user1": {
            "name": "User 1",
            "password": "hashed_password_1"  # Use bcrypt
        },
        "user2": {
            "name": "User 2",
            "password": "hashed_password_2"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "meal_planner",
    "secret_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f"Welcome {name}")
    # Main app here
elif authentication_status == False:
    st.error("Username/password incorrect")
```

**API Key Security:**
- Store in `.env` file (not committed)
- Use Streamlit secrets for deployment
- Never hardcode in source

---

## Development Phases

### Phase 1: MVP (Week 1)
- [x] Create folder structure and sample data files
- [ ] Basic Streamlit app with navigation
- [ ] Recipe generation page (LLM integration)
- [ ] Manual pantry entry
- [ ] Display pantry contents

### Phase 2: Core Features (Week 2)
- [ ] Photo upload for pantry (Vision API)
- [ ] Recipe feedback system
- [ ] Meal history logging
- [ ] Smart pantry updates (LLM removes used items)

### Phase 3: Enhancements (Week 3)
- [ ] Shopping list management
- [ ] Expiry tracking and alerts
- [ ] Preference learning
- [ ] Better UI/UX polish

### Phase 4: Polish (Week 4+)
- [ ] Authentication (2 users)
- [ ] Deploy to Streamlit Cloud
- [ ] Error handling
- [ ] Mobile-responsive design
- [ ] User testing and refinement

---

## Sample User Flows

### Flow 1: Generate a Recipe
1. User opens app → sees dashboard
2. Clicks "Generate Recipes"
3. Selects cuisines: Italian ✓, Asian ✓
4. Clicks "Get Suggestions"
5. LLM reads all data files (pantry, preferences, history)
6. Shows 4 recipe options with ✅ available / ⚠️ needed ingredients
7. User clicks "Cook This" on Pasta Primavera
8. System prompts: "Mark ingredients as used?" → Yes
9. LLM updates pantry files, adds to meal_history.md
10. After cooking, app asks for rating
11. User gives 5 stars + notes → moved to loved.md

### Flow 2: Pantry with Photo
1. User clicks "Pantry" → Photo Upload tab
2. Takes picture of grocery bags
3. Clicks "Detect Items"
4. Vision AI processes → shows detected items
5. User reviews list:
   - ✓ Milk - 1 gallon
   - ✓ Chicken breast - 2 lbs
   - ✓ Bell peppers - 3
   - ✗ (unchecks incorrectly detected item)
6. Edits quantity on one item
7. Clicks "Confirm & Add to Pantry"
8. Items appended to fresh.md with today's date

### Flow 3: Cooking with AI Assistant
1. User generates recipe suggestions
2. Clicks "👨‍🍳 Cook This" on Pasta Primavera
3. Enters Cooking Mode - sees full recipe displayed
4. While cooking, has questions:
   - Types: "Can I use vegetable oil instead of olive oil?"
   - AI responds: "Yes! Vegetable oil works fine for this recipe..."
   - Types: "How do I know when the pasta is al dente?"
   - AI explains with recipe context
5. Continues cooking with AI assistance available
6. When done, clicks "✅ Finished Cooking"
7. Rates recipe and adds notes
8. Recipe saved to appropriate file (loved/liked/not_again)

### Flow 4: Weekly Meal Planning
1. User wants to plan the week
2. Clicks "Generate Recipes" multiple times with different cuisine preferences
3. For each liked recipe, clicks "Add to Shopping List"
4. LLM aggregates all needed ingredients
5. User views shopping_list.md
6. Goes grocery shopping with the list
7. After shopping, uploads photo of groceries
8. Pantry automatically updated

---

## Success Metrics

- **Ease of use**: Can generate recipes in < 30 seconds
- **Accuracy**: Photo detection > 80% accurate
- **Waste reduction**: Track items expiring unused
- **Satisfaction**: Average recipe rating
- **Time saved**: Less time planning meals

---

## Future Enhancements

- Voice input: "Add milk to shopping list"
- Barcode scanning
- Nutrition tracking
- Budget tracking
- Recipe scaling (2 servings → 4 servings)
- Meal prep suggestions
- Leftover management
- Integration with grocery delivery APIs

---

## Open Questions

1. **Preferred cuisines**: What are your top 5 favorite cuisines?
2. **Dietary restrictions**: Any allergies or dietary preferences?
3. **Meal frequency**: How many times per week do you cook at home?
4. **Shopping habits**: Weekly grocery trips or as-needed?
5. **Current pain points**: What's most frustrating about meal planning now?
6. **Device usage**: Primarily phone, tablet, or desktop?
7. **Recipe sources**: Do you have existing recipes to import?
8. **Current tools**: Using any apps/tools for meal planning now?

---

## Next Steps

1. ✅ Create folder structure with sample data
2. Set up Python environment
3. Install dependencies (streamlit, anthropic)
4. Build basic Streamlit app
5. Test Claude API integration
6. Get user feedback and iterate!

**Estimated Timeline:** 2-3 weeks to working MVP
**Recommended Approach:** Start simple, iterate based on real usage
