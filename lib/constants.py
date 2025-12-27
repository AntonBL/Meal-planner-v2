"""Application-wide constants.

Centralizes magic strings and configuration values to maintain consistency
and make updates easier.
"""

# ============================================================================
# RECIPE SOURCES
# ============================================================================

RECIPE_SOURCE_GENERATED = "Generated"
RECIPE_SOURCE_LOVED = "Loved"
RECIPE_SOURCE_LIKED = "Liked"
RECIPE_SOURCE_NOT_AGAIN = "Not Again"
RECIPE_SOURCE_CAPTURED = "Captured"

# ============================================================================
# RATING THRESHOLDS
# ============================================================================

# Recipes rated 5 stars go to loved collection
RATING_LOVED_THRESHOLD = 5

# Recipes rated 3-4 stars go to liked collection
RATING_LIKED_THRESHOLD = 3

# Recipes below 3 stars go to not_again collection
