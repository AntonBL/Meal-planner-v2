# AI Recipe Planner - Product Roadmap

**Last Updated:** November 28, 2025
**Current Version:** 1.1.0 (Post-Integration Release)

---

## Table of Contents
1. [Version History](#version-history)
2. [Version 2.0 - Next Release](#version-20---next-release)
3. [Version 2.5 - Enhanced Intelligence](#version-25---enhanced-intelligence)
4. [Version 3.0 - Social & Scaling](#version-30---social--scaling)
5. [Future Ideas Backlog](#future-ideas-backlog)
6. [Technical Debt & Improvements](#technical-debt--improvements)

---

## Version History

### Version 1.1.0 - Integration Release (November 2025) ✅
**Theme:** Seamless Workflow Integration

**Major Features:**
- ✅ Bidirectional shopping list sync with weekly planner
- ✅ Smart pantry updates after cooking (staple preservation)
- ✅ AI-powered pantry management with conversational interface
- ✅ Enhanced cooking mode with chat history
- ✅ Photo upload with Claude Vision API
- ✅ Recipe feedback and rating system

**Files Modified:**
- Created `lib/weekly_plan_manager.py`
- Enhanced `pages/generate_recipes.py`, `pages/cooking_mode.py`, `pages/weekly_planner.py`
- Renamed `pages/update_pantry.py` → `pages/pantry.py`

### Version 1.0.0 - MVP Release (November 2025) ✅
**Theme:** Core Functionality

- ✅ Basic recipe generation
- ✅ Manual pantry management
- ✅ Weekly meal planner
- ✅ Shopping list
- ✅ Meal history
- ✅ Authentication

---

## Version 2.0 - Next Release

**Target Date:** December 2025 (2-3 weeks)
**Theme:** Intelligence & Usability Enhancements

### High Priority Features

#### 1. Expiry Alerts & Notifications ⏰
**Priority:** HIGH
**Effort:** Medium (3-4 days)
**Dependencies:** None

**Description:**
Proactive alerts when items are about to expire to reduce food waste.

**Implementation Details:**
- Dashboard widget showing items expiring in next 3 days
- Color-coded alerts (green = fresh, yellow = expiring soon, red = expired)
- Daily check on app load for expiring items
- Recipe suggestions prioritizing expiring ingredients
- Optional email notifications (future enhancement)

**Technical Approach:**
```python
# lib/expiry_manager.py
def get_expiring_items(days_threshold=3):
    """Returns items expiring within threshold days."""
    # Parse fresh.md for expiry dates
    # Compare with today's date
    # Return sorted list by expiry date

def suggest_recipes_with_expiring_items(expiring_items):
    """Generate recipes that use expiring ingredients."""
    # Pass expiring items to LLM with higher priority
    # Suggest recipes that maximize usage of expiring items
```

**Files to Create/Modify:**
- `lib/expiry_manager.py` (new)
- `app.py` (add expiry widget to dashboard)
- `pages/generate_recipes.py` (prioritize expiring ingredients)
- `pages/pantry.py` (highlight expiring items)

**User Stories:**
- As a user, I want to see which items are expiring soon on my dashboard
- As a user, I want recipe suggestions that use ingredients about to expire
- As a user, I want visual indicators for item freshness

---

#### 2. Recipe Scaling 📐
**Priority:** HIGH
**Effort:** Small (2-3 days)
**Dependencies:** None

**Description:**
Automatically scale recipes from 2 servings to any number (1, 2, 4, 6, 8).

**Implementation Details:**
- Add "Servings" selector to recipe display (dropdown: 1, 2, 4, 6, 8)
- LLM-powered scaling for complex measurements ("1 can" → "2 cans")
- Scale both ingredients and cooking times appropriately
- Save scaled version to shopping list
- Display original and scaled versions side-by-side

**Technical Approach:**
```python
# lib/recipe_scaler.py
def scale_recipe(recipe: dict, original_servings: int, target_servings: int) -> dict:
    """Scale recipe ingredients using LLM for complex conversions."""
    scale_factor = target_servings / original_servings

    # Use LLM to intelligently scale ingredients
    # Handle edge cases: "1 can" vs "200g" vs "to taste"
    # Don't scale time linearly (some steps don't scale)

    return scaled_recipe
```

**Files to Create/Modify:**
- `lib/recipe_scaler.py` (new)
- `pages/generate_recipes.py` (add servings selector)
- `pages/cooking_mode.py` (add servings selector)
- `pages/weekly_planner.py` (display serving size)

**User Stories:**
- As a user, I want to scale recipes for different numbers of people
- As a user, I want to make just 1 serving for myself
- As a user, I want to double a recipe for meal prep

---

#### 3. Nutrition Information 🥗
**Priority:** HIGH
**Effort:** Medium (3-4 days)
**Dependencies:** None (could use external API later)

**Description:**
Display estimated nutrition information for recipes (calories, macros).

**Implementation Details:**
- LLM estimates calories and macros based on ingredients
- Display nutrition facts card for each recipe
- Show per-serving breakdown
- Filter recipes by dietary goals (low-carb, high-protein, etc.)
- Track nutrition over week in meal planner

**Technical Approach:**
```python
# lib/nutrition_estimator.py
def estimate_nutrition(recipe: dict) -> dict:
    """Use LLM to estimate nutrition info from ingredients."""
    # Prompt LLM with ingredient list and quantities
    # Return: calories, protein, carbs, fat, fiber
    # Per-serving breakdown

def calculate_weekly_nutrition(weekly_plan: list) -> dict:
    """Aggregate nutrition across weekly meal plan."""
```

**Files to Create/Modify:**
- `lib/nutrition_estimator.py` (new)
- `pages/generate_recipes.py` (display nutrition card)
- `pages/cooking_mode.py` (show nutrition)
- `pages/weekly_planner.py` (weekly nutrition summary)
- `data/preferences.md` (add nutrition goals)

**User Stories:**
- As a user, I want to see calorie counts for recipes
- As a user, I want to track my weekly nutrition intake
- As a user, I want to filter recipes by protein content

---

#### 4. Recipe Import from URLs 🔗
**Priority:** HIGH
**Effort:** Medium (4-5 days)
**Dependencies:** None

**Description:**
Import recipes from popular recipe websites by pasting a URL.

**Implementation Details:**
- Input: URL field on recipe generation page
- Use LLM to parse and extract recipe from HTML
- Handle various formats (AllRecipes, Food Network, blogs, etc.)
- Standardize to our recipe format
- Save to loved.md or liked.md
- Add ingredients to shopping list option

**Technical Approach:**
```python
# lib/recipe_importer.py
import anthropic
import requests

def import_recipe_from_url(url: str) -> dict:
    """Fetch URL and use LLM to extract recipe."""
    # Fetch HTML content
    html_content = requests.get(url).text

    # Use Claude to parse HTML and extract:
    # - Recipe name
    # - Ingredients (with quantities)
    # - Instructions
    # - Time, servings, difficulty

    # Return standardized recipe dict
```

**Files to Create/Modify:**
- `lib/recipe_importer.py` (new)
- `pages/generate_recipes.py` (add import section)
- `requirements.txt` (add requests, beautifulsoup4)

**User Stories:**
- As a user, I want to import recipes from my favorite websites
- As a user, I want imported recipes to be formatted like generated ones
- As a user, I want to add imported recipe ingredients to my shopping list

---

### Testing & Deployment

#### 5. Deploy to Streamlit Cloud ☁️
**Priority:** HIGH
**Effort:** Small (1-2 days)
**Dependencies:** None

**Description:**
Deploy application to Streamlit Cloud for public access.

**Implementation Details:**
- Set up Streamlit Cloud account
- Connect to GitHub repository
- Configure secrets (ANTHROPIC_API_KEY, AUTH credentials)
- Test deployment
- Set up custom domain (optional)
- Configure automatic deployments on push to main

**Steps:**
1. Create `.streamlit/config.toml` for production settings
2. Update `.env.example` with deployment notes
3. Create deployment documentation in README
4. Set up secrets in Streamlit Cloud dashboard
5. Test all features in deployed environment
6. Monitor usage and logs

**Files to Create/Modify:**
- `.streamlit/config.toml` (new)
- `.streamlit/secrets.toml.example` (new)
- `README.md` (add deployment section)
- `DEPLOYMENT.md` (new - deployment guide)

---

## Version 2.5 - Enhanced Intelligence

**Target Date:** January 2026
**Theme:** Smarter AI, Better Predictions

### Medium Priority Features

#### 6. Advanced Preference Learning 🧠
**Priority:** MEDIUM
**Effort:** Large (5-7 days)
**Dependencies:** Nutrition info (optional)

**Description:**
Deeper pattern recognition for cuisine and ingredient preferences.

**Implementation Details:**
- Analyze recipe ratings to detect patterns
- Learn preferred cooking times and difficulty levels
- Detect ingredient dislikes beyond explicit feedback
- Suggest new cuisines based on liked flavors
- Seasonal preference tracking (winter comfort food, summer salads)

**Technical Approach:**
- Periodic LLM analysis of meal history
- Update preferences.md with learned patterns
- Weight factors: rating, frequency cooked, notes keywords
- Generate "taste profile" summary

---

#### 7. Meal Prep Suggestions 📦
**Priority:** MEDIUM
**Effort:** Medium (3-4 days)
**Dependencies:** Recipe scaling

**Description:**
Identify recipes suitable for batch cooking and meal prep.

**Implementation Details:**
- Flag recipes that reheat well
- Suggest batch cooking schedules
- Calculate prep time savings
- Recommend storage containers needed
- Show which meals to prep together (shared ingredients)

---

#### 8. Leftover Management 🍱
**Priority:** MEDIUM
**Effort:** Medium (4-5 days)
**Dependencies:** Pantry tracking enhancement

**Description:**
Track leftovers and suggest creative ways to use them.

**Implementation Details:**
- After cooking, ask "How much is left?"
- Add leftovers to pantry with 3-4 day expiry
- Generate recipes using leftovers
- "Leftover Makeover" suggestions
- Track leftover usage to reduce waste

---

#### 9. Budget Tracking 💰
**Priority:** MEDIUM
**Effort:** Large (6-8 days)
**Dependencies:** None

**Description:**
Track grocery spending and cost per meal.

**Implementation Details:**
- Optional price entry for shopping list items
- Calculate total shopping trip cost
- Track cost per meal
- Monthly spending reports
- Budget alerts when approaching limits
- Compare recipe costs

**Files to Create/Modify:**
- `data/budget_history.md` (new)
- `pages/budget.py` (new page)
- `lib/budget_tracker.py` (new)

---

#### 10. Voice Input 🎤
**Priority:** MEDIUM
**Effort:** Medium (4-5 days)
**Dependencies:** Browser speech API support

**Description:**
Hands-free pantry updates and shopping list additions.

**Implementation Details:**
- Voice button on pantry page
- "Add 2 pounds of chicken"
- "Remove milk from shopping list"
- Works while cooking (hands-free)
- Uses browser's Web Speech API

---

## Version 3.0 - Social & Scaling

**Target Date:** February-March 2026
**Theme:** Community & Advanced Features

### Low Priority / Nice-to-Have Features

#### 11. Barcode Scanning 📷
**Priority:** LOW
**Effort:** Large (7-10 days)
**Dependencies:** External barcode API or database

**Description:**
Scan product barcodes to add items to pantry.

**Implementation Considerations:**
- Requires barcode API (Open Food Facts, UPC Database)
- Mobile camera access via Streamlit
- Nutrition data from barcode lookup
- Product name standardization

---

#### 12. Grocery Delivery Integration 🛒
**Priority:** LOW
**Effort:** Very Large (2-3 weeks)
**Dependencies:** Partnership with grocery services

**Description:**
One-click ordering from shopping list via Instacart, Amazon Fresh, etc.

**Implementation Considerations:**
- Requires API access from delivery services
- Complex authentication flow
- Price comparison across services
- Item matching challenges

---

#### 13. Weather-Based Recommendations ☀️
**Priority:** LOW
**Effort:** Small (2-3 days)
**Dependencies:** Weather API

**Description:**
Suggest comfort food on rainy days, salads on hot days.

**Implementation Details:**
- Integrate weather API (OpenWeatherMap)
- Adjust recipe suggestions based on temperature
- "Cozy soup for a rainy Tuesday"

---

#### 14. Social Features - Recipe Sharing 👥
**Priority:** LOW
**Effort:** Very Large (3-4 weeks)
**Dependencies:** Multi-user architecture

**Description:**
Share recipes and meal plans with family/friends.

**Implementation Considerations:**
- Requires database instead of markdown files
- User management system
- Privacy controls
- Recipe attribution
- Public/private recipe collections

---

#### 15. Meal Plan Templates 📋
**Priority:** LOW
**Effort:** Medium (3-4 days)
**Dependencies:** None

**Description:**
Pre-made weekly meal plans (e.g., "Keto Week", "Budget Friendly").

**Implementation Details:**
- Create template library
- One-click apply to weekly planner
- Customize templates before applying
- Community-contributed templates (future)

---

## Future Ideas Backlog

**Unsorted ideas for future consideration:**

- 🌱 **Sustainability tracking** - Carbon footprint per meal, local sourcing suggestions
- 🎓 **Cooking skill progression** - Level up from easy to advanced recipes
- 🏆 **Gamification** - Badges for trying new cuisines, using all ingredients
- 📊 **Analytics dashboard** - Most cooked recipes, cuisine breakdown, waste reduction stats
- 🌍 **Multi-language support** - Internationalization for global users
- 👨‍👩‍👧‍👦 **Family profiles** - Different preferences for each family member
- 🍷 **Wine pairing suggestions** - AI-recommended wine/beverage pairings
- ⏲️ **Smart appliance integration** - Send recipe to smart oven/Instant Pot
- 📱 **Native mobile app** - iOS/Android apps with offline mode
- 🎬 **Video tutorials** - Link to cooking technique videos
- 📖 **Cookbook export** - Generate PDF cookbook from loved recipes

---

## Technical Debt & Improvements

**Items to address for code quality and maintainability:**

### Code Quality
- [ ] Add comprehensive unit tests for all lib functions (target 80%+ coverage)
- [ ] Implement integration tests for key workflows
- [ ] Add type hints to all function signatures
- [ ] Set up pre-commit hooks for linting and formatting
- [ ] Add docstrings to all public functions

### Performance
- [ ] Implement caching for LLM responses (reduce API calls)
- [ ] Optimize file I/O operations (batch reads/writes)
- [ ] Add loading states for all LLM operations
- [ ] Implement request rate limiting for API calls

### Architecture
- [ ] Refactor recipe parsing into dedicated module
- [ ] Create consistent error handling patterns
- [ ] Add logging throughout application
- [ ] Standardize response formats from LLM agents
- [ ] Create shared utilities module for common operations

### Data Management
- [ ] Add backup/restore functionality for markdown files
- [ ] Implement data migration system for schema changes
- [ ] Add data validation for all user inputs
- [ ] Create data export feature (JSON, CSV)

### Security
- [ ] Review authentication implementation
- [ ] Add CSRF protection
- [ ] Implement rate limiting for API endpoints
- [ ] Add input sanitization for all user inputs
- [ ] Security audit for file operations

### Documentation
- [ ] Add inline code comments for complex logic
- [ ] Create developer onboarding guide
- [ ] Document API integration patterns
- [ ] Add troubleshooting guide
- [ ] Create video walkthrough for users

---

## Release Criteria

**Version 2.0 Release Checklist:**

**Features:**
- [ ] Expiry alerts working on dashboard
- [ ] Recipe scaling functional for all recipes
- [ ] Nutrition information displaying correctly
- [ ] Recipe import successfully parsing 90%+ of test URLs
- [ ] Deployed to Streamlit Cloud and accessible

**Quality:**
- [ ] All existing features still working
- [ ] No critical bugs
- [ ] Mobile-responsive on iOS and Android
- [ ] Performance acceptable (page load < 3s)
- [ ] Documentation updated

**Testing:**
- [ ] Manual testing of all workflows
- [ ] User testing with 2-3 beta users
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile device testing

**Documentation:**
- [ ] README.md updated with new features
- [ ] SPEC.md updated
- [ ] CHANGELOG.md updated
- [ ] User guide updated (if exists)

---

## Feedback & Contributions

**How to contribute to this roadmap:**

1. Open an issue on GitHub with feature suggestions
2. Discuss in project discussions
3. Vote on features using GitHub reactions
4. Submit pull requests for approved features

**Roadmap Review Schedule:**
- Monthly review of priorities
- Quarterly assessment of completed features
- Annual strategic planning

---

**Document Version:** 1.0
**Last Reviewed:** November 28, 2025
**Next Review:** December 15, 2025
