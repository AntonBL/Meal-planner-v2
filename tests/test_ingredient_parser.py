"""Tests for ingredient parser - core functionality."""

import json
from unittest.mock import Mock, patch

import pytest

from lib.ingredient_parser import (
    format_ingredient,
    normalize_name,
    fuzzy_match,
    combine_ingredients,
)


class TestNormalizeName:
    """Test ingredient name normalization."""

    def test_plural_removal(self):
        """Test that plurals are normalized to singular."""
        assert normalize_name("mushrooms") == "mushroom"
        assert normalize_name("tomatoes") == "tomato"  # -es ending removed
        assert normalize_name("berries") == "berry"

    def test_lowercase_conversion(self):
        """Test that names are converted to lowercase."""
        assert normalize_name("ONION") == "onion"
        assert normalize_name("Spinach") == "spinach"


class TestFuzzyMatch:
    """Test fuzzy matching logic."""

    def test_exact_match_after_normalization(self):
        """Test that similar names match after normalization."""
        assert fuzzy_match("mushroom", "mushrooms") is True
        assert fuzzy_match("tomato", "tomatoes") is True

    def test_different_ingredients_dont_match(self):
        """Test that different ingredients don't match."""
        assert fuzzy_match("mushroom", "spinach") is False
        assert fuzzy_match("onion", "garlic") is False

    def test_case_insensitive(self):
        """Test that matching is case insensitive."""
        assert fuzzy_match("Mushroom", "mushrooms") is True
        assert fuzzy_match("ONION", "onions") is True


class TestCombineIngredients:
    """Test ingredient combination logic."""

    def test_combines_matching_ingredients(self, sample_ingredients):
        """Test that duplicate ingredients are combined."""
        combined = combine_ingredients(sample_ingredients)

        # Should combine mushroom + mushrooms, tomato + tomatoes
        # But keep onion separate
        assert len(combined) == 3  # mushrooms, tomatoes, onion

    def test_sums_quantities(self):
        """Test that quantities are summed correctly."""
        ingredients = [
            {"name": "mushroom", "quantity": 16.0, "unit": "oz", "modifier": None, "prep_method": None},
            {"name": "mushrooms", "quantity": 6.0, "unit": "oz", "modifier": None, "prep_method": None}
        ]

        combined = combine_ingredients(ingredients)

        assert len(combined) == 1
        assert combined[0]["quantity"] == 22.0
        assert combined[0]["unit"] == "oz"

    def test_keeps_prep_method(self):
        """Test that prep methods are preserved."""
        ingredients = [
            {"name": "tomato", "quantity": 2.0, "unit": None, "modifier": None, "prep_method": "diced"},
            {"name": "tomatoes", "quantity": 3.0, "unit": None, "modifier": None, "prep_method": "diced"}
        ]

        combined = combine_ingredients(ingredients)

        assert combined[0]["prep_method"] == "diced"

    def test_different_units_dont_combine(self):
        """Test that ingredients with different units don't combine."""
        ingredients = [
            {"name": "mushroom", "quantity": 1.0, "unit": "cup", "modifier": None, "prep_method": None},
            {"name": "mushrooms", "quantity": 16.0, "unit": "oz", "modifier": None, "prep_method": None}
        ]

        combined = combine_ingredients(ingredients)

        # Should NOT combine because units are different
        assert len(combined) == 2


class TestFormatIngredient:
    """Test ingredient formatting."""

    def test_format_with_quantity_and_unit(self):
        """Test formatting ingredient with quantity and unit."""
        ing = {"name": "spinach", "quantity": 2.0, "unit": "cups", "modifier": "fresh", "prep_method": None}
        formatted = format_ingredient(ing)

        assert "2" in formatted
        assert "cups" in formatted
        assert "fresh" in formatted
        assert "spinach" in formatted

    def test_format_with_prep_method(self):
        """Test formatting ingredient with prep method."""
        ing = {"name": "onion", "quantity": 1.0, "unit": None, "modifier": None, "prep_method": "chopped"}
        formatted = format_ingredient(ing)

        assert "onion" in formatted
        assert "chopped" in formatted

    def test_format_integer_quantity(self):
        """Test that integer quantities are formatted without decimals."""
        ing = {"name": "tomato", "quantity": 3.0, "unit": None, "modifier": None, "prep_method": None}
        formatted = format_ingredient(ing)

        assert "3 tomato" in formatted
        assert "3.0" not in formatted


class TestIngredientParserIntegration:
    """Integration tests for ingredient parser with mocked LLM."""

    @patch('lib.ingredient_parser.get_fast_model')
    def test_parse_ingredient_with_llm(self, mock_get_model, mock_llm):
        """Test parsing ingredient with mocked LLM."""
        from lib.ingredient_parser import IngredientParser

        mock_get_model.return_value = mock_llm

        parser = IngredientParser()
        result = parser.parse("2 cups fresh spinach")

        assert result["name"] == "spinach"
        assert result["quantity"] == 2.0
        assert result["unit"] == "cups"
        assert result["modifier"] == "fresh"

    @patch('lib.ingredient_parser.get_fast_model')
    def test_parse_handles_markdown_code_blocks(self, mock_get_model):
        """Test that parser handles JSON wrapped in markdown code blocks."""
        from lib.ingredient_parser import IngredientParser

        mock_llm = Mock()
        mock_llm.generate.return_value = '```json\n{"name": "test", "quantity": 1.0}\n```'
        mock_get_model.return_value = mock_llm

        parser = IngredientParser()
        result = parser.parse("test ingredient")

        # Should successfully parse despite markdown wrapper
        assert "name" in result

    @patch('lib.ingredient_parser.get_fast_model')
    def test_parse_fallback_on_error(self, mock_get_model):
        """Test that parser falls back gracefully on LLM errors."""
        from lib.ingredient_parser import IngredientParser
        from lib.exceptions import LLMAPIError

        mock_llm = Mock()
        # Raise LLMAPIError which is caught by the parser
        mock_llm.generate.side_effect = LLMAPIError("API Error")
        mock_get_model.return_value = mock_llm

        parser = IngredientParser()
        result = parser.parse("test ingredient")

        # Should return fallback structure with lowercased name
        assert result["name"] == "test ingredient"
        assert result["quantity"] is None
