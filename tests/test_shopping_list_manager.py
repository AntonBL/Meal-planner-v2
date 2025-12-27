"""Tests for shopping list manager - core functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lib.shopping_list_manager import (
    add_items_to_list,
    get_combined_shopping_list,
    get_grouped_shopping_list,
)


class TestCombinedShoppingList:
    """Test combined shopping list functionality."""

    @patch('lib.shopping_list_manager.load_shopping_list')
    @patch('lib.shopping_list_manager.combine_ingredients')
    def test_combines_structured_items(self, mock_combine, mock_load):
        """Test that structured items are combined."""
        mock_load.return_value = [
            {
                "item": "mushrooms (16 oz)",
                "structured": {"name": "mushrooms", "quantity": 16.0, "unit": "oz"},
                "recipe": "Recipe A",
                "category": "Fresh Produce"
            },
            {
                "item": "mushrooms (6 oz)",
                "structured": {"name": "mushrooms", "quantity": 6.0, "unit": "oz"},
                "recipe": "Recipe B",
                "category": "Fresh Produce"
            }
        ]

        mock_combine.return_value = [
            {"name": "mushrooms", "quantity": 22.0, "unit": "oz"}
        ]

        result = get_combined_shopping_list()

        # Should call combine_ingredients with structured data
        mock_combine.assert_called_once()

        # Should return combined results
        assert len(result) > 0

    @patch('lib.shopping_list_manager.load_shopping_list')
    def test_handles_empty_list(self, mock_load):
        """Test handling of empty shopping list."""
        mock_load.return_value = []

        result = get_combined_shopping_list()

        assert result == []

    @patch('lib.shopping_list_manager.load_shopping_list')
    def test_handles_items_without_structured_data(self, mock_load):
        """Test handling of legacy items without structured data."""
        mock_load.return_value = [
            {
                "item": "old format item",
                "recipe": "Recipe A",
                "category": "Other"
            }
        ]

        result = get_combined_shopping_list()

        # Should return original items if no structured data
        assert len(result) > 0

    @patch('lib.shopping_list_manager.load_shopping_list')
    @patch('lib.shopping_list_manager.combine_ingredients')
    @patch('lib.shopping_list_manager.format_ingredient')
    def test_adds_recipe_metadata(self, mock_format, mock_combine, mock_load):
        """Test that recipe information is preserved."""
        mock_load.return_value = [
            {
                "item": "mushrooms",
                "structured": {"name": "mushrooms", "quantity": 10.0, "unit": "oz"},
                "recipe": "Recipe A",
                "category": "Fresh Produce"
            },
            {
                "item": "mushrooms",
                "structured": {"name": "mushrooms", "quantity": 10.0, "unit": "oz"},
                "recipe": "Recipe B",
                "category": "Fresh Produce"
            }
        ]

        mock_combine.return_value = [
            {"name": "mushrooms", "quantity": 20.0, "unit": "oz"}
        ]

        mock_format.return_value = "20 oz mushrooms"

        result = get_combined_shopping_list()

        # Should have recipe count
        assert result[0].get('recipe_count') == 2
        assert 'recipes' in result[0]


class TestGroupedShoppingList:
    """Test grouped shopping list functionality."""

    @patch('lib.shopping_list_manager.get_combined_shopping_list')
    def test_groups_by_category(self, mock_combined):
        """Test that items are grouped by category."""
        mock_combined.return_value = [
            {
                "item": "mushrooms",
                "category": "Fresh Produce",
                "structured": {"name": "mushrooms"}
            },
            {
                "item": "spinach",
                "category": "Fresh Produce",
                "structured": {"name": "spinach"}
            },
            {
                "item": "butter",
                "category": "Dairy & Eggs",
                "structured": {"name": "butter"}
            }
        ]

        result = get_grouped_shopping_list()

        # Should have 2 categories
        assert len(result) == 2
        assert "Fresh Produce" in result
        assert "Dairy & Eggs" in result

        # Fresh Produce should have 2 items
        assert len(result["Fresh Produce"]) == 2

        # Dairy should have 1 item
        assert len(result["Dairy & Eggs"]) == 1

    @patch('lib.shopping_list_manager.get_combined_shopping_list')
    def test_category_ordering(self, mock_combined):
        """Test that categories are ordered logically."""
        mock_combined.return_value = [
            {"item": "butter", "category": "Dairy & Eggs"},
            {"item": "mushrooms", "category": "Fresh Produce"},
            {"item": "pasta", "category": "Grains & Pasta"},
        ]

        result = get_grouped_shopping_list()

        # Fresh Produce should come before Dairy in the order
        categories = list(result.keys())
        fresh_index = categories.index("Fresh Produce")
        dairy_index = categories.index("Dairy & Eggs")

        assert fresh_index < dairy_index  # Fresh Produce first

    @patch('lib.shopping_list_manager.get_combined_shopping_list')
    def test_handles_empty_combined_list(self, mock_combined):
        """Test handling of empty combined list."""
        mock_combined.return_value = []

        result = get_grouped_shopping_list()

        # Should return empty dict or handle gracefully
        assert isinstance(result, dict)

    @patch('lib.shopping_list_manager.get_combined_shopping_list')
    def test_handles_errors_gracefully(self, mock_combined):
        """Test that errors are handled gracefully."""
        mock_combined.side_effect = Exception("Test error")

        result = get_grouped_shopping_list()

        # Should fall back to something reasonable
        assert isinstance(result, dict)


class TestAddItemsToList:
    """Test adding items to shopping list with duplicate detection."""

    @patch('lib.shopping_list_manager._load_list_data')
    @patch('lib.shopping_list_manager._save_list_data')
    @patch('lib.shopping_list_manager.get_ingredient_parser')
    @patch('lib.shopping_list_manager.categorize_ingredient')
    def test_adds_similar_ingredients_with_same_unit(self, mock_categorize, mock_parser_getter, mock_save, mock_load):
        """Test adding 'tomato' then 'tomatoes' combines quantities (same unit)."""
        # Setup
        mock_categorize.return_value = "Fresh Produce"
        mock_save.return_value = True

        # Mock parser
        mock_parser = Mock()
        mock_parser_getter.return_value = mock_parser

        # First call: "4 tomato" -> parsed as {name: "tomato", quantity: 4, unit: null}
        mock_parser.parse.return_value = {
            "name": "tomato",
            "quantity": 4.0,
            "unit": None,
            "modifier": None,
            "prep_method": None
        }

        # Existing list is empty
        mock_load.return_value = {"items": [], "last_updated": None}

        # Add "4 tomato"
        result = add_items_to_list("Manual Additions", ["4 tomato"])
        assert result is True

        # Get the items that were saved
        first_call_items = mock_save.call_args[0][0]["items"]
        assert len(first_call_items) == 1
        assert first_call_items[0]["structured"]["quantity"] == 4.0

        # Second call: "10 tomatoes" -> parsed as {name: "tomatoes", quantity: 10, unit: null}
        mock_parser.parse.return_value = {
            "name": "tomatoes",
            "quantity": 10.0,
            "unit": None,
            "modifier": None,
            "prep_method": None
        }

        # Now the list has the first item
        mock_load.return_value = {"items": first_call_items, "last_updated": None}

        # Add "10 tomatoes"
        result = add_items_to_list("Manual Additions", ["10 tomatoes"])
        assert result is True

        # Get the items after second add
        second_call_items = mock_save.call_args[0][0]["items"]

        # Should still be 1 item (combined, not 2 separate)
        assert len(second_call_items) == 1

        # Quantity should be 4 + 10 = 14
        assert second_call_items[0]["structured"]["quantity"] == 14.0

    @patch('lib.shopping_list_manager._load_list_data')
    @patch('lib.shopping_list_manager._save_list_data')
    @patch('lib.shopping_list_manager.get_ingredient_parser')
    @patch('lib.shopping_list_manager.categorize_ingredient')
    def test_keeps_separate_with_different_units(self, mock_categorize, mock_parser_getter, mock_save, mock_load):
        """Test adding '4 tomatoes' (count) and '10 oz tomatoes' (weight) stays separate."""
        # Setup
        mock_categorize.return_value = "Fresh Produce"
        mock_save.return_value = True

        mock_parser = Mock()
        mock_parser_getter.return_value = mock_parser

        # First: "4 tomatoes" (no unit)
        mock_parser.parse.return_value = {
            "name": "tomatoes",
            "quantity": 4.0,
            "unit": None,
            "modifier": None,
            "prep_method": None
        }

        mock_load.return_value = {"items": [], "last_updated": None}

        add_items_to_list("Manual Additions", ["4 tomatoes"])
        first_items = mock_save.call_args[0][0]["items"]

        # Second: "10 oz tomatoes" (weight unit)
        mock_parser.parse.return_value = {
            "name": "tomatoes",
            "quantity": 10.0,
            "unit": "oz",
            "modifier": None,
            "prep_method": None
        }

        mock_load.return_value = {"items": first_items, "last_updated": None}

        add_items_to_list("Manual Additions", ["10 oz tomatoes"])
        second_items = mock_save.call_args[0][0]["items"]

        # Should be 2 separate items (different units)
        assert len(second_items) == 2
        assert second_items[0]["structured"]["unit"] is None
        assert second_items[0]["structured"]["quantity"] == 4.0
        assert second_items[1]["structured"]["unit"] == "oz"
        assert second_items[1]["structured"]["quantity"] == 10.0

    @patch('lib.shopping_list_manager._load_list_data')
    @patch('lib.shopping_list_manager._save_list_data')
    @patch('lib.shopping_list_manager.get_ingredient_parser')
    @patch('lib.shopping_list_manager.categorize_ingredient')
    def test_keeps_separate_for_different_recipes(self, mock_categorize, mock_parser_getter, mock_save, mock_load):
        """Test same ingredient for different recipes stays separate."""
        # Setup
        mock_categorize.return_value = "Fresh Produce"
        mock_save.return_value = True

        mock_parser = Mock()
        mock_parser_getter.return_value = mock_parser

        mock_parser.parse.return_value = {
            "name": "mushrooms",
            "quantity": 8.0,
            "unit": "oz",
            "modifier": None,
            "prep_method": None
        }

        # Add to Recipe A
        mock_load.return_value = {"items": [], "last_updated": None}
        add_items_to_list("Recipe A", ["8 oz mushrooms"])
        first_items = mock_save.call_args[0][0]["items"]

        # Add same ingredient to Recipe B
        mock_load.return_value = {"items": first_items, "last_updated": None}
        add_items_to_list("Recipe B", ["8 oz mushrooms"])
        second_items = mock_save.call_args[0][0]["items"]

        # Should be 2 separate items (different recipes)
        assert len(second_items) == 2
        assert second_items[0]["recipe"] == "Recipe A"
        assert second_items[1]["recipe"] == "Recipe B"


class TestShoppingListManagerIntegration:
    """Integration tests for shopping list manager."""

    def test_full_workflow_with_sample_data(self, sample_shopping_list_data):
        """Test the full workflow from loading to grouping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create shopping list file
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()
            list_file = data_dir / "shopping_list.json"

            with open(list_file, 'w') as f:
                json.dump(sample_shopping_list_data, f)

            # Patch the path function
            with patch('lib.shopping_list_manager._get_shopping_list_path', return_value=list_file):
                grouped = get_grouped_shopping_list()

                # Should have some categories
                assert len(grouped) > 0

                # Should have Fresh Produce (mushrooms and spinach)
                if "Fresh Produce" in grouped:
                    assert len(grouped["Fresh Produce"]) >= 1

                # Should have Dairy & Eggs (butter)
                if "Dairy & Eggs" in grouped:
                    assert len(grouped["Dairy & Eggs"]) >= 1
