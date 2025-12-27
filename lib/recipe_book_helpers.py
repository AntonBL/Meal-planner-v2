"""Recipe Book Helpers - Utility functions for organizing and filtering recipes."""

from datetime import datetime, timedelta
from typing import Dict, List


def get_recipe_collections(recipes: list[dict]) -> dict:
    """Organize recipes into auto-generated collections.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        Dictionary with collections organized by cuisine, rating, and special categories
    """
    collections = {
        'by_cuisine': {},
        'by_rating': {
            '5_stars': [],
            '4_plus': [],
            '3_plus': []
        },
        'special': {
            'all': recipes,
            'recent': [],
            'popular': [],
            'never_cooked': [],
            'quick': []
        }
    }

    # By cuisine
    for recipe in recipes:
        cuisine = recipe.get('cuisine')
        if cuisine and cuisine.strip():
            cuisine = cuisine.strip()
        else:
            cuisine = 'Uncategorized'

        if cuisine not in collections['by_cuisine']:
            collections['by_cuisine'][cuisine] = []
        collections['by_cuisine'][cuisine].append(recipe)

    # By rating
    for recipe in recipes:
        rating = recipe.get('rating', 0)
        try:
            rating = int(rating) if rating is not None else 0
        except (ValueError, TypeError):
            rating = 0

        if rating >= 5:
            collections['by_rating']['5_stars'].append(recipe)
        if rating >= 4:
            collections['by_rating']['4_plus'].append(recipe)
        if rating >= 3:
            collections['by_rating']['3_plus'].append(recipe)

    # Special collections
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    for recipe in recipes:
        # Recent (added to book in last 7 days)
        added_to_book = recipe.get('added_to_book')
        if added_to_book:
            try:
                added_dt = datetime.fromisoformat(added_to_book)
                if added_dt >= week_ago:
                    collections['special']['recent'].append(recipe)
            except:
                pass

        # Popular (cooked 3+ times)
        cook_count = recipe.get('cook_count', 0)
        try:
            cook_count = int(cook_count) if cook_count is not None else 0
        except (ValueError, TypeError):
            cook_count = 0

        if cook_count >= 3:
            collections['special']['popular'].append(recipe)

        # Never cooked
        if cook_count == 0:
            collections['special']['never_cooked'].append(recipe)

        # Quick (under 30 minutes)
        time = recipe.get('time_minutes', 999)
        try:
            time = int(time) if time is not None else 999
        except (ValueError, TypeError):
            time = 999

        if time < 30:
            collections['special']['quick'].append(recipe)

    return collections


def get_unique_cuisines(recipes: list[dict]) -> list[str]:
    """Extract unique cuisines from recipes, sorted alphabetically.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        Sorted list of unique cuisine names, with 'Uncategorized' at the end
    """
    cuisines = set()
    has_uncategorized = False

    for recipe in recipes:
        cuisine = recipe.get('cuisine')
        if cuisine and cuisine.strip():
            cuisines.add(cuisine.strip())
        else:
            has_uncategorized = True

    cuisine_list = sorted(list(cuisines))

    # Add Uncategorized at the end if there are any recipes without cuisine
    if has_uncategorized:
        cuisine_list.append('Uncategorized')

    return cuisine_list


def calculate_avg_rating(recipes: list[dict]) -> float:
    """Calculate average rating across recipes.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        Average rating (0.0 if no ratings exist)
    """
    ratings = []
    for r in recipes:
        rating = r.get('rating', 0)
        try:
            rating_val = int(rating) if rating is not None else 0
            if rating_val > 0:
                ratings.append(rating_val)
        except (ValueError, TypeError):
            continue

    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def sort_recipes(recipes: list[dict], sort_by: str) -> list[dict]:
    """Sort recipes by specified criteria.

    Args:
        recipes: List of recipe dictionaries
        sort_by: Sort criterion ("Name (A-Z)", "Rating (High-Low)",
                "Recently Added", "Cook Count")

    Returns:
        Sorted list of recipes
    """
    if sort_by == "Name (A-Z)":
        return sorted(recipes, key=lambda r: str(r.get('name', '')).lower())

    elif sort_by == "Rating (High-Low)":
        def safe_rating(r):
            rating = r.get('rating', 0)
            try:
                return int(rating) if rating is not None else 0
            except (ValueError, TypeError):
                return 0
        return sorted(recipes, key=safe_rating, reverse=True)

    elif sort_by == "Recently Added":
        def safe_date(r):
            added = r.get('added_to_book', '')
            # Return empty string if None, otherwise convert to string
            return str(added) if added else ''
        return sorted(recipes, key=safe_date, reverse=True)

    elif sort_by == "Cook Count":
        def safe_count(r):
            count = r.get('cook_count', 0)
            try:
                return int(count) if count is not None else 0
            except (ValueError, TypeError):
                return 0
        return sorted(recipes, key=safe_count, reverse=True)

    return recipes


def filter_recipes(
    recipes: list[dict],
    cuisine: str = None,
    min_rating: int = 0,
    max_time: int = None,
    search_query: str = None
) -> list[dict]:
    """Filter recipes based on various criteria.

    Args:
        recipes: List of recipe dictionaries
        cuisine: Filter by cuisine type (None = all cuisines)
        min_rating: Minimum rating (0 = all ratings)
        max_time: Maximum cooking time in minutes (None = no limit)
        search_query: Search in name, description, tags (None = no search)

    Returns:
        Filtered list of recipes
    """
    filtered = recipes

    # Cuisine filter
    if cuisine and cuisine != "All":
        if cuisine == "Uncategorized":
            filtered = [r for r in filtered if not r.get('cuisine') or not str(r.get('cuisine')).strip()]
        else:
            filtered = [r for r in filtered if str(r.get('cuisine', '')) == cuisine]

    # Rating filter
    if min_rating > 0:
        def has_min_rating(r):
            rating = r.get('rating', 0)
            try:
                return int(rating) if rating is not None else 0
            except (ValueError, TypeError):
                return 0
        filtered = [r for r in filtered if has_min_rating(r) >= min_rating]

    # Time filter
    if max_time:
        def get_time(r):
            time = r.get('time_minutes', 999)
            try:
                return int(time) if time is not None else 999
            except (ValueError, TypeError):
                return 999
        filtered = [r for r in filtered if get_time(r) <= max_time]

    # Search query
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            r for r in filtered
            if (query_lower in str(r.get('name', '')).lower() or
                query_lower in str(r.get('description', '')).lower() or
                any(query_lower in str(tag).lower() for tag in r.get('tags', [])))
        ]

    return filtered
