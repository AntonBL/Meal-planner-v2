"""Pantry Management Functions.

Shared functions for managing the pantry using JSON storage.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger

logger = get_logger(__name__)


def _get_pantry_path() -> Path:
    """Get the path to the pantry JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "pantry.json"


def _load_pantry_data() -> dict:
    """Load the full pantry data structure from JSON."""
    pantry_path = _get_pantry_path()
    if not pantry_path.exists():
        return {"items": [], "last_updated": None}
    
    try:
        with open(pantry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse pantry JSON: {e}")
        return {"items": [], "last_updated": None}


def _save_pantry_data(data: dict) -> bool:
    """Save the full pantry data structure to JSON."""
    try:
        pantry_path = _get_pantry_path()
        data["last_updated"] = datetime.now().isoformat()
        
        with open(pantry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save pantry JSON: {e}")
        return False


def _parse_markdown_line(line: str) -> dict:
    """Parse a markdown pantry item line."""
    # Format: - Item Name - Quantity - Added: YYYY-MM-DD - Expires: YYYY-MM-DD
    # Or: - Item Name (simple)
    
    text = line.strip()
    if text.startswith('- '):
        text = text[2:]
        
    parts = [p.strip() for p in text.split(' - ')]
    
    item = {
        "id": str(uuid.uuid4()),
        "name": parts[0],
        "quantity": "1",
        "added": datetime.now().strftime("%Y-%m-%d"),
        "expiry": None
    }
    
    if len(parts) > 1:
        # Try to identify parts
        for part in parts[1:]:
            if part.startswith("Added:"):
                item["added"] = part.replace("Added:", "").strip()
            elif part.startswith("Expires:"):
                item["expiry"] = part.replace("Expires:", "").strip()
            else:
                # Assume quantity if not a date field
                item["quantity"] = part
                
    return item


def _migrate_markdown_pantry_if_needed():
    """Migrate legacy markdown pantry files to JSON if JSON doesn't exist."""
    json_path = _get_pantry_path()
    if json_path.exists():
        return

    try:
        logger.info("Migrating pantry from markdown to JSON...")
        items = []
        
        # Files to migrate
        files = [
            ("fresh", "fresh"),
            ("staples", "staple")
        ]
        
        for file_key, item_type in files:
            md_path = get_data_file_path(file_key)
            if not md_path.exists():
                continue
                
            content = md_path.read_text(encoding="utf-8")
            current_section = "Uncategorized"
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('##'):
                    current_section = line.replace('##', '').strip()
                elif line.startswith('-'):
                    item = _parse_markdown_line(line)
                    item["category"] = current_section
                    item["type"] = item_type
                    items.append(item)

        # Save to JSON
        data = {
            "items": items,
            "last_updated": datetime.now().isoformat()
        }
        _save_pantry_data(data)
        logger.info(f"Migrated {len(items)} items to pantry.json")

    except Exception as e:
        logger.error(f"Failed to migrate pantry: {e}", exc_info=True)


def load_pantry_items() -> List[Dict]:
    """Load all pantry items.

    Returns:
        List of item dictionaries
    """
    _migrate_markdown_pantry_if_needed()
    data = _load_pantry_data()
    return data.get("items", [])


def add_pantry_item(item_data: dict) -> bool:
    """Add an item to the pantry.

    Args:
        item_data: Dictionary with name, category, quantity, etc.

    Returns:
        True if successful
    """
    try:
        data = _load_pantry_data()
        items = data.get("items", [])
        
        # Ensure ID
        if "id" not in item_data:
            item_data["id"] = str(uuid.uuid4())
            
        # Ensure added date
        if "added" not in item_data:
            item_data["added"] = datetime.now().strftime("%Y-%m-%d")
            
        items.append(item_data)
        data["items"] = items
        
        if _save_pantry_data(data):
            logger.info(f"Added pantry item: {item_data.get('name')}")
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to add pantry item: {e}", exc_info=True)
        return False


def remove_pantry_item(item_id: str) -> bool:
    """Remove an item from the pantry by ID.

    Args:
        item_id: UUID of the item

    Returns:
        True if successful
    """
    try:
        data = _load_pantry_data()
        items = data.get("items", [])
        
        initial_count = len(items)
        items = [i for i in items if i.get("id") != item_id]
        
        if len(items) == initial_count:
            logger.warning(f"Item not found for removal: {item_id}")
            return False
            
        data["items"] = items
        
        if _save_pantry_data(data):
            logger.info(f"Removed pantry item: {item_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to remove pantry item: {e}", exc_info=True)
        return False


def update_pantry_item(item_id: str, updates: dict) -> bool:
    """Update an item in the pantry.

    Args:
        item_id: UUID of the item
        updates: Dictionary of fields to update

    Returns:
        True if successful
    """
    try:
        data = _load_pantry_data()
        items = data.get("items", [])
        
        found = False
        for item in items:
            if item.get("id") == item_id:
                item.update(updates)
                found = True
                break
                
        if not found:
            return False
            
        data["items"] = items
        return _save_pantry_data(data)

    except Exception as e:
        logger.error(f"Failed to update pantry item: {e}", exc_info=True)
        return False
