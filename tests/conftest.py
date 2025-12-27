"""Pytest configuration and shared fixtures."""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider for testing."""
    mock = Mock()

    def generate_response(prompt: str, max_tokens: int = 2000) -> str:
        """Mock generate method that returns structured JSON for ingredients."""
        # Parse ingredient parsing requests
        if "Parse this ingredient" in prompt and '"name":' in prompt:
            # Extract the ingredient from prompt
            if "2 cups fresh spinach" in prompt:
                return json.dumps({
                    "name": "spinach",
                    "quantity": 2.0,
                    "unit": "cups",
                    "modifier": "fresh",
                    "prep_method": None
                })
            elif "mushrooms (16 oz)" in prompt:
                return json.dumps({
                    "name": "mushrooms",
                    "quantity": 16.0,
                    "unit": "oz",
                    "modifier": None,
                    "prep_method": None
                })
            elif "3-4 medium tomatoes" in prompt:
                return json.dumps({
                    "name": "tomatoes",
                    "quantity": 3.5,
                    "unit": None,
                    "modifier": "medium",
                    "prep_method": None
                })
            elif "1/2 lb butter" in prompt:
                return json.dumps({
                    "name": "butter",
                    "quantity": 0.5,
                    "unit": "lb",
                    "modifier": None,
                    "prep_method": None
                })
            elif "fresh ginger (2-inch piece)" in prompt:
                return json.dumps({
                    "name": "ginger",
                    "quantity": 2.0,
                    "unit": "inch",
                    "modifier": "fresh",
                    "prep_method": None
                })
            else:
                # Default fallback for unknown ingredients
                return json.dumps({
                    "name": "unknown",
                    "quantity": 1.0,
                    "unit": None,
                    "modifier": None,
                    "prep_method": None
                })

        # Categorization requests
        elif "Categorize this ingredient" in prompt:
            if any(veg in prompt.lower() for veg in ['spinach', 'mushroom', 'tomato', 'onion', 'ginger', 'garlic']):
                return "Fresh Produce"
            elif any(dairy in prompt.lower() for dairy in ['butter', 'milk', 'cheese', 'yogurt']):
                return "Dairy & Eggs"
            else:
                return "Other"

        return "Mock response"

    mock.generate.side_effect = generate_response
    return mock


@pytest.fixture
def sample_ingredients():
    """Sample ingredient data for testing."""
    return [
        {
            "name": "mushroom",
            "quantity": 16.0,
            "unit": "oz",
            "modifier": "fresh",
            "prep_method": None
        },
        {
            "name": "mushrooms",
            "quantity": 6.0,
            "unit": "oz",
            "modifier": "fresh",
            "prep_method": "sliced"
        },
        {
            "name": "tomato",
            "quantity": 3.0,
            "unit": None,
            "modifier": "ripe",
            "prep_method": None
        },
        {
            "name": "tomatoes",
            "quantity": 2.0,
            "unit": None,
            "modifier": "ripe",
            "prep_method": "diced"
        },
        {
            "name": "onion",
            "quantity": 1.0,
            "unit": None,
            "modifier": "yellow",
            "prep_method": "chopped"
        }
    ]


@pytest.fixture
def sample_shopping_list_data():
    """Sample shopping list data for testing."""
    return {
        "items": [
            {
                "item": "mushrooms (16 oz)",
                "structured": {
                    "name": "mushrooms",
                    "quantity": 16.0,
                    "unit": "oz",
                    "modifier": "fresh",
                    "prep_method": None
                },
                "recipe": "Spicy Mushroom Curry",
                "added": "2025-12-14",
                "checked": False,
                "category": "Fresh Produce"
            },
            {
                "item": "mushrooms (6 oz)",
                "structured": {
                    "name": "mushrooms",
                    "quantity": 6.0,
                    "unit": "oz",
                    "modifier": "fresh",
                    "prep_method": None
                },
                "recipe": "Italian Risotto",
                "added": "2025-12-14",
                "checked": False,
                "category": "Fresh Produce"
            },
            {
                "item": "2 cups fresh spinach",
                "structured": {
                    "name": "spinach",
                    "quantity": 2.0,
                    "unit": "cups",
                    "modifier": "fresh",
                    "prep_method": None
                },
                "recipe": "Spicy Mushroom Curry",
                "added": "2025-12-14",
                "checked": False,
                "category": "Fresh Produce"
            },
            {
                "item": "butter",
                "structured": {
                    "name": "butter",
                    "quantity": 0.5,
                    "unit": "lb",
                    "modifier": None,
                    "prep_method": None
                },
                "recipe": "Manual Additions",
                "added": "2025-12-14",
                "checked": False,
                "category": "Dairy & Eggs"
            }
        ],
        "last_updated": "2025-12-14T23:34:17.402942"
    }


@pytest.fixture
def mock_shopping_list_file(tmp_path, sample_shopping_list_data):
    """Create a temporary shopping list JSON file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    shopping_list_path = data_dir / "shopping_list.json"
    with open(shopping_list_path, 'w') as f:
        json.dump(sample_shopping_list_data, f)

    return shopping_list_path


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch, tmp_path):
    """Set environment variables for testing."""
    # Mock API key for tests
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("MODEL_SMART", "claude-sonnet-4-5-20250929")
    monkeypatch.setenv("MODEL_FAST", "claude-haiku-4-5")
