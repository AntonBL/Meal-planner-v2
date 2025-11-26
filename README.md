# AI Recipe Planner

An intelligent meal planning application powered by AI that helps you manage ingredients, discover recipes, and plan meals based on what's in your pantry.

## Features

- 🤖 **AI-Powered Recipe Suggestions**: Get personalized recipe recommendations based on available ingredients
- 📦 **Smart Pantry Management**: Track pantry staples and fresh ingredients
- 📸 **Photo Recognition**: Upload photos of groceries to automatically update your inventory
- 💚 **Preference Learning**: The AI learns your taste preferences over time
- 📅 **Meal Planning**: Plan your weekly meals and generate shopping lists
- ✅ **Simple Interface**: Intuitive yes/no buttons and easy navigation

## Tech Stack

- **Framework**: Python + Streamlit (all-in-one solution)
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Vision**: Claude 3.5 Sonnet (photo recognition)
- **Storage**: Markdown files (human-readable, LLM-friendly)
- **Hosting**: Streamlit Cloud (free tier)

## Documentation

See [SPEC.md](./SPEC.md) for detailed product specification, architecture, and development roadmap.

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
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - The app will automatically open at `http://localhost:8501`

## Project Structure

```
meal-planner-v2/
├── app.py                 # Main Streamlit app (home dashboard)
├── requirements.txt       # Python dependencies
├── .env                   # API keys (not committed)
├── .env.example          # Example environment file
├── .gitignore
│
├── pages/                 # Streamlit pages (coming soon)
│   ├── generate_recipes.py
│   ├── update_pantry.py
│   └── meal_history.py
│
├── lib/                   # Core logic (coming soon)
│   ├── llm_agents.py      # Claude API interactions
│   ├── file_manager.py    # Markdown file operations
│   └── vision.py          # Image processing
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

## Current Status

✅ Project structure created
✅ Sample data files added
✅ Basic home dashboard implemented
🚧 Recipe generation page (coming next)
🚧 Pantry management (coming next)
🚧 Claude AI integration (coming next)

## License

See [LICENSE](./LICENSE) file for details.
