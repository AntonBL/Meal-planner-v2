# AI Recipe Planner - Development Plan

**Last Updated:** 2025-11-27
**Status:** MVP In Progress - Deployment Complete, Features Pending

---

## 🎯 Project Overview

Building an AI-powered meal planning app for a 2-person household using:
- **Framework:** Streamlit (Python)
- **AI:** Claude Haiku 4.5 (fast, cost-effective)
- **Storage:** Markdown files (human-readable)
- **Deployment:** Akamai Cloud (Ubuntu server)

---

## ✅ Current Status

### Infrastructure (100% Complete)

**Deployment:**
- ✅ Server: Akamai Cloud (Ubuntu 24.04)
- ✅ HTTPS: Self-signed SSL certificate (valid 365 days)
- ✅ Authentication: HTTP Basic Auth (username: roger)
- ✅ Firewall: UFW configured (ports 22, 80, 443)
- ✅ Process Manager: Supervisor (auto-restart)
- ✅ Reverse Proxy: Nginx
- ✅ Package Manager: UV (fast Python package management)

**Access:**
- URL: `https://50.116.63.56`
- Username: `roger`
- Password: (set via htpasswd)

**Services:**
```bash
# Application service
supervisorctl status meal-planner
supervisorctl restart meal-planner

# Logs
tail -f /var/log/meal-planner.out.log
tail -f /var/log/meal-planner.err.log

# Web server
systemctl status nginx
systemctl restart nginx
```

**API Configuration:**
- ✅ Claude Haiku 4.5 configured (`claude-haiku-4-5`)
- ✅ API key loaded from .env
- ✅ dotenv integration working

### Application Features (40% Complete)

**Working:**
- ✅ Home dashboard with stats
- ✅ Recipe generation page (basic UI + API integration)
- ✅ Data structure (all markdown files created)
- ✅ LLM agents library (ClaudeProvider, RecipeGenerator)
- ✅ File manager library
- ✅ Exception handling framework
- ✅ Structured logging

**Missing (Causing Errors):**
- ❌ `pages/update_pantry.py` (referenced but doesn't exist)
- ❌ `pages/meal_history.py` (referenced but doesn't exist)
- ❌ Recipe feedback system
- ❌ Photo upload (Vision API)
- ❌ Smart pantry updates
- ❌ Shopping list management

---

## 🚧 Known Issues

### Critical (Blocking Navigation)
1. **Missing Pages** - Home dashboard links to non-existent pages
   - Impact: Users see errors when clicking "Update Pantry" or "Meal History"
   - Priority: HIGH
   - Fix: Create stub pages with basic functionality

### Non-Critical
2. **Expiring Soon** - Hardcoded to 3 items
   - Impact: Dashboard shows inaccurate count
   - Priority: MEDIUM
   - Fix: Parse dates from fresh.md

3. **Recipe Suggestions** - No feedback loop
   - Impact: Can generate recipes but can't save favorites
   - Priority: MEDIUM
   - Fix: Add "Cook This" button functionality

---

## 📋 Development Phases

### Phase 1: MVP - Complete Core Loop (NEXT)
**Goal:** Functional meal planning system with basic features
**Estimated Time:** 2-3 hours
**Priority:** HIGH

#### Tasks:

**1.1 Create Update Pantry Page** (45 min)
- [ ] Create `pages/update_pantry.py`
- [ ] Implement manual entry form (item name, quantity, category)
- [ ] Add dropdown for category (Pantry Staple / Fresh Item)
- [ ] Add date picker for fresh items (expiry date)
- [ ] Save to appropriate markdown file (staples.md or fresh.md)
- [ ] Show current pantry contents (grouped by category)
- [ ] Add delete item functionality
- [ ] Add edit item functionality (optional)

**1.2 Create Meal History Page** (30 min)
- [ ] Create `pages/meal_history.py`
- [ ] Read and parse `data/meal_history.md`
- [ ] Display meals chronologically (newest first)
- [ ] Show ratings with stars (⭐⭐⭐⭐⭐)
- [ ] Show notes and ingredients used
- [ ] Add filters (by month, by rating)
- [ ] Add search functionality (optional)

**1.3 Recipe Feedback System** (45 min)
- [ ] Add "Cook This" button to recipe suggestions
- [ ] When clicked, show rating modal:
  - Star rating (1-5)
  - Optional notes field
  - "Would you make this again?" (Yes/No)
- [ ] Save to `data/meal_history.md` with timestamp
- [ ] Move recipe to appropriate file:
  - 5 stars → `recipes/loved.md`
  - 3-4 stars → `recipes/liked.md`
  - 1-2 stars → `recipes/not_again.md`
- [ ] Show success message

**1.4 Smart Pantry Updates** (30 min)
- [ ] After "Cook This" button, mark ingredients as used
- [ ] Use LLM to determine which items to remove/reduce
- [ ] Update `data/pantry/staples.md` and `fresh.md`
- [ ] Show "Pantry updated" confirmation

**1.5 Cooking Mode with AI Chat** (60 min)
- [ ] Create `pages/cooking_mode.py`
- [ ] Display active recipe with full details
- [ ] Implement chat interface (message input + history)
- [ ] Store chat messages in session state
- [ ] Integrate with Claude API for Q&A
- [ ] Pass recipe context in each API call
- [ ] Add "✅ Finished Cooking" button to exit to rating
- [ ] Add "Clear Chat" button
- [ ] Show helpful prompts (e.g., "Ask me anything about this recipe!")

**1.6 Testing & Bug Fixes** (30 min)
- [ ] Test all navigation works
- [ ] Test recipe generation end-to-end
- [ ] Test pantry add/remove
- [ ] Test meal history logging
- [ ] Test cooking mode chat interactions
- [ ] Fix expiring soon counter (parse dates)
- [ ] Check error handling

**Success Criteria for Phase 1:**
- ✅ Can navigate entire app without errors
- ✅ Can generate recipes based on pantry
- ✅ Can add items to pantry manually
- ✅ Can enter cooking mode with a recipe
- ✅ Can ask questions about recipe and get AI responses
- ✅ Can finish cooking and rate recipe
- ✅ Pantry auto-updates after cooking
- ✅ Meal history shows past meals

---

### Phase 2: Enhanced Features (LATER)
**Goal:** Add photo upload and smart features
**Estimated Time:** 3-4 hours
**Priority:** MEDIUM

#### Tasks:

**2.1 Photo Upload - Vision API** (90 min)
- [ ] Add file uploader to Update Pantry page
- [ ] Implement Claude Vision integration
- [ ] Send image + prompt to Claude API
- [ ] Parse detected items from response
- [ ] Show detected items in editable table
- [ ] Allow user to confirm/edit before adding
- [ ] Auto-categorize as staple vs fresh
- [ ] Add expiry estimates for fresh items

**2.2 Shopping List Management** (45 min)
- [ ] Add "Add to Shopping List" button on recipes
- [ ] Aggregate missing ingredients
- [ ] Save to `data/pantry/shopping_list.md`
- [ ] Show shopping list on Update Pantry page
- [ ] Allow marking items as purchased
- [ ] Auto-move purchased items to pantry

**2.3 Expiry Tracking** (45 min)
- [ ] Parse dates from `fresh.md`
- [ ] Calculate days until expiry
- [ ] Show "Expiring Soon" alert (< 3 days)
- [ ] Highlight expiring items in pantry view
- [ ] Suggest recipes using expiring items
- [ ] Add "Use Soon" badge on dashboard

**2.4 Preference Learning** (30 min)
- [ ] Track cuisine preferences from ratings
- [ ] Update `preferences.md` automatically
- [ ] Identify favorite ingredients
- [ ] Identify disliked ingredients
- [ ] Use in recipe suggestions

**Success Criteria for Phase 2:**
- ✅ Can upload photo and detect items
- ✅ Shopping list auto-generates from recipes
- ✅ Dashboard shows accurate expiry warnings
- ✅ AI learns preferences over time

---

### Phase 3: Polish & Optimization (OPTIONAL)
**Goal:** Improve UX and add nice-to-have features
**Estimated Time:** 2-3 hours
**Priority:** LOW

#### Tasks:

**3.1 UI/UX Improvements**
- [ ] Add loading spinners for API calls
- [ ] Better error messages (user-friendly)
- [ ] Mobile responsive design
- [ ] Add keyboard shortcuts
- [ ] Improve page load times
- [ ] Add "Back to Home" buttons
- [ ] Better typography and spacing

**3.2 Advanced Features**
- [ ] Weekly meal planning calendar
- [ ] Bulk pantry entry (paste list)
- [ ] Recipe import from URL
- [ ] Nutrition information
- [ ] Budget tracking
- [ ] Barcode scanning (stretch goal)

**3.3 Testing & Quality**
- [ ] Add unit tests for core functions
- [ ] Add integration tests
- [ ] Run type checking (mypy)
- [ ] Run linting (ruff)
- [ ] Test on mobile devices
- [ ] User acceptance testing

---

## 🛠 Technical Decisions Made

### Architecture

**Why Streamlit?**
- Pure Python (no JavaScript)
- Fast development cycle
- Built-in UI components
- Works on all devices
- Perfect for 2-user app

**Why Markdown Files?**
- Human-readable
- Easy to edit manually
- LLM-friendly (no parsing complexity)
- Git-friendly for backups
- No database setup needed

**Why Claude Haiku 4.5?**
- Fast (2x faster than Sonnet)
- Cost-effective ($1/$5 per million tokens)
- Good coding performance
- Perfect for recipe generation
- Vision API included

**Why UV?**
- 10-100x faster than pip
- Better dependency resolution
- Modern Python packaging
- User requested it

**Why Self-Signed SSL?**
- Free and immediate
- No domain needed
- Good for personal use
- Can upgrade to Let's Encrypt later

---

## 📁 Project Structure

```
Meal-planner-v2/
├── app.py                      # ✅ Home dashboard
├── requirements.txt            # ✅ Dependencies
├── .env                        # ✅ API key (secured)
├── .gitignore                  # ✅ Ignore sensitive files
│
├── pages/                      # Streamlit pages
│   ├── generate_recipes.py    # ✅ Recipe generation
│   ├── cooking_mode.py        # ❌ TODO: Phase 1.6
│   ├── update_pantry.py       # ❌ TODO: Phase 1
│   └── meal_history.py        # ❌ TODO: Phase 1
│
├── lib/                        # Core logic
│   ├── llm_agents.py          # ✅ Claude API
│   ├── file_manager.py        # ✅ Markdown I/O
│   ├── exceptions.py          # ✅ Custom errors
│   ├── logging_config.py      # ✅ Structured logging
│   └── vision.py              # ❌ TODO: Phase 2
│
└── data/                       # User data (markdown)
    ├── pantry/
    │   ├── staples.md         # ✅ Pantry items
    │   ├── fresh.md           # ✅ Perishables
    │   └── shopping_list.md   # ✅ To buy
    ├── recipes/
    │   ├── loved.md           # ✅ 5-star favorites
    │   ├── liked.md           # ✅ 3-4 stars
    │   └── not_again.md       # ✅ 1-2 stars
    ├── preferences.md         # ✅ User preferences
    └── meal_history.md        # ✅ Cooking log
```

---

## 🎯 Success Metrics

### Phase 1 MVP
- [ ] Zero navigation errors
- [ ] Can generate 3-5 recipe suggestions in < 10 seconds
- [ ] Can add pantry items in < 30 seconds
- [ ] Can cook and rate a meal in < 1 minute
- [ ] Pantry auto-updates correctly after cooking

### Phase 2 Features
- [ ] Photo detection > 80% accurate
- [ ] Shopping list generation works
- [ ] Expiry warnings are accurate
- [ ] AI suggestions improve over time

### Phase 3 Polish
- [ ] App loads in < 3 seconds
- [ ] No errors in logs
- [ ] Works on mobile devices
- [ ] Users happy with UX

---

## 🔄 Update Process

When code changes:
```bash
# SSH into server
ssh root@50.116.63.56

# Pull latest changes
cd /root/Meal-planner-v2
git pull

# Update dependencies (if needed)
source venv/bin/activate
uv pip install -r requirements.txt

# Restart app
supervisorctl restart meal-planner

# Check logs
tail -f /var/log/meal-planner.out.log
```

---

## 📝 Notes & Decisions

### User Preferences (from SPEC.md)
- Household of 2 people
- Cuisines: Italian, Asian, American (favorites)
- Dietary: No restrictions, wife dislikes cilantro
- Cooking: 30 min weeknight meals preferred
- Proteins: Prefer chicken/fish over red meat
- Style: One-pan meals (easy cleanup)

### Technical Constraints
- Must use pure Python (Streamlit)
- Must work on mobile browsers
- Must be simple to maintain
- Budget: Free tier for AI API preferred

### Security Considerations
- HTTPS enforced (self-signed)
- Password protected (HTTP Basic Auth)
- API key in .env file (chmod 600)
- Firewall configured
- Consider upgrade to Let's Encrypt if domain added

---

## 🚀 Getting Started (Next Session)

**Pre-requisites:**
- ✅ Server deployed and running
- ✅ API key configured
- ✅ Claude Haiku 4.5 working

**To start Phase 1:**
1. Create `pages/update_pantry.py` (see task 1.1)
2. Create `pages/meal_history.py` (see task 1.2)
3. Test navigation works
4. Add recipe feedback system (task 1.3)
5. Test end-to-end flow

**Estimated Session Time:** 2-3 hours

---

## 📚 Related Documentation

- **[SPEC.md](./SPEC.md)** - Complete product specification
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Server deployment guide (updated to use UV)
- **[README.md](./README.md)** - Project overview
- **[agent.md](./agent.md)** - Python coding standards
- **[claude.md](./claude.md)** - AI assistant instructions

---

## 🎯 Next Actions

**Immediate (This Week):**
- [ ] Create update_pantry.py page
- [ ] Create meal_history.py page
- [ ] Add recipe feedback system
- [ ] Test complete user flow

**Short-term (Next Week):**
- [ ] Add photo upload (Vision API)
- [ ] Implement shopping list
- [ ] Add expiry tracking

**Long-term (Future):**
- [ ] Weekly meal planning
- [ ] Recipe import
- [ ] Nutrition tracking
- [ ] Get a domain name for proper SSL

---

**Document Status:** Active working document
**Owner:** Development team
**Review Frequency:** After each phase completion
