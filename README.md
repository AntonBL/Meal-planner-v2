# AI Recipe Planner

An intelligent meal planning application powered by AI that helps you manage ingredients, discover recipes, and plan meals based on what's in your pantry.

## Features

- 🤖 **AI-Powered Recipe Suggestions**: Get personalized recipe recommendations based on available ingredients
- 📦 **Smart Pantry Management**: Track pantry staples and fresh ingredients
- 📸 **Photo Recognition**: Upload photos of groceries to automatically update your inventory
- 💚 **Preference Learning**: The AI learns your taste preferences over time
- 📅 **Meal Planning**: Plan your weekly meals and generate shopping lists
- 🔒 **Secure Authentication**: Built-in login system with session management
- ✅ **Simple Interface**: Intuitive yes/no buttons and easy navigation

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
├── lib/                   # Core logic
│   ├── auth.py            # Authentication & session management
│   ├── llm_agents.py      # Claude API interactions
│   ├── file_manager.py    # Markdown file operations
│   ├── exceptions.py      # Custom exceptions
│   └── logging_config.py  # Logging configuration
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

✅ Project structure created
✅ Sample data files added
✅ Basic home dashboard implemented
✅ Development standards and tooling configured
✅ Secure authentication with session management
✅ Recipe generation page with Claude AI
✅ Claude AI integration (Claude Haiku 4.5)
🚧 Pantry management (in progress)
🚧 Meal history tracking (in progress)

## License

See [LICENSE](./LICENSE) file for details.
