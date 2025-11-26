# AI Recipe Planner - Product Specification

## Overview
An AI-powered meal planning application that helps manage ingredients, discover recipes, and plan meals based on what's available in your pantry. Designed for a household of 2 users with an intuitive interface and intelligent automation.

---

## Core Concept
The system uses an LLM agent as the "brain" that:
- Maintains knowledge of your ingredients (pantry + fresh items)
- Learns your recipe preferences (likes/dislikes)
- Suggests recipes based on available ingredients
- Updates inventory through manual input or photo recognition
- Adapts to your cuisine preferences and dietary needs

---

## Data Storage Architecture

### File-Based Storage (Text Files)
All data stored in structured text files that the LLM can read and update:

#### `/data/pantry.json`
```json
{
  "pantry_items": [
    {
      "name": "rice",
      "category": "grains",
      "quantity": "2 lbs",
      "last_updated": "2025-11-26",
      "expiry_estimate": null
    }
  ],
  "fresh_items": [
    {
      "name": "chicken breast",
      "quantity": "4 pieces",
      "purchase_date": "2025-11-24",
      "expiry_estimate": "2025-11-28"
    }
  ]
}
```

#### `/data/recipes.json`
```json
{
  "recipes": [
    {
      "id": "001",
      "name": "Chicken Stir Fry",
      "cuisine": "asian",
      "ingredients": ["chicken", "soy sauce", "vegetables"],
      "rating": 5,
      "status": "loved",
      "last_made": "2025-11-20",
      "notes": "Add extra ginger"
    }
  ]
}
```

#### `/data/preferences.json`
```json
{
  "cuisines": {
    "italian": "love",
    "mexican": "like",
    "indian": "neutral",
    "japanese": "love"
  },
  "dietary_restrictions": [],
  "allergies": [],
  "disliked_ingredients": ["cilantro"],
  "meal_frequency_preferences": {
    "chicken": "2-3 times/week",
    "fish": "once/week"
  }
}
```

#### `/data/meal_history.json`
```json
{
  "meals": [
    {
      "date": "2025-11-25",
      "recipe_id": "001",
      "feedback": "delicious",
      "modifications": "used brown rice instead"
    }
  ]
}
```

---

## Key Features

### 1. Recipe Generation
- **Input**: Select cuisine preferences (checkboxes/buttons)
- **Process**: LLM analyzes available ingredients + preferences
- **Output**: 3-5 recipe suggestions with:
  - Recipe name & description
  - Ingredients needed (highlighting what you have vs. need to buy)
  - Difficulty & time estimate
  - Nutritional info (optional)
- **Actions**:
  - ✅ "Cook This" (marks ingredients as used, logs to history)
  - ❌ "Not Interested" (learns preference)
  - 💾 "Save for Later"

### 2. Pantry Management

#### Manual Entry
- Simple form: Item name, quantity, category (pantry/fresh)
- Quick-add favorites (common items with one tap)
- Bulk entry mode (paste shopping list)

#### Photo Upload
- Take/upload photo of groceries or receipt
- Vision AI extracts items and quantities
- User confirms/edits before adding
- Updates pantry automatically

#### Smart Features
- Expiry warnings for fresh items
- Low stock alerts for pantry staples
- Shopping list generation

### 3. Recipe Feedback System
- After each meal:
  - ⭐ Star rating (1-5)
  - 👍/👎 Simple like/dislike
  - "Make Again?" Yes/No
  - Optional notes field
- LLM learns patterns and adjusts suggestions

### 4. Meal Planning View
- Weekly calendar view
- Drag-and-drop recipes to days
- Auto-generates shopping list for the week
- Considers ingredient overlap to minimize waste

---

## User Interface Design

### Platform Recommendation: **Progressive Web App (PWA)**
**Rationale:**
- Works on iPhone, Android, and desktop
- No app store approval needed
- Easier to update and maintain
- Can be "installed" to home screen
- Lower development cost than native app
- Hosted frontend = accessible anywhere

### Core UI Pages

#### 1. Home Dashboard
```
┌─────────────────────────────────┐
│  🏠 AI Recipe Planner           │
├─────────────────────────────────┤
│                                 │
│  📦 Pantry: 47 items            │
│  🥬 Fresh: 12 items             │
│  ⚠️  3 items expiring soon      │
│                                 │
│  ┌─────────────────────────┐   │
│  │  🎲 Generate Recipes    │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  📝 Update Pantry       │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  📅 Meal Plan           │   │
│  └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

#### 2. Recipe Generator
```
┌─────────────────────────────────┐
│  ← Back                         │
├─────────────────────────────────┤
│  What sounds good tonight?      │
│                                 │
│  Select cuisines:               │
│  [✓] Italian  [ ] Mexican       │
│  [ ] Asian    [✓] American      │
│  [ ] Indian   [ ] Mediterranean │
│                                 │
│  Recipe type:                   │
│  (•) Dinner  ( ) Lunch ( ) Quick│
│                                 │
│  ┌─────────────────────────┐   │
│  │  🤖 Get Suggestions     │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

#### 3. Recipe Results
```
┌─────────────────────────────────┐
│  Recipe Suggestions             │
├─────────────────────────────────┤
│                                 │
│  🍝 Creamy Garlic Pasta         │
│  ⏱️  25 min  |  ⭐⭐⭐ Medium     │
│  ✅ Have all ingredients!       │
│  ┌──────┐ ┌──────┐ ┌─────────┐ │
│  │ Cook │ │ Pass │ │ Details │ │
│  └──────┘ └──────┘ └─────────┘ │
│                                 │
│  🌮 Chicken Tacos               │
│  ⏱️  30 min  |  ⭐⭐ Easy         │
│  ⚠️  Need: tortillas, lime      │
│  ┌──────┐ ┌──────┐ ┌─────────┐ │
│  │ Cook │ │ Pass │ │ Details │ │
│  └──────┘ └──────┘ └─────────┘ │
│                                 │
└─────────────────────────────────┘
```

#### 4. Pantry Update
```
┌─────────────────────────────────┐
│  Update Pantry                  │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────┐   │
│  │  📸 Upload Photo        │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  ✏️  Manual Entry       │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  🗑️  Remove Items       │   │
│  └─────────────────────────┘   │
│                                 │
│  Recent additions:              │
│  • Milk (2 days ago)            │
│  • Eggs (2 days ago)            │
│                                 │
└─────────────────────────────────┘
```

---

## Technical Architecture

### Recommended Tech Stack

#### Frontend
- **Framework**: Next.js 14+ (React)
  - Server-side rendering
  - Built-in API routes
  - PWA support
  - Optimized performance
- **Styling**: Tailwind CSS
- **State Management**: React Context or Zustand
- **UI Components**: shadcn/ui or Material-UI

#### Backend
- **Runtime**: Node.js with Next.js API routes
- **LLM Integration**:
  - Primary: Anthropic Claude API (Claude 3.5 Sonnet)
  - Vision: Claude 3.5 Sonnet (for image recognition)
- **File Operations**: Node.js fs module with structured JSON

#### Infrastructure
- **Hosting**: Vercel (free tier, perfect for Next.js)
- **Storage**: Git repository + Vercel environment
- **Database**: File-based (JSON files in `/data` directory)
- **Authentication**: Simple password protection (2 users only)
  - NextAuth.js with credentials provider
  - Environment variables for user credentials

#### APIs & Services
- **LLM**: Anthropic Claude API
- **Image Recognition**: Claude 3.5 Sonnet Vision
- **Optional**:
  - Nutritional data: Edamam API or USDA FoodData Central
  - Recipe inspiration: Spoonacular API (if needed)

### Security Considerations

**For 2-User Household:**
1. **Authentication**: Simple username/password
   - Store hashed passwords in environment variables
   - Session-based auth with secure cookies
   - No need for complex user management

2. **API Keys**:
   - Store in `.env.local` (never commit)
   - Use Vercel environment variables for production

3. **Data Privacy**:
   - All data in private git repository
   - No third-party analytics
   - LLM API calls over HTTPS

4. **Access Control**:
   - Password protect the entire app
   - Optional: IP whitelist if always accessing from home

---

## LLM Agent Workflow

### Agent Responsibilities

1. **Recipe Suggestion Agent**
   - Reads: `pantry.json`, `recipes.json`, `preferences.json`
   - Process: Analyzes ingredients + preferences + history
   - Outputs: Recipe suggestions with reasoning
   - Updates: None (read-only operation)

2. **Pantry Update Agent** (Photo)
   - Reads: Image input, `pantry.json`
   - Process: Vision AI extracts items → matches existing inventory
   - Outputs: Detected items for user confirmation
   - Updates: `pantry.json` after confirmation

3. **Meal Logging Agent**
   - Reads: Selected recipe, `pantry.json`
   - Process: Deducts ingredients, logs meal
   - Updates: `pantry.json`, `meal_history.json`

4. **Preference Learning Agent**
   - Reads: User feedback, `recipes.json`, `preferences.json`
   - Process: Identifies patterns in likes/dislikes
   - Updates: `preferences.json`, `recipes.json` (ratings)

5. **Shopping List Agent**
   - Reads: Planned meals, `pantry.json`
   - Process: Calculates needed ingredients
   - Outputs: Shopping list grouped by store section

### Agent Prompt Structure

```typescript
const recipeAgentPrompt = `
You are a meal planning assistant. Your task is to suggest recipes.

CONTEXT:
- Available ingredients: {pantry_items}
- User preferences: {preferences}
- Recent meals: {meal_history}
- Cuisine request: {selected_cuisines}

INSTRUCTIONS:
1. Suggest 3-5 recipes that:
   - Use available ingredients (minimize shopping needs)
   - Match cuisine preferences
   - Avoid recently cooked meals (variety)
   - Respect dietary restrictions
2. For each recipe, specify:
   - Ingredients (mark which are available vs. needed)
   - Estimated time and difficulty
   - Brief description
3. Format as JSON

OUTPUT FORMAT:
{
  "suggestions": [
    {
      "name": "Recipe Name",
      "cuisine": "italian",
      "description": "...",
      "ingredients_available": [...],
      "ingredients_needed": [...],
      "time_minutes": 30,
      "difficulty": "easy"
    }
  ]
}
`;
```

---

## Development Phases

### Phase 1: MVP (Weeks 1-2)
- [ ] Basic Next.js setup with authentication
- [ ] File-based data storage (JSON files)
- [ ] Manual pantry management (add/remove items)
- [ ] Simple recipe generation (Claude API integration)
- [ ] Basic UI with 3 pages: Home, Pantry, Recipe Generator

### Phase 2: Core Features (Weeks 3-4)
- [ ] Photo upload for pantry updates (Vision AI)
- [ ] Recipe feedback system (like/dislike)
- [ ] Preference learning
- [ ] Meal history tracking
- [ ] Improved UI/UX

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] Weekly meal planning calendar
- [ ] Shopping list generation
- [ ] Expiry tracking and alerts
- [ ] Recipe detail pages with instructions
- [ ] Nutritional information

### Phase 4: Polish (Week 7+)
- [ ] PWA installation support
- [ ] Mobile-optimized UI
- [ ] Performance optimization
- [ ] Error handling and edge cases
- [ ] User testing and refinement

---

## Sample User Flows

### Flow 1: Generate a Recipe
1. User opens app → sees dashboard
2. Clicks "Generate Recipes"
3. Selects cuisines: Italian ✓, Asian ✓
4. Clicks "Get Suggestions"
5. LLM reads pantry + preferences
6. Shows 4 recipe options
7. User clicks "Cook This" on Pasta Primavera
8. System asks: "Mark ingredients as used?" → Yes
9. Updates pantry, logs meal to history

### Flow 2: Update Pantry with Photo
1. User clicks "Update Pantry"
2. Clicks "Upload Photo"
3. Takes picture of grocery bags
4. Vision AI processes → shows detected items
5. User confirms/edits list
6. Clicks "Add to Pantry"
7. Items added with timestamp

### Flow 3: Rate a Meal
1. After cooking, app prompts: "How was Pasta Primavera?"
2. User taps 5 stars
3. "Make again?" → Yes
4. Optional notes: "Added extra basil"
5. LLM updates recipe rating and preferences

---

## Success Metrics

- **User Engagement**: Recipes generated per week
- **Waste Reduction**: Fewer expired items
- **Satisfaction**: Recipe ratings average
- **Efficiency**: Time saved on meal planning
- **Accuracy**: Photo recognition success rate

---

## Future Enhancements (Post-MVP)

- Voice input: "Add milk to pantry"
- Barcode scanning for precise product tracking
- Integration with grocery delivery services
- Nutritional tracking and goals
- Recipe scaling (adjust servings)
- Leftover management suggestions
- Seasonal recipe recommendations
- Budget tracking
- Collaborative cooking mode (assign tasks)

---

## Open Questions

1. **Preferred cuisines**: What are your top 5 favorite cuisines?
2. **Dietary restrictions**: Any allergies or dietary preferences?
3. **Meal frequency**: How many times per week do you cook at home?
4. **Shopping habits**: Weekly grocery trips or as-needed?
5. **Current pain points**: What's most frustrating about meal planning now?
6. **Device usage**: Primarily phone, tablet, or desktop?
7. **Recipe sources**: Do you have existing recipes to import?

---

## Getting Started

**Next Steps:**
1. Review this spec and provide feedback
2. Answer open questions above
3. Set up development environment
4. Create initial project structure
5. Begin Phase 1 development

**Estimated Timeline**: 6-8 weeks to full-featured MVP
**Recommended Approach**: Start with web app, can port to native mobile later if needed
