#!/usr/bin/env python3
"""Verification script for shopping list migration.

Run this script to trigger the shopping list migration and verify it works:
    uv run python scripts/verify_shopping_list_migration.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.shopping_list_manager import load_shopping_list, _get_shopping_list_path
from lib.logging_config import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("Verifying Shopping List Migration")
    print("=" * 60)
    
    # 1. Trigger migration by loading the list
    print("\n1. Loading current list (triggers migration)...")
    items = load_shopping_list()
    print(f"   Loaded {len(items)} items.")
    
    # 2. Check if JSON file exists
    print("\n2. Checking for shopping_list.json...")
    json_path = _get_shopping_list_path()
    if json_path.exists():
        print(f"   ✅ File created at: {json_path}")
        
        # 3. Verify content
        print("\n3. Verifying JSON content...")
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print(f"   Items in JSON: {len(data.get('items', []))}")
        
        if len(items) == len(data.get('items', [])):
            print("\n✅ Verification SUCCESS!")
        else:
            print("\n❌ Verification FAILED: Mismatch in item counts.")
    else:
        print("\n❌ Verification FAILED: JSON file not created.")
