#!/usr/bin/env python3
"""Manual migration script to convert markdown recipes to JSON.

Run this script to manually trigger the data migration:
    uv run python scripts/migrate_to_json.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.data_migration import run_migration
from lib.logging_config import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("Recipe Data Migration: Markdown → JSON")
    print("=" * 60)
    print()
    
    print("This will:")
    print("  1. Backup existing markdown files to data/markdown_backup/")
    print("  2. Parse all recipes from markdown files")
    print("  3. Create data/recipes.json with structured data")
    print()
    
    response = input("Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)
    
    print()
    print("Starting migration...")
    print("-" * 60)
    
    success = run_migration()
    
    print("-" * 60)
    
    if success:
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("  - Check data/recipes.json to see your recipes")
        print("  - Backups are in data/markdown_backup/")
        print("  - Run the app: uv run streamlit run app.py")
        sys.exit(0)
    else:
        print()
        print("❌ Migration failed. Check logs for details.")
        print("Your original markdown files are safe.")
        sys.exit(1)
