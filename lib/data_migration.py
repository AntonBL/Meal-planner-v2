"""Data Migration - Convert markdown recipe data to JSON.

This module handles the one-time migration from markdown-based storage
to JSON-based storage for recipes, weekly plans, and other data.
"""

import uuid
from datetime import datetime
from pathlib import Path

from lib.constants import RECIPE_SOURCE_GENERATED, RECIPE_SOURCE_LIKED, RECIPE_SOURCE_LOVED
from lib.file_manager import get_data_file_path, load_data_file
from lib.logging_config import get_logger
from lib.recipe_parser import parse_all_recipes
from lib.recipe_store import load_recipes, save_recipes

logger = get_logger(__name__)

# ============================================================================
# MIGRATION FUNCTIONS
# ============================================================================


def migrate_recipes_to_json() -> bool:
    """Migrate all recipes from markdown files to JSON.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if already migrated
        existing_recipes = load_recipes()
        if existing_recipes:
            logger.info("Recipes already migrated to JSON, skipping")
            return True

        logger.info("Starting recipe migration from markdown to JSON")

        all_recipes = []

        # Migrate loved recipes
        try:
            loved_content = load_data_file("loved_recipes")
            loved_recipes = parse_all_recipes(loved_content)
            for recipe in loved_recipes:
                recipe['id'] = str(uuid.uuid4())
                recipe['source'] = RECIPE_SOURCE_LOVED
                recipe['rating'] = recipe.get('rating', 5)  # Loved = 5 stars
                recipe['created_date'] = datetime.now().isoformat()
                recipe['cook_count'] = 0
                recipe['tags'] = ['vegetarian']  # All recipes are vegetarian

                # Ensure ingredients is a list
                if 'ingredients' in recipe and isinstance(recipe['ingredients'], str):
                    recipe['ingredients'] = [i.strip() for i in recipe['ingredients'].split(',')]

                all_recipes.append(recipe)

            logger.info(f"Migrated {len(loved_recipes)} loved recipes")
        except Exception as e:
            logger.warning(f"Could not migrate loved recipes: {e}")

        # Migrate liked recipes
        try:
            liked_content = load_data_file("liked_recipes")
            liked_recipes = parse_all_recipes(liked_content)
            for recipe in liked_recipes:
                recipe['id'] = str(uuid.uuid4())
                recipe['source'] = RECIPE_SOURCE_LIKED
                recipe['rating'] = recipe.get('rating', 4)  # Liked = 4 stars
                recipe['created_date'] = datetime.now().isoformat()
                recipe['cook_count'] = 0
                recipe['tags'] = ['vegetarian']

                # Ensure ingredients is a list
                if 'ingredients' in recipe and isinstance(recipe['ingredients'], str):
                    recipe['ingredients'] = [i.strip() for i in recipe['ingredients'].split(',')]

                all_recipes.append(recipe)

            logger.info(f"Migrated {len(liked_recipes)} liked recipes")
        except Exception as e:
            logger.warning(f"Could not migrate liked recipes: {e}")

        # Migrate generated recipes
        try:
            generated_content = load_data_file("generated_recipes")
            generated_recipes = parse_all_recipes(generated_content)
            for recipe in generated_recipes:
                recipe['id'] = str(uuid.uuid4())
                recipe['source'] = RECIPE_SOURCE_GENERATED
                recipe['rating'] = 0  # Not rated yet
                recipe['created_date'] = datetime.now().isoformat()
                recipe['cook_count'] = 0
                recipe['tags'] = ['vegetarian']

                # Ensure ingredients is a list
                if 'ingredients' in recipe and isinstance(recipe['ingredients'], str):
                    recipe['ingredients'] = [i.strip() for i in recipe['ingredients'].split(',')]

                all_recipes.append(recipe)

            logger.info(f"Migrated {len(generated_recipes)} generated recipes")
        except Exception as e:
            logger.warning(f"Could not migrate generated recipes: {e}")

        # Save to JSON
        if all_recipes:
            success = save_recipes(all_recipes)
            if success:
                logger.info(f"Successfully migrated {len(all_recipes)} total recipes to JSON")
                return True
            else:
                logger.error("Failed to save migrated recipes")
                return False
        else:
            logger.info("No recipes found to migrate")
            # Create empty recipes file
            save_recipes([])
            return True

    except Exception as e:
        logger.error(f"Recipe migration failed: {e}", exc_info=True)
        return False


def backup_markdown_files() -> bool:
    """Create backups of markdown files before deletion.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use direct path construction to avoid "Unknown file type" error
        data_dir = Path(__file__).parent.parent / "data"
        backup_dir = data_dir / "markdown_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        files_to_backup = [
            "loved_recipes",
            "liked_recipes",
            "generated_recipes",
            "weekly_plan",
            "meal_history"
        ]

        for file_type in files_to_backup:
            try:
                source_path = get_data_file_path(file_type)
                if source_path.exists():
                    dest_path = backup_dir / source_path.name
                    dest_path.write_text(source_path.read_text(encoding='utf-8'), encoding='utf-8')
                    logger.info(f"Backed up {source_path.name}")
            except Exception as e:
                logger.warning(f"Could not backup {file_type}: {e}")

        logger.info(f"Created markdown backups in {backup_dir}")
        return True

    except Exception as e:
        logger.error(f"Failed to create backups: {e}", exc_info=True)
        return False


def run_migration() -> bool:
    """Run the complete migration process.

    This is the main entry point for migration. It will:
    1. Check if migration is needed
    2. Backup existing markdown files
    3. Migrate recipes to JSON
    4. Verify migration success

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=== Starting data migration ===")

        # Check if already migrated
        existing_recipes = load_recipes()
        if existing_recipes:
            logger.info("Migration already completed, skipping")
            return True

        # Backup markdown files
        logger.info("Creating backups of markdown files")
        backup_markdown_files()

        # Migrate recipes
        logger.info("Migrating recipes to JSON")
        if not migrate_recipes_to_json():
            logger.error("Recipe migration failed")
            return False

        # Verify migration
        migrated_recipes = load_recipes()
        logger.info(f"Migration complete: {len(migrated_recipes)} recipes in JSON store")

        logger.info("=== Migration completed successfully ===")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False
