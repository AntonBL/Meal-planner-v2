#!/usr/bin/env python3
"""Verification script for pantry migration.

Run this script to trigger the pantry migration and verify it works:
    uv run python scripts/verify_pantry_migration.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.pantry_manager import load_pantry_items, _get_pantry_path
from lib.logging_config import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("Verifying Pantry Migration")
    print("=" * 60)
    
    # 1. Trigger migration by loading items
    print("\n1. Loading pantry items (triggers migration)...")
    items = load_pantry_items()
    print(f"   Loaded {len(items)} items.")
    
    # 2. Check if JSON file exists
    print("\n2. Checking for pantry.json...")
    json_path = _get_pantry_path()
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
