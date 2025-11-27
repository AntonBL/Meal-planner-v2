# Claude AI Assistant Instructions

**Instructions for Claude when working on the AI Recipe Planner project**

---

## Overview

You are working on a professional Python application for meal planning and recipe management. This is production-quality code, not a learning exercise. Follow professional software engineering practices at all times.

---

## Required Reading

**BEFORE writing any code, you MUST:**

1. Read and internalize **[agent.md](./agent.md)** - this contains all Python best practices, coding standards, and architectural principles for this project

2. Understand the project architecture in **[SPEC.md](./SPEC.md)**

3. Review existing code to maintain consistency

---

## Core Principles (from agent.md)

### Code Quality Standards

✅ **ALWAYS:**
- Use structured logging (never `print()` statements)
- Include complete type hints on all functions
- Write docstrings (Google style) for all public functions/classes
- Follow DRY, YAGNI, KISS, and SOLID principles
- Handle errors with specific exception classes
- Write outcome-based tests with pytest
- Use `pathlib.Path` instead of string paths
- Validate inputs early (fail fast)

❌ **NEVER:**
- Use `print()` for output (use `logging` module)
- Commit code without type hints
- Leave functions without docstrings
- Repeat code (extract into functions)
- Over-engineer solutions (YAGNI)
- Ignore errors or use bare `except:` clauses
- Use `os.path` when `pathlib` is clearer

### Testing Requirements

Every new feature MUST include:
- Unit tests using pytest
- Tests for happy path AND error cases
- Mocked external dependencies (LLM API, file I/O)
- Isolated tests that don't depend on each other
- AAA pattern (Arrange, Act, Assert)

**Test outcomes, not implementation details.**

### Type Safety Requirements

All code must pass:
```bash
ruff check lib/ app.py
mypy lib/ app.py
```

Configure mypy with strict settings:
- `disallow_untyped_defs = true`
- `warn_return_any = true`
- `strict_equality = true`

### Logging Requirements

Use structured logging with context:
```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD
logger.info(
    "Recipe generated successfully",
    extra={
        "cuisine": cuisine,
        "ingredient_count": len(ingredients),
        "execution_time_ms": elapsed_ms
    }
)

# ❌ BAD
print("Recipe generated")
```

---

## Development Workflow

### 1. Before Writing Code

- [ ] Understand the requirement completely
- [ ] Check if similar code already exists (DRY)
- [ ] Consider if this feature is actually needed (YAGNI)
- [ ] Plan the simplest solution (KISS)
- [ ] Identify which principles from agent.md apply

### 2. While Writing Code

- [ ] Use type hints everywhere
- [ ] Add logging with structured context
- [ ] Write docstrings as you go
- [ ] Keep functions small and focused (SRP)
- [ ] Avoid premature optimization
- [ ] Handle errors explicitly

### 3. After Writing Code

- [ ] Write tests (aim for 80%+ coverage)
- [ ] Run linter: `ruff check --fix .`
- [ ] Run type checker: `mypy .`
- [ ] Run tests: `pytest --cov=lib`
- [ ] Review against checklist in agent.md
- [ ] Update documentation if needed
- [ ] **Check logs after restart** (see Deployment Operations below)

### 4. Code Review Checklist

Before considering code "done":
- [ ] No `print()` statements remain
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Tests are written and passing
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] No obvious DRY violations
- [ ] Error handling is appropriate
- [ ] Logging provides useful context

---

## Architecture Patterns to Follow

### Repository Pattern
Separate data access from business logic:
- Repositories handle file I/O
- Services contain business logic
- Keep them separate and testable

### Dependency Injection
Make dependencies explicit:
```python
# ✅ GOOD
class RecipeService:
    def __init__(self, repository: RecipeRepository, llm: LLMProvider):
        self.repository = repository
        self.llm = llm

# ❌ BAD
class RecipeService:
    def __init__(self):
        self.repository = MarkdownRecipeRepository()  # Hard-coded
        self.llm = anthropic.Anthropic()  # Hard to test
```

### Service Layer
Encapsulate business logic in service classes:
- Services orchestrate between repositories and external APIs
- Services contain domain logic
- Services are easily testable with mocked dependencies

---

## File Organization

```
lib/
├── __init__.py
├── repositories.py      # Data access layer
├── services.py          # Business logic layer
├── llm_agents.py        # LLM integration
├── file_manager.py      # File utilities
├── models.py            # Data models (dataclasses)
├── exceptions.py        # Custom exceptions
└── logging_config.py    # Logging setup

tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_repositories.py
├── test_services.py
├── test_llm_agents.py
└── fixtures/            # Test data files
```

---

## Common Patterns

### Loading Data Files

```python
from pathlib import Path
from typing import Literal
import logging

logger = logging.getLogger(__name__)

DataFile = Literal['staples', 'fresh', 'shopping_list']

def load_pantry_file(file_type: DataFile) -> str:
    """Load a pantry data file.

    Args:
        file_type: Type of pantry file to load

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If the data file doesn't exist
    """
    file_map = {
        'staples': 'data/pantry/staples.md',
        'fresh': 'data/pantry/fresh.md',
        'shopping_list': 'data/pantry/shopping_list.md',
    }

    file_path = Path(file_map[file_type])

    logger.debug(
        "Loading pantry file",
        extra={"file_type": file_type, "file_path": str(file_path)}
    )

    try:
        content = file_path.read_text(encoding='utf-8')
        logger.info(
            "Pantry file loaded successfully",
            extra={"file_type": file_type, "size_bytes": len(content)}
        )
        return content
    except FileNotFoundError:
        logger.error(
            "Pantry file not found",
            extra={"file_type": file_type, "file_path": str(file_path)}
        )
        raise
```

### LLM API Calls

```python
import anthropic
from typing import Protocol
import logging

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def generate(self, prompt: str, max_tokens: int = 2000) -> str: ...

class ClaudeProvider:
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Claude API.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from the LLM

        Raises:
            LLMAPIError: If API call fails
        """
        logger.info(
            "Calling Claude API",
            extra={"prompt_length": len(prompt), "max_tokens": max_tokens}
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            logger.info(
                "Claude API call successful",
                extra={"response_length": len(response_text)}
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude API call failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise LLMAPIError(f"API call failed: {e}") from e
```

### Writing Tests

```python
import pytest
from pathlib import Path
from unittest.mock import Mock
from lib.services import RecipeService
from lib.exceptions import RecipeNotFoundError

@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    repo = Mock()
    repo.get_loved_recipes.return_value = "# Sample recipes..."
    return repo

@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing."""
    llm = Mock()
    llm.generate.return_value = "Pasta Carbonara\nChicken Stir Fry"
    return llm

def test_suggest_recipes_success(mock_repository, mock_llm):
    """Test successful recipe suggestion generation."""
    # Arrange
    service = RecipeService(repository=mock_repository, llm=mock_llm)
    cuisines = ["italian", "asian"]
    ingredients = ["pasta", "chicken", "eggs"]

    # Act
    recipes = service.suggest_recipes(cuisines, ingredients)

    # Assert
    assert len(recipes) == 2
    assert "Pasta Carbonara" in recipes
    mock_llm.generate.assert_called_once()

def test_suggest_recipes_empty_ingredients(mock_repository, mock_llm):
    """Test that empty ingredients raises ValueError."""
    # Arrange
    service = RecipeService(repository=mock_repository, llm=mock_llm)

    # Act & Assert
    with pytest.raises(ValueError, match="Ingredients list cannot be empty"):
        service.suggest_recipes(["italian"], [])
```

---

## Communication with User

When presenting code changes to the user:

1. **Explain the reasoning**: Why you chose this approach
2. **Reference principles**: Mention which principles from agent.md you applied
3. **Highlight testing**: Show what tests you wrote
4. **Note trade-offs**: If you made any compromises, explain them

Example:
> "I've implemented the recipe suggestion service following the Service Layer pattern from agent.md. The service depends on injected interfaces (Repository and LLMProvider) to maintain testability. I've included comprehensive logging with structured context, type hints throughout, and wrote 5 tests covering both happy paths and error cases. The code passes both ruff and mypy checks."

---

## Pragmatic Decision Making

While following best practices is important, be pragmatic:

- **Don't over-engineer**: YAGNI applies - build what's needed now
- **Don't under-engineer**: But also don't skip logging, types, or tests
- **Balance is key**: Professional code is both robust AND simple

When in doubt, ask yourself:
1. Is this the simplest solution that works?
2. Can I test this easily?
3. Will another developer understand this in 6 months?
4. Does this follow the principles in agent.md?

---

## Deployment Operations

### After Every Code Change and Restart

**ALWAYS check logs before confirming success:**

```bash
# Easiest way: Use Makefile (does everything automatically)
make restart

# This will:
# - Restart the service
# - Wait for startup
# - Check service status
# - Show recent error logs
# - Check for errors in output log
```

**Manual method (if needed):**

```bash
# Restart the service
supervisorctl restart meal-planner

# Wait a few seconds for startup
sleep 3

# Check for errors in error log
tail -30 /var/log/meal-planner.err.log

# Check for errors in output log
tail -50 /var/log/meal-planner.out.log | grep -i -E "(error|warning|exception|traceback)"

# Verify service is running
supervisorctl status meal-planner

# Test the endpoint
curl -k -s https://localhost | head -20
```

**Never say "it's ready" without checking logs first!**

### Common Log Locations

- Error log: `/var/log/meal-planner.err.log`
- Output log: `/var/log/meal-planner.out.log`
- Service status: `supervisorctl status meal-planner`

### Environment Variables

Credentials are stored in `.env` file:
- `ANTHROPIC_API_KEY` - Claude API key
- `AUTH_USERNAME` - Login username
- `AUTH_PASSWORD` - Login password (plaintext, hashed at runtime)
- `AUTH_COOKIE_KEY` - Cookie encryption key (optional)

After changing `.env`, restart: `supervisorctl restart meal-planner`

---

## Quick Reference: Common Commands

### Using Makefile (Recommended)

The project includes a Makefile with convenient shortcuts:

```bash
# Production operations
make restart        # Restart app and check logs (most common)
make status         # Check service status
make logs          # View recent error logs
make logs-tail     # Follow error logs in real-time

# Development
make install       # Install dependencies with uv
make lint          # Run linter
make format        # Format code
make test          # Run tests with coverage
make clean         # Clean Python cache files

# Environment
make env-edit      # Edit .env file
make env-show      # Show environment (passwords hidden)

# Help
make help          # Show all available commands
```

### Manual Commands

```bash
# Linting
ruff check lib/ app.py
ruff check --fix lib/ app.py
ruff format lib/ app.py

# Type checking
mypy lib/ app.py

# Testing
pytest
pytest --cov=lib --cov-report=html
pytest -v tests/test_services.py::test_specific_function

# Running the app locally
streamlit run app.py

# Production operations
supervisorctl restart meal-planner
supervisorctl status meal-planner
tail -f /var/log/meal-planner.err.log
```

---

## Remember

You are building **production-quality software**. Every line of code should reflect professional software engineering practices. The extra effort spent on logging, type hints, tests, and following SOLID principles pays off in maintainability, debuggability, and reliability.

**Quality over speed. Simplicity over cleverness. Tests over hope.**

Refer to **[agent.md](./agent.md)** frequently as you work. It's your guide to professional Python development on this project.
