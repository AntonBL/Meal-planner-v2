#!/usr/bin/env python3
"""Verification script for weekly plan migration.

Run this script to trigger the weekly plan migration and verify it works:
    uv run python scripts/verify_weekly_plan_migration.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.weekly_plan_manager import load_current_plan, _get_weekly_plan_path
from lib.logging_config import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("Verifying Weekly Plan Migration")
    print("=" * 60)
    
    # 1. Trigger migration by loading the plan
    print("\n1. Loading current plan (triggers migration)...")
    plan = load_current_plan()
    print(f"   Loaded {len(plan)} meals.")
    
    # 2. Check if JSON file exists
    print("\n2. Checking for weekly_plan.json...")
    json_path = _get_weekly_plan_path()
    if json_path.exists():
        print(f"   ✅ File created at: {json_path}")
        
        # 3. Verify content
        print("\n3. Verifying JSON content...")
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print(f"   Meals in JSON: {len(data.get('current_plan', []))}")
        print(f"   History items: {len(data.get('history', []))}")
        
        if len(plan) == len(data.get('current_plan', [])):
            print("\n✅ Verification SUCCESS!")
        else:
            print("\n❌ Verification FAILED: Mismatch in meal counts.")
    else:
        print("\n❌ Verification FAILED: JSON file not created.")
