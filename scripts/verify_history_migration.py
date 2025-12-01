#!/usr/bin/env python3
"""Verification script for meal history migration.

Run this script to trigger the meal history migration and verify it works:
    uv run python scripts/verify_history_migration.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.history_manager import load_meal_history, _get_history_path
from lib.logging_config import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("Verifying Meal History Migration")
    print("=" * 60)
    
    # 1. Trigger migration by loading history
    print("\n1. Loading meal history (triggers migration)...")
    meals = load_meal_history()
    print(f"   Loaded {len(meals)} meals.")
    
    # 2. Check if JSON file exists
    print("\n2. Checking for meal_history.json...")
    json_path = _get_history_path()
    if json_path.exists():
        print(f"   ✅ File created at: {json_path}")
        
        # 3. Verify content
        print("\n3. Verifying JSON content...")
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print(f"   Meals in JSON: {len(data.get('meals', []))}")
        
        if len(meals) == len(data.get('meals', [])):
            print("\n✅ Verification SUCCESS!")
        else:
            print("\n❌ Verification FAILED: Mismatch in meal counts.")
    else:
        print("\n❌ Verification FAILED: JSON file not created.")
