# Agent Development Guidelines

**Professional Python Best Practices for AI Recipe Planner**

This document defines the coding standards, architectural principles, and quality practices for this project. These guidelines transform good code into professional, maintainable, production-ready software.

---

## Table of Contents

1. [Core Programming Principles](#core-programming-principles)
2. [Python Code Quality Standards](#python-code-quality-standards)
3. [Logging & Observability](#logging--observability)
4. [Type Safety & Static Analysis](#type-safety--static-analysis)
5. [Testing Philosophy](#testing-philosophy)
6. [Architecture & Design Patterns](#architecture--design-patterns)
7. [Error Handling](#error-handling)
8. [Performance & Optimization](#performance--optimization)
9. [Documentation Standards](#documentation-standards)
10. [Development Workflow](#development-workflow)

---

## Core Programming Principles

### DRY (Don't Repeat Yourself)

> "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." — The Pragmatic Programmer

**Apply DRY by:**
- Extracting common functionality into reusable functions/classes
- Using configuration files for repeated values
- Creating abstractions for repeated patterns
- Avoiding copy-paste programming

**Example:**
```python
# ❌ BAD: Repetitive code
def load_staples():
    with open('data/pantry/staples.md', 'r') as f:
        return f.read()

def load_fresh():
    with open('data/pantry/fresh.md', 'r') as f:
        return f.read()

def load_preferences():
    with open('data/preferences.md', 'r') as f:
        return f.read()

# ✅ GOOD: DRY approach
from pathlib import Path
from typing import Literal

DataFile = Literal['staples', 'fresh', 'shopping_list', 'preferences', 'meal_history']

def load_data_file(file_type: DataFile) -> str:
    """Load a data file from the appropriate location."""
    file_paths = {
        'staples': 'data/pantry/staples.md',
        'fresh': 'data/pantry/fresh.md',
        'shopping_list': 'data/pantry/shopping_list.md',
        'preferences': 'data/preferences.md',
        'meal_history': 'data/meal_history.md',
    }
    return Path(file_paths[file_type]).read_text(encoding='utf-8')
```

### YAGNI (You Aren't Gonna Need It)

> "Always implement things when you actually need them, never when you just foresee that you need them." — Extreme Programming

**Apply YAGNI by:**
- Building features only when required, not "just in case"
- Avoiding premature abstraction
- Removing unused code immediately
- Resisting over-engineering

**Example:**
```python
# ❌ BAD: Over-engineering for hypothetical futures
class RecipeManager:
    def __init__(self, db_connection=None, cache_layer=None, event_bus=None):
        self.db = db_connection  # We're using files, not a DB
        self.cache = cache_layer  # No caching needed yet
        self.events = event_bus   # No event system needed

    def get_recipe(self, id, use_cache=True, emit_event=True):
        # Complex logic we don't need yet
        pass

# ✅ GOOD: Simple, meets current needs
class RecipeManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def get_loved_recipes(self) -> str:
        """Load loved recipes from markdown file."""
        return (self.data_dir / 'recipes' / 'loved.md').read_text()
```

### KISS (Keep It Simple, Stupid)

> "Simplicity is the ultimate sophistication." — Leonardo da Vinci

**Apply KISS by:**
- Preferring simple solutions over clever ones
- Writing code that's easy to understand
- Avoiding unnecessary complexity
- Using clear, descriptive names

### SOLID Principles

#### Single Responsibility Principle (SRP)
Each class/function should have one well-defined purpose.

```python
# ❌ BAD: Multiple responsibilities
class PantryManager:
    def add_item(self, item): ...
    def remove_item(self, item): ...
    def generate_shopping_list(self): ...
    def suggest_recipes(self): ...  # Different responsibility!
    def send_email_notification(self): ...  # Different responsibility!

# ✅ GOOD: Separate responsibilities
class PantryManager:
    """Manages pantry inventory operations."""
    def add_item(self, item: Item) -> None: ...
    def remove_item(self, item_name: str) -> None: ...
    def get_all_items(self) -> list[Item]: ...

class RecipeGenerator:
    """Generates recipe suggestions based on ingredients."""
    def suggest_recipes(self, ingredients: list[str]) -> list[Recipe]: ...

class ShoppingListService:
    """Manages shopping list creation and updates."""
    def generate_shopping_list(self, needed_items: list[str]) -> ShoppingList: ...
```

#### Open/Closed Principle
Classes should be open for extension, closed for modification.

```python
# ✅ GOOD: Extensible design
from abc import ABC, abstractmethod

class DataFileLoader(ABC):
    """Base class for loading different data file formats."""

    @abstractmethod
    def load(self, file_path: Path) -> str:
        pass

class MarkdownLoader(DataFileLoader):
    def load(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')

class JSONLoader(DataFileLoader):
    def load(self, file_path: Path) -> str:
        import json
        with open(file_path) as f:
            return json.dumps(json.load(f))

# Easy to add new loaders without modifying existing code
```

#### Dependency Inversion Principle
Depend on abstractions, not concretions.

```python
# ✅ GOOD: Depend on abstractions
from typing import Protocol

class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def generate(self, prompt: str) -> str: ...

class RecipeGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm  # Depends on protocol, not specific implementation

    def suggest_recipes(self, ingredients: list[str]) -> list[str]:
        prompt = f"Suggest recipes for: {', '.join(ingredients)}"
        return self.llm.generate(prompt)

# Can swap implementations easily
class ClaudeProvider:
    def generate(self, prompt: str) -> str:
        # Claude API implementation
        pass

class OpenAIProvider:
    def generate(self, prompt: str) -> str:
        # OpenAI API implementation
        pass
```

**Sources:**
- [Python Principles Playbook: SOLID to YAGNI Examples](https://medium.com/@ramanbazhanau/python-principles-playbook-from-solid-to-yagni-on-examples-b98445e11c9c)
- [Clean Code and Software Principles](https://medium.com/@burakatestepe/clean-code-and-software-principles-solid-yagni-kiss-dry-807bf0c2e219)
- [Engineering with SOLID, DRY, KISS, YAGNI](https://idatamax.com/blog/engineering-with-solid-dry-kiss-yagni-and-grasp)

---

## Python Code Quality Standards

### Use Modern Python Features (3.9+)

```python
# ✅ Use type hints
def parse_recipe(content: str) -> dict[str, Any]:
    pass

# ✅ Use pathlib over os.path
from pathlib import Path
data_dir = Path('data')
staples = data_dir / 'pantry' / 'staples.md'

# ✅ Use f-strings for formatting
logger.info(f"Loaded {count} recipes from {file_path}")

# ✅ Use dataclasses for data structures
from dataclasses import dataclass

@dataclass
class Recipe:
    name: str
    cuisine: str
    ingredients: list[str]
    rating: int
```

### Naming Conventions (PEP 8)

```python
# Functions and variables: snake_case
def load_recipe_file(file_name: str) -> str:
    recipe_content = ""
    return recipe_content

# Classes: PascalCase
class RecipeManager:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RECIPES = 10
DEFAULT_CUISINE = "italian"

# Private methods/attributes: _leading_underscore
class PantryManager:
    def _validate_item(self, item: str) -> bool:
        pass
```

### Code Organization

```python
# ✅ Group imports properly
# Standard library
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Third-party
import anthropic
import streamlit as st

# Local
from lib.file_manager import load_data_file
from lib.llm_agents import RecipeGenerator
```

---

## Logging & Observability

### NEVER Use Print Statements

> "Print statements are temporary debugging tools, not production code."

**Why logging is superior:**
- ✅ Structured output with levels (DEBUG, INFO, WARNING, ERROR)
- ✅ Automatic timestamps and context
- ✅ Can be disabled/redirected without code changes
- ✅ Thread-safe
- ✅ Integration with monitoring tools

### Structured Logging

```python
# ❌ BAD: Print statements
def load_recipes():
    print("Loading recipes...")
    recipes = load_file('recipes.md')
    print(f"Loaded {len(recipes)} recipes")
    return recipes

# ✅ GOOD: Structured logging
import logging
from typing import Any

logger = logging.getLogger(__name__)

def load_recipes() -> list[dict[str, Any]]:
    """Load recipes from markdown file with proper logging."""
    logger.info("Loading recipes from file", extra={
        "file_path": "data/recipes/loved.md",
        "operation": "load_recipes"
    })

    try:
        recipes = load_file('data/recipes/loved.md')
        logger.info(
            "Successfully loaded recipes",
            extra={
                "recipe_count": len(recipes),
                "operation": "load_recipes"
            }
        )
        return recipes
    except FileNotFoundError as e:
        logger.error(
            "Recipe file not found",
            extra={
                "file_path": "data/recipes/loved.md",
                "error": str(e)
            },
            exc_info=True
        )
        raise
```

### Logging Configuration

```python
# lib/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to stdout for containerization
            logging.FileHandler(Path('logs') / 'app.log')  # Also log to file
        ]
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
```

### Log Levels Guide

```python
# DEBUG: Detailed diagnostic information
logger.debug("LLM prompt constructed", extra={"prompt_length": len(prompt)})

# INFO: General informational messages about program execution
logger.info("Recipe generation started", extra={"cuisine": "italian"})

# WARNING: Something unexpected but not critical
logger.warning("Recipe file missing optional field", extra={"field": "prep_time"})

# ERROR: Error occurred but application can continue
logger.error("Failed to parse recipe", extra={"recipe_name": name}, exc_info=True)

# CRITICAL: Serious error, application may not continue
logger.critical("Cannot connect to LLM API", exc_info=True)
```

**Sources:**
- [Python Logging Best Practices: Complete Guide 2025](https://www.carmatec.com/blog/python-logging-best-practices-complete-guide/)
- [Python Logging Best Practices - SigNoz](https://signoz.io/guides/python-logging-best-practices/)
- [Python logging: basic, better and best](https://www.matthewstrawbridge.com/content/2024/python-logging-basic-better-best/)

---

## Type Safety & Static Analysis

### Type Hints Everywhere

```python
from typing import Optional, Union
from pathlib import Path

# ✅ GOOD: Complete type hints
def load_recipe_file(
    file_path: Path,
    encoding: str = 'utf-8',
    fallback: Optional[str] = None
) -> str:
    """Load recipe from file with proper type safety.

    Args:
        file_path: Path to the recipe file
        encoding: File encoding (default: utf-8)
        fallback: Fallback content if file not found

    Returns:
        Recipe content as string

    Raises:
        FileNotFoundError: If file doesn't exist and no fallback provided
    """
    try:
        return file_path.read_text(encoding=encoding)
    except FileNotFoundError:
        if fallback is not None:
            return fallback
        raise
```

### Modern Type Hints (Python 3.9+)

```python
# ✅ Use built-in generics (Python 3.9+)
def process_recipes(recipes: list[dict[str, str]]) -> dict[str, list[str]]:
    pass

# ✅ Use Union with | operator (Python 3.10+)
def get_cuisine(name: str) -> str | None:
    pass

# ✅ Use Protocol for structural typing
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
    def from_dict(self, data: dict[str, Any]) -> None: ...
```

### Tool Configuration

**pyproject.toml:**
```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
```

### Running Type Checking & Linting

```bash
# Type checking with mypy
mypy lib/ app.py

# Linting with ruff
ruff check lib/ app.py

# Auto-fix with ruff
ruff check --fix lib/ app.py

# Format with ruff
ruff format lib/ app.py
```

**Sources:**
- [A Modern Python Toolkit: Pydantic, Ruff, MyPy, and UV](https://dev.to/devasservice/a-modern-python-toolkit-pydantic-ruff-mypy-and-uv-4b2f)
- [Enhancing Python Code Quality with Ruff, Black, and Mypy](https://www.higherpass.com/2025/04/29/enhancing-python-code-quality-with-ruff-black-and-mypy/)
- [Ruff FAQ](https://docs.astral.sh/ruff/faq/)

---

## Testing Philosophy

### Outcome-Based Testing

> "Test outcomes, not implementation details."

**Focus on:**
- ✅ What the code produces (output)
- ✅ What the code does (behavior)
- ✅ Edge cases and error conditions

**Avoid:**
- ❌ Testing internal implementation details
- ❌ Testing framework code
- ❌ Redundant tests that don't add value

### AAA Pattern (Arrange, Act, Assert)

```python
import pytest
from lib.file_manager import PantryManager

def test_add_item_to_pantry():
    """Test that adding an item updates the pantry file correctly."""
    # Arrange: Set up test data and dependencies
    manager = PantryManager(data_dir=Path("test_data"))
    item = "Chicken breast - 2 lbs"
    expected_content = "Chicken breast - 2 lbs - Added: 2025-11-26"

    # Act: Perform the operation
    manager.add_item(item, category="fresh")

    # Assert: Verify the outcome
    actual_content = (Path("test_data/pantry/fresh.md")).read_text()
    assert expected_content in actual_content
```

### Test Isolation & Independence

```python
import pytest
from pathlib import Path
import shutil

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory for each test."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Copy test fixtures
    (data_dir / "pantry").mkdir()
    (data_dir / "recipes").mkdir()

    yield data_dir

    # Cleanup happens automatically with tmp_path

def test_recipe_loading_isolated(temp_data_dir: Path):
    """Each test gets its own clean data directory."""
    # This test cannot affect other tests
    manager = RecipeManager(temp_data_dir)
    # ... test logic
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch
import pytest

def test_recipe_generation_with_llm_mock():
    """Test recipe generation without calling actual LLM API."""
    # Arrange
    mock_llm = Mock()
    mock_llm.generate.return_value = "Pasta Carbonara\nChicken Stir Fry"

    generator = RecipeGenerator(llm=mock_llm)
    ingredients = ["chicken", "pasta", "eggs"]

    # Act
    recipes = generator.suggest_recipes(ingredients)

    # Assert
    assert len(recipes) == 2
    assert "Pasta Carbonara" in recipes
    mock_llm.generate.assert_called_once()

@patch('lib.llm_agents.anthropic.Anthropic')
def test_recipe_generation_with_api_patch(mock_anthropic):
    """Test with patched Anthropic client."""
    # Configure mock
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value.content = [
        Mock(text="Suggested recipe content")
    ]

    # Test logic here
    pass
```

### Pytest Best Practices

```python
# Use fixtures for reusable test setup
@pytest.fixture
def sample_recipes() -> list[dict]:
    return [
        {"name": "Pasta", "cuisine": "italian", "rating": 5},
        {"name": "Stir Fry", "cuisine": "asian", "rating": 4},
    ]

# Use parametrize for testing multiple cases
@pytest.mark.parametrize("rating,expected_category", [
    (5, "loved"),
    (4, "liked"),
    (3, "liked"),
    (2, "not_again"),
    (1, "not_again"),
])
def test_recipe_categorization(rating: int, expected_category: str):
    """Test recipe categorization based on rating."""
    result = categorize_recipe(rating)
    assert result == expected_category

# Test exceptions properly
def test_invalid_recipe_raises_error():
    """Test that invalid recipe data raises ValueError."""
    with pytest.raises(ValueError, match="Invalid recipe format"):
        parse_recipe("invalid data")
```

### Test Coverage Guidelines

```bash
# Run tests with coverage
pytest --cov=lib --cov-report=html --cov-report=term

# Aim for 80%+ coverage, but focus on critical paths
# 100% coverage doesn't mean bug-free code
```

**Sources:**
- [Python Unit Testing Best Practices For Building Reliable Applications](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/)
- [Effective Python Testing With pytest – Real Python](https://realpython.com/pytest-python-testing/)
- [Python Testing 101 (How To Decide What To Test)](https://pytest-with-eric.com/introduction/python-testing-strategy/)

---

## Avoiding AI-Written Test Weaknesses

> "AI can write tests fast, but fast tests that don't catch bugs are worse than no tests at all."

When using AI to assist with test generation (including yourself as an AI assistant), be aware of common weaknesses and actively work to avoid them.

### Common AI Test Weaknesses

#### 1. Poor Mock Implementation (25% failure rate)

**Problem:** LLMs often create broken mocks that turn unit tests into integration tests.

```python
# ❌ BAD: AI-generated test without proper mocking
def test_suggest_recipes():
    service = RecipeService()  # Creates real dependencies!
    recipes = service.suggest_recipes(['italian'], ['pasta'])
    assert len(recipes) > 0  # Calls real LLM API, hits real files

# ✅ GOOD: Properly mocked dependencies
def test_suggest_recipes_with_mocks(mock_repository, mock_llm):
    """Test recipe suggestion with isolated dependencies."""
    # Arrange: Configure mocks
    mock_repository.get_loved_recipes.return_value = "Sample recipes..."
    mock_llm.generate.return_value = "Pasta Carbonara\nMargherita Pizza"

    service = RecipeService(repository=mock_repository, llm=mock_llm)

    # Act
    recipes = service.suggest_recipes(['italian'], ['pasta', 'eggs'])

    # Assert
    assert len(recipes) == 2
    assert "Pasta Carbonara" in recipes
    mock_llm.generate.assert_called_once()  # Verify interaction
```

**Fix Checklist:**
- [ ] All external dependencies are mocked (APIs, databases, file systems)
- [ ] Mocks are configured with realistic return values
- [ ] Test verifies mocks were called correctly
- [ ] Test runs in milliseconds (not seconds)

#### 2. Inadequate Edge Case Coverage

**Problem:** AI focuses on happy paths, missing edge cases and error conditions.

```python
# ❌ BAD: Only tests happy path
def test_load_recipe():
    recipe = load_recipe_file(Path('data/recipes/loved.md'))
    assert recipe is not None

# ✅ GOOD: Comprehensive edge case coverage
@pytest.mark.parametrize("file_path,expected_error", [
    (Path('nonexistent.md'), FileNotFoundError),
    (Path('/dev/null'), ValueError),  # Empty file
    (Path('malformed.md'), InvalidRecipeFormatError),
])
def test_load_recipe_error_cases(file_path, expected_error):
    """Test error handling for invalid inputs."""
    with pytest.raises(expected_error):
        load_recipe_file(file_path)

def test_load_recipe_with_unicode():
    """Test handling of unicode characters."""
    recipe = load_recipe_file(Path('data/recipes/unicode_test.md'))
    assert '🍝' in recipe  # Emoji in recipe name

def test_load_recipe_very_large_file():
    """Test performance with large files."""
    large_recipe = 'x' * (10 * 1024 * 1024)  # 10MB
    with pytest.raises(ValueError, match="File too large"):
        parse_recipe(large_recipe)
```

**Edge Cases Checklist:**
- [ ] Empty inputs (empty strings, empty lists, None)
- [ ] Boundary values (0, -1, MAX_INT)
- [ ] Invalid types
- [ ] Unicode and special characters
- [ ] Very large inputs
- [ ] Concurrent access (if applicable)
- [ ] Network failures (if applicable)

#### 3. Cryptic Variable Names & Poor Readability

**Problem:** AI-generated tests often have meaningless variable names.

```python
# ❌ BAD: Robotic, unclear test
def test_func():
    obj = Thing()
    result_obj = obj.do_thing(param1, param2)
    assert result_obj.val == expected_val  # What does this test?

# ✅ GOOD: Clear, descriptive test
def test_recipe_service_suggests_italian_when_pasta_available():
    """Test that Italian recipes are suggested when pasta is in pantry."""
    # Arrange
    service = RecipeService(repository=mock_repo, llm=mock_llm)
    available_ingredients = ['pasta', 'tomatoes', 'basil']
    preferred_cuisines = ['italian']

    mock_llm.generate.return_value = "Pasta Marinara"

    # Act
    suggested_recipes = service.suggest_recipes(
        cuisines=preferred_cuisines,
        ingredients=available_ingredients
    )

    # Assert: Verify Italian recipe was suggested
    assert len(suggested_recipes) == 1
    assert "Pasta Marinara" in suggested_recipes[0]
```

**Readability Checklist:**
- [ ] Test name describes what is being tested
- [ ] Variable names are descriptive
- [ ] Comments explain "why", not "what"
- [ ] AAA pattern is clear (Arrange, Act, Assert)
- [ ] Can understand test without reading implementation

#### 4. Testing Implementation Instead of Behavior

**Problem:** AI tests often check internal implementation details instead of public behavior.

```python
# ❌ BAD: Tests implementation details
def test_recipe_parser_uses_regex():
    parser = RecipeParser()
    assert hasattr(parser, '_regex_pattern')  # Who cares?
    assert parser._internal_cache == {}  # Implementation detail

# ✅ GOOD: Tests behavior/outcomes
def test_recipe_parser_extracts_ingredients():
    """Test that parser correctly extracts ingredients from recipe text."""
    # Arrange
    recipe_text = """
    Pasta Carbonara
    Ingredients: pasta, eggs, bacon, parmesan
    """

    # Act
    parsed = RecipeParser().parse(recipe_text)

    # Assert: Verify behavior/outcome
    assert parsed.name == "Pasta Carbonara"
    assert "pasta" in parsed.ingredients
    assert "eggs" in parsed.ingredients
    assert len(parsed.ingredients) == 4
```

**Behavior Testing Checklist:**
- [ ] Tests verify public API, not private methods
- [ ] Tests don't access internal state (_attributes)
- [ ] Tests don't care about implementation details
- [ ] Refactoring code shouldn't break tests
- [ ] Tests describe what the code does, not how

#### 5. Missing Assertions or Weak Assertions

**Problem:** AI sometimes writes tests that don't actually verify anything useful.

```python
# ❌ BAD: Weak or missing assertions
def test_load_recipes():
    recipes = load_all_recipes()
    assert recipes  # Too vague! Tests almost nothing

def test_parse_recipe():
    result = parse_recipe("some text")
    # No assertions at all!

# ✅ GOOD: Strong, specific assertions
def test_load_recipes_returns_all_categories():
    """Test that all recipe categories are loaded."""
    recipes = load_all_recipes()

    # Specific assertions about structure and content
    assert isinstance(recipes, dict)
    assert 'loved' in recipes
    assert 'liked' in recipes
    assert 'not_again' in recipes

    # Verify content
    assert len(recipes['loved']) > 0
    for recipe in recipes['loved']:
        assert 'name' in recipe
        assert 'ingredients' in recipe
        assert 'rating' in recipe
        assert recipe['rating'] == 5  # Loved recipes are 5-star
```

**Assertion Checklist:**
- [ ] Every test has at least one meaningful assertion
- [ ] Assertions are specific, not vague
- [ ] Assertions verify the actual requirement
- [ ] Assertions check types, values, and structure
- [ ] No "assert True" or similar useless assertions

#### 6. Language-Specific Issues

**Problem:** AI performs differently across programming languages.

**Python-Specific Gotchas:**
```python
# ❌ BAD: Doesn't handle Python's dynamic typing
def test_add_item(pantry):
    pantry.add_item("milk")  # What if someone passes an int?

# ✅ GOOD: Tests type validation
def test_add_item_rejects_invalid_types():
    """Test that add_item validates input types."""
    pantry = PantryManager()

    with pytest.raises(TypeError, match="Item must be a string"):
        pantry.add_item(123)  # Invalid type

    with pytest.raises(TypeError):
        pantry.add_item(None)
```

---

### Human Review Checklist for AI-Generated Tests

Before accepting any AI-generated test code, verify:

**Correctness:**
- [ ] Test actually tests the requirement
- [ ] Assertions are meaningful and specific
- [ ] Edge cases are covered
- [ ] Error cases are tested

**Quality:**
- [ ] Proper mocking of external dependencies
- [ ] Fast execution (< 100ms for unit tests)
- [ ] Clear, descriptive names
- [ ] Follows AAA pattern
- [ ] No implementation details tested

**Completeness:**
- [ ] Happy path covered
- [ ] Error paths covered
- [ ] Edge cases covered
- [ ] Boundary conditions covered

**Maintainability:**
- [ ] Future developers can understand it
- [ ] Doesn't rely on implementation details
- [ ] Easy to update when requirements change

---

### Best Practices When Using AI for Tests

1. **Start with requirements, not implementation**
   - Tell AI what behavior to test, not how to test it
   - Provide edge cases explicitly

2. **Review every line**
   - Don't blindly accept AI-generated tests
   - Verify mocks are correct
   - Check assertions are meaningful

3. **Run tests and verify they fail first**
   - Temporarily break the code to ensure test catches it
   - Verify test fails for the right reason

4. **Improve iteratively**
   - Start with AI draft
   - Add edge cases AI missed
   - Improve variable names and clarity
   - Add documentation

5. **Use AI as a starting point, not final solution**
   - AI can scaffold tests quickly
   - Human review is essential for quality
   - Combine AI speed with human insight

---

### Example: From AI-Generated to Professional Test

```python
# AI First Draft (needs improvement)
def test_recipe():
    r = get_recipe("pasta")
    assert r

# After Human Review (professional quality)
def test_get_recipe_returns_loved_pasta_recipe_when_exists():
    """Test that get_recipe returns the correct recipe for 'pasta' query.

    Given: A recipe database with Italian pasta recipes marked as 'loved'
    When: User searches for 'pasta'
    Then: System returns the loved pasta recipe with all required fields
    """
    # Arrange: Set up test database with known recipes
    test_db = RecipeDatabase()
    expected_recipe = Recipe(
        name="Pasta Carbonara",
        cuisine="italian",
        rating=5,
        ingredients=["pasta", "eggs", "bacon", "parmesan"]
    )
    test_db.add_recipe(expected_recipe)

    # Act: Search for pasta recipe
    actual_recipe = test_db.get_recipe("pasta")

    # Assert: Verify correct recipe returned with all fields
    assert actual_recipe is not None, "Recipe should be found"
    assert actual_recipe.name == "Pasta Carbonara"
    assert actual_recipe.rating == 5
    assert len(actual_recipe.ingredients) == 4
    assert "pasta" in actual_recipe.ingredients

def test_get_recipe_returns_none_when_recipe_not_found():
    """Test that get_recipe returns None for non-existent recipes."""
    test_db = RecipeDatabase()

    result = test_db.get_recipe("nonexistent_recipe")

    assert result is None

def test_get_recipe_raises_error_for_invalid_input():
    """Test that get_recipe validates input parameters."""
    test_db = RecipeDatabase()

    with pytest.raises(ValueError, match="Recipe name cannot be empty"):
        test_db.get_recipe("")

    with pytest.raises(TypeError, match="Recipe name must be a string"):
        test_db.get_recipe(None)
```

**Sources:**
- [Unmasking the Flaws: Why AI-Generated Unit Tests Fall Short](https://shekhar14.medium.com/unmasking-the-flaws-why-ai-generated-unit-tests-fall-short-in-real-codebases-71e394581a8e)
- [Unit Test Writing with AI vs. Manual Methods: A Deep Dive](https://zencoder.ai/blog/ai-vs-manual-unit-testing)
- [4 AI Testing Pitfalls and How to Solve Them](https://medium.com/@aiotests/4-ai-testing-pitfalls-and-how-aio-tests-solves-them-55243ef67187)
- [Choosing LLMs to generate high-quality unit tests](https://research.redhat.com/blog/2025/04/21/choosing-llms-to-generate-high-quality-unit-tests-for-code/)

---

## Architecture & Design Patterns

### Repository Pattern

Separate data access logic from business logic.

```python
# lib/repositories.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

class RecipeRepository(Protocol):
    """Protocol for recipe data access."""

    def get_loved_recipes(self) -> str: ...
    def get_liked_recipes(self) -> str: ...
    def save_recipe(self, recipe: str, category: str) -> None: ...

class MarkdownRecipeRepository:
    """File-based repository for recipes stored in markdown."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.recipes_dir = data_dir / "recipes"

    def get_loved_recipes(self) -> str:
        return (self.recipes_dir / "loved.md").read_text(encoding='utf-8')

    def get_liked_recipes(self) -> str:
        return (self.recipes_dir / "liked.md").read_text(encoding='utf-8')

    def save_recipe(self, recipe: str, category: str) -> None:
        file_path = self.recipes_dir / f"{category}.md"
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{recipe}\n")
```

### Service Layer Pattern

Encapsulate business logic in services.

```python
# lib/services.py
from dataclasses import dataclass
from lib.repositories import RecipeRepository
from lib.llm_agents import LLMProvider

@dataclass
class RecipeService:
    """Service for recipe-related business logic."""

    repository: RecipeRepository
    llm: LLMProvider

    def suggest_recipes(
        self,
        cuisines: list[str],
        available_ingredients: list[str]
    ) -> list[str]:
        """Generate recipe suggestions based on preferences and ingredients.

        Args:
            cuisines: List of preferred cuisines
            available_ingredients: Ingredients currently available

        Returns:
            List of suggested recipe descriptions
        """
        # Load existing recipes for context
        loved_recipes = self.repository.get_loved_recipes()

        # Build prompt
        prompt = self._build_recipe_prompt(
            cuisines, available_ingredients, loved_recipes
        )

        # Generate suggestions
        suggestions = self.llm.generate(prompt)

        return self._parse_suggestions(suggestions)

    def _build_recipe_prompt(
        self,
        cuisines: list[str],
        ingredients: list[str],
        context: str
    ) -> str:
        """Build LLM prompt for recipe generation."""
        # Implementation details...
        pass

    def _parse_suggestions(self, raw_output: str) -> list[str]:
        """Parse LLM output into structured recipe list."""
        # Implementation details...
        pass
```

### Dependency Injection

Make dependencies explicit and testable.

```python
# ❌ BAD: Hard-coded dependencies
class RecipeGenerator:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")  # Hard to test
        self.client = anthropic.Anthropic(api_key=self.api_key)  # Hard to mock

# ✅ GOOD: Injected dependencies
class RecipeGenerator:
    def __init__(self, llm_client: LLMProvider):
        self.llm = llm_client  # Easy to test with mocks

# In production code:
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
generator = RecipeGenerator(llm_client=client)

# In tests:
mock_client = Mock(spec=LLMProvider)
generator = RecipeGenerator(llm_client=mock_client)
```

---

## Error Handling

### Fail Fast, Fail Loud

```python
# ✅ Validate inputs early
def add_recipe(name: str, cuisine: str, rating: int) -> None:
    """Add a new recipe with validation."""
    if not name or not name.strip():
        raise ValueError("Recipe name cannot be empty")

    if cuisine not in VALID_CUISINES:
        raise ValueError(f"Invalid cuisine: {cuisine}")

    if not 1 <= rating <= 5:
        raise ValueError(f"Rating must be between 1 and 5, got {rating}")

    # Proceed with valid data
    _save_recipe(name, cuisine, rating)
```

### Use Specific Exceptions

```python
# lib/exceptions.py
class RecipePlannerError(Exception):
    """Base exception for recipe planner errors."""
    pass

class RecipeNotFoundError(RecipePlannerError):
    """Recipe not found in database."""
    pass

class InvalidRecipeFormatError(RecipePlannerError):
    """Recipe file has invalid format."""
    pass

class LLMAPIError(RecipePlannerError):
    """Error communicating with LLM API."""
    pass

# Usage
def load_recipe(recipe_id: str) -> Recipe:
    try:
        content = load_file(f"recipes/{recipe_id}.md")
    except FileNotFoundError:
        raise RecipeNotFoundError(f"Recipe {recipe_id} not found")

    try:
        return parse_recipe(content)
    except ValueError as e:
        raise InvalidRecipeFormatError(f"Invalid format: {e}") from e
```

### Context Managers for Resource Management

```python
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def atomic_write(file_path: Path):
    """Write to file atomically using a temporary file."""
    temp_path = file_path.with_suffix('.tmp')

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yield f
        temp_path.replace(file_path)  # Atomic on POSIX
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

# Usage
with atomic_write(Path('data/pantry/fresh.md')) as f:
    f.write(updated_content)  # Only replaces file if write succeeds
```

---

## Performance & Optimization

### Lazy Loading

```python
from functools import lru_cache
from pathlib import Path

class DataLoader:
    """Lazy-loading data manager."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._cache: dict[str, str] = {}

    @lru_cache(maxsize=128)
    def load_file(self, file_name: str) -> str:
        """Load file with caching."""
        return (self.data_dir / file_name).read_text(encoding='utf-8')
```

### Avoid Premature Optimization

> "Premature optimization is the root of all evil." — Donald Knuth

- ✅ Write clear, correct code first
- ✅ Profile before optimizing
- ✅ Optimize only proven bottlenecks
- ❌ Don't sacrifice readability for micro-optimizations

### Use Generators for Large Data

```python
# ✅ Memory-efficient iteration
def parse_meal_history(file_path: Path) -> Generator[dict, None, None]:
    """Parse meal history line by line (memory efficient)."""
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('###'):
                yield parse_meal_entry(line)
```

---

## Documentation Standards

### Docstrings (Google Style)

```python
def suggest_recipes(
    cuisines: list[str],
    ingredients: list[str],
    max_results: int = 5
) -> list[Recipe]:
    """Generate recipe suggestions based on available ingredients.

    This function uses an LLM to analyze available ingredients and
    user preferences to suggest relevant recipes.

    Args:
        cuisines: List of preferred cuisine types (e.g., ['italian', 'asian'])
        ingredients: Available ingredients in pantry
        max_results: Maximum number of recipes to return (default: 5)

    Returns:
        List of Recipe objects sorted by relevance

    Raises:
        ValueError: If cuisines or ingredients list is empty
        LLMAPIError: If LLM API call fails

    Example:
        >>> recipes = suggest_recipes(
        ...     cuisines=['italian'],
        ...     ingredients=['pasta', 'tomatoes', 'basil']
        ... )
        >>> len(recipes)
        5
    """
    pass
```

### Comments: When and How

```python
# ✅ GOOD: Explain WHY, not WHAT
# Use structured logging to enable cloud-native log aggregation
logger.info("Recipe generated", extra={"recipe_id": recipe.id})

# ❌ BAD: Redundant comment
# Add 1 to counter
counter += 1

# ✅ GOOD: Explain non-obvious business logic
# LLM performs better with recipes in separate sections
# rather than one large list, so we split by category
loved = load_file("recipes/loved.md")
liked = load_file("recipes/liked.md")
```

---

## Development Workflow

### Pre-commit Hooks

**Install pre-commit:**
```bash
pip install pre-commit
```

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### CI/CD Pipeline

**GitHub Actions (.github/workflows/ci.yml):**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with Ruff
        run: ruff check lib/ app.py

      - name: Type check with Mypy
        run: mypy lib/ app.py

      - name: Run tests with coverage
        run: pytest --cov=lib --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## Summary: The Professional Python Checklist

Before committing code, verify:

- [ ] **No print statements** (use logging)
- [ ] **Type hints on all functions**
- [ ] **Docstrings on public functions/classes**
- [ ] **Tests written for new functionality**
- [ ] **Ruff linting passes** (`ruff check --fix`)
- [ ] **Mypy type checking passes** (`mypy .`)
- [ ] **Tests pass** (`pytest`)
- [ ] **Code follows SOLID principles**
- [ ] **No obvious violations of DRY/YAGNI/KISS**
- [ ] **Errors are handled with specific exceptions**
- [ ] **Logging includes structured context**

---

**Remember:** These are guidelines, not absolute rules. Use judgment to apply them appropriately for the situation. The goal is maintainable, professional code—not perfect code.
