# AI Recipe Planner

An intelligent meal planning application powered by AI that helps you manage ingredients, discover recipes, and plan meals based on what's in your pantry.

## Features

- 🤖 **AI-Powered Recipe Suggestions**: Get personalized recipe recommendations based on available ingredients
- 💬 **Conversational Recipe Generation**: Add free-form preferences and chat with each recipe to refine it in real-time
- 📦 **Smart Pantry Management**: Track pantry staples and fresh ingredients with AI-powered chat interface
- 📸 **Photo Recognition**: Upload photos of groceries to automatically update your inventory
- 🛒 **Intelligent Shopping List**: Automatically syncs with weekly meal plan - ingredients added when you plan meals, removed when you delete them
- 📅 **Weekly Meal Planning**: Plan up to 7 meals for the week with automatic shopping list integration
- 👨‍🍳 **Interactive Cooking Mode**: Cook with AI assistance - ask questions, get help, and automatically update your pantry when done
- 🥫 **Auto Pantry Updates**: After cooking, smart removal of used ingredients while preserving staples like oil and spices
- 💚 **Preference Learning**: The AI learns your taste preferences over time
- 🔒 **Secure Authentication**: Built-in login system with session management
- ✅ **Simple Interface**: Intuitive buttons and easy navigation

## Tech Stack

- **Framework**: Python + Streamlit (all-in-one solution)
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Vision**: Claude 3.5 Sonnet (photo recognition)
- **Storage**: Markdown files (human-readable, LLM-friendly)
- **Hosting**: Streamlit Cloud (free tier)

## Documentation

- **[SPEC.md](./SPEC.md)** - Detailed product specification, architecture, and development roadmap
- **[agent.md](./agent.md)** - Python best practices, coding standards, and professional development guidelines
- **[claude.md](./claude.md)** - Instructions for AI assistants working on this project

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/meal-planner-v2.git
   cd meal-planner-v2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development (testing, linting)
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials:
   # - ANTHROPIC_API_KEY (required for AI features)
   # - AUTH_USERNAME (for web login)
   # - AUTH_PASSWORD (for web login)
   ```

   Example `.env` file:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   AUTH_USERNAME=your_username
   AUTH_PASSWORD=your_secure_password
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - The app will automatically open at `http://localhost:8501`

## How It Works

The app provides a complete meal planning workflow with automatic data synchronization:

### 1. **Generate Personalized Recipes** 🤖

#### Free-Form Preferences
- Add custom preferences when generating recipes
- Examples: "spicy", "under 30 minutes", "one pot meal", "low carb", "high protein"
- The AI incorporates your preferences into all suggested recipes

#### Per-Recipe Chat
- Each generated recipe has a chat interface for real-time refinement
- Have a back-and-forth conversation to modify recipes:
  - "Make this spicier"
  - "What if I don't have bell peppers?"
  - "Can you make this in 20 minutes instead?"
  - "Use mushrooms instead of tofu"
  - "Make this oil-free"
- Recipes update in-place based on your conversation
- Full chat history maintained for each recipe

### 2. **Plan Your Week** 📅
- Add meals to your weekly planner (up to 7 meals)
- Choose from generated recipes or your saved favorites
- **Automatic sync**: Needed ingredients are automatically added to your shopping list

### 3. **Shop for Ingredients** 🛒
- View your shopping list with all ingredients from planned meals
- Mark items as "Bought" to automatically add them to your pantry
- Remove items you don't need
- **Automatic sync**: Removing a meal from your plan removes its ingredients from the shopping list

### 4. **Cook with AI Assistance** 👨‍🍳
- Start cooking mode for any recipe
- Ask questions while cooking (substitutions, timing, techniques)
- AI assistant remembers your conversation (last 10 messages)
- Get step-by-step cooking instructions

### 5. **Rate Your Meal** ⭐
- When finished cooking, rate the recipe (1-5 stars)
- Add notes about what worked or what to change
- Meals are automatically logged to your history

### 6. **Update Your Pantry** 🥫
- **Smart pantry updates**: After rating, choose to update your pantry
- **Intelligent removal**: Fresh items and consumables are removed
- **Staples preserved**: Oil, spices, sauces, and shelf-stable items stay in your pantry
- Keeps your pantry accurate without manual tracking

### Complete Workflow Example:

```
1. Generate recipes with preference: "spicy and quick"
   → AI suggests 4 spicy recipes under 30 minutes

2. Chat with a recipe: "make this less spicy, I want mild heat"
   → Recipe updates in-place with milder seasoning

3. Add refined "Spicy Garlic Noodles" to weekly plan
   → Ingredients automatically added to shopping list

4. Go shopping, mark "garlic" and "chili flakes" as bought
   → Items automatically moved to pantry

5. Start cooking mode, ask "Can I use regular pasta instead of rice noodles?"
   → AI provides helpful answer

6. Finish cooking, rate 5 stars
   → Meal logged to history

7. Update pantry: removes garlic & chili flakes, keeps soy sauce, oil, salt
   → Pantry stays accurate for next recipe generation
```

## Project Structure

```
meal-planner-v2/
├── app.py                 # Main Streamlit app (home dashboard)
├── requirements.txt       # Python dependencies
├── .env                   # API keys (not committed)
├── .env.example          # Example environment file
├── .gitignore
│
├── pages/                 # Streamlit pages
│   ├── generate_recipes.py  # AI recipe suggestions
│   ├── pantry.py            # AI-powered pantry management
│   ├── shopping_list.py     # Shopping list with buy/remove
│   ├── weekly_planner.py    # Weekly meal planning
│   ├── meal_history.py      # Past meals and ratings
│   └── cooking_mode.py      # Interactive cooking assistant
│
├── lib/                   # Core logic
│   ├── auth.py                 # Authentication & session management
│   ├── llm_agents.py           # Claude API interactions
│   ├── file_manager.py         # Markdown file operations
│   ├── weekly_plan_manager.py  # Weekly plan & shopping list sync
│   ├── vision.py               # Photo recognition with Claude Vision
│   ├── recipe_parser.py        # Recipe parsing utilities
│   ├── exceptions.py           # Custom exceptions
│   └── logging_config.py       # Logging configuration
│
└── data/                  # All user data (markdown files)
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

## Development Standards

This project follows professional Python development practices:

- ✅ **Type checking** with mypy (strict mode)
- ✅ **Linting** with Ruff (replaces flake8, isort, etc.)
- ✅ **Testing** with pytest (outcome-based, 80%+ coverage)
- ✅ **Logging** instead of print statements (structured logging)
- ✅ **Pre-commit hooks** for automated quality checks
- ✅ **SOLID principles**, DRY, YAGNI, KISS

See [agent.md](./agent.md) for complete coding standards and best practices.

### Quick Commands

Use the included Makefile for common operations:

```bash
# Development
make install       # Install dependencies
make lint          # Run linter
make format        # Format code
make test          # Run tests with coverage
make clean         # Clean cache files

# Production (if deployed)
make restart       # Restart app and check logs
make status        # Check service status
make logs          # View error logs

# Help
make help          # Show all commands
```

### Quality Checks (Manual)

```bash
# Run linter
ruff check lib/ app.py

# Run type checker
mypy lib/ app.py

# Run tests with coverage
pytest --cov=lib

# Install pre-commit hooks
pre-commit install
```

## Current Status

### Completed Features ✅
- Project structure and development standards
- Secure authentication with session management
- **Recipe Generation**: AI-powered recipe suggestions based on pantry
  - Free-form preference input (e.g., "spicy", "quick", "low carb")
  - Per-recipe chat for real-time refinement
  - Conversation history maintained for each recipe
  - Recipes update in-place based on chat
- **Pantry Management**: AI chat interface for adding/removing items
- **Photo Recognition**: Upload photos to detect and add groceries
- **Weekly Meal Planner**: Plan up to 7 meals with automatic shopping list sync
- **Shopping List**: Add ingredients from recipes with smart categorization
  - Mark items as bought → auto-adds to pantry
  - Remove items you don't need
  - Automatic staple vs fresh categorization
- **Meal History**: Track past meals with ratings
- **Cooking Mode**: Interactive AI assistant while cooking
- **Smart Pantry Updates**: After cooking, intelligently removes consumables while preserving staples
- Claude Haiku 4.5 integration throughout

### In Development 🚧
- Expiry tracking and alerts
- Advanced preference learning
- Recipe import from URLs
- Nutrition information

## License

See [LICENSE](./LICENSE) file for details.
