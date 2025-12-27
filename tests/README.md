# Tests for Meal Planner v2

This directory contains pytest tests for the meal planner application, focusing on the new shopping list features.

## Running Tests

### Setup

Install test dependencies using uv:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install pytest pytest-mock
```

### Run All Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test ingredient parser
python -m pytest tests/test_ingredient_parser.py -v

# Test shopping list manager
python -m pytest tests/test_shopping_list_manager.py -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=lib --cov-report=html
```

## Test Structure

### `conftest.py`
Shared fixtures and test configuration:
- `mock_llm`: Mock LLM provider for testing without API calls
- `sample_ingredients`: Test ingredient data
- `sample_shopping_list_data`: Test shopping list data

### `test_ingredient_parser.py` (15 tests)
Tests for ingredient parsing and manipulation:
- **Name normalization**: Plural removal, lowercase conversion
- **Fuzzy matching**: Similar ingredient detection
- **Ingredient combination**: Quantity summing, unit handling
- **Formatting**: Display string generation
- **LLM integration**: Parsing with mocked LLM

### `test_shopping_list_manager.py` (9 tests)
Tests for shopping list manager functions:
- **Combined list**: Ingredient combination across recipes
- **Grouped list**: Organizing by store sections
- **Error handling**: Graceful fallbacks
- **Integration**: Full workflow tests

## Test Coverage

Current test coverage focuses on core functionality:
- ✅ Ingredient parsing (Haiku LLM)
- ✅ Fuzzy name matching
- ✅ Quantity combination
- ✅ Store section grouping
- ✅ Error handling and fallbacks

## Writing New Tests

When adding new features, follow these patterns:

1. **Unit tests**: Test individual functions in isolation
2. **Integration tests**: Test multiple components working together
3. **Mock external dependencies**: Use `@patch` for LLM calls, file I/O
4. **Use fixtures**: Share test data via `conftest.py`

Example test:

```python
from unittest.mock import patch

@patch('lib.ingredient_parser.get_fast_model')
def test_new_feature(mock_model):
    """Test description."""
    # Setup
    mock_model.return_value.generate.return_value = "mock response"

    # Execute
    result = some_function()

    # Assert
    assert result == expected_value
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    uv pip install pytest pytest-mock
    pytest tests/ -v
```
