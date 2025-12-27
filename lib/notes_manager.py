"""Notes Manager - Centralized notes storage for improvements and bugs.

This module manages user notes for tracking improvements and bugs,
similar to a simple issue tracker.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)


def _get_notes_path() -> Path:
    """Get the path to the notes JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "notes.json"


def load_notes() -> List[Dict]:
    """Load notes from JSON storage.

    Returns:
        List of note dictionaries
    """
    try:
        notes_path = _get_notes_path()

        if not notes_path.exists():
            logger.info("Notes file doesn't exist, creating empty notes list")
            save_notes([])
            return []

        with open(notes_path, encoding='utf-8') as f:
            data = json.load(f)

        notes = data.get('notes', [])
        logger.info(f"Loaded {len(notes)} notes from JSON")
        return notes

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse notes JSON: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Failed to load notes: {e}", exc_info=True)
        return []


def save_notes(notes: List[Dict]) -> bool:
    """Save notes to JSON storage.

    Args:
        notes: List of note dictionaries

    Returns:
        True if successful, False otherwise
    """
    try:
        notes_path = _get_notes_path()
        notes_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'notes': notes,
            'last_updated': datetime.now().isoformat()
        }

        with open(notes_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(notes)} notes to JSON")
        return True

    except Exception as e:
        logger.error(f"Failed to save notes: {e}", exc_info=True)
        return False


def add_note(title: str, description: str, note_type: str = "improvement") -> Optional[str]:
    """Add a new note.

    Args:
        title: Note title
        description: Note description/details
        note_type: Type of note ("improvement" or "bug")

    Returns:
        Note ID if successful, None otherwise
    """
    try:
        notes = load_notes()

        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        new_note = {
            'id': note_id,
            'title': title,
            'description': description,
            'type': note_type,
            'status': 'open',
            'created_at': now,
            'updated_at': now
        }

        notes.append(new_note)

        if save_notes(notes):
            logger.info(f"Added note: {note_id}")
            return note_id
        return None

    except Exception as e:
        logger.error(f"Failed to add note: {e}", exc_info=True)
        return None


def update_note(note_id: str, title: Optional[str] = None,
                description: Optional[str] = None,
                note_type: Optional[str] = None,
                status: Optional[str] = None) -> bool:
    """Update an existing note.

    Args:
        note_id: ID of note to update
        title: New title (optional)
        description: New description (optional)
        note_type: New type (optional)
        status: New status (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        notes = load_notes()

        for note in notes:
            if note['id'] == note_id:
                if title is not None:
                    note['title'] = title
                if description is not None:
                    note['description'] = description
                if note_type is not None:
                    note['type'] = note_type
                if status is not None:
                    note['status'] = status

                note['updated_at'] = datetime.now().isoformat()

                if save_notes(notes):
                    logger.info(f"Updated note: {note_id}")
                    return True
                return False

        logger.warning(f"Note not found: {note_id}")
        return False

    except Exception as e:
        logger.error(f"Failed to update note: {e}", exc_info=True)
        return False


def delete_note(note_id: str) -> bool:
    """Delete a note.

    Args:
        note_id: ID of note to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        notes = load_notes()
        original_count = len(notes)

        notes = [note for note in notes if note['id'] != note_id]

        if len(notes) < original_count:
            if save_notes(notes):
                logger.info(f"Deleted note: {note_id}")
                return True
        else:
            logger.warning(f"Note not found: {note_id}")

        return False

    except Exception as e:
        logger.error(f"Failed to delete note: {e}", exc_info=True)
        return False


def get_notes_by_type(note_type: str) -> List[Dict]:
    """Get all notes of a specific type.

    Args:
        note_type: Type to filter by ("improvement" or "bug")

    Returns:
        List of matching notes
    """
    notes = load_notes()
    return [note for note in notes if note['type'] == note_type]


def get_notes_by_status(status: str) -> List[Dict]:
    """Get all notes with a specific status.

    Args:
        status: Status to filter by ("open", "in_progress", or "done")

    Returns:
        List of matching notes
    """
    notes = load_notes()
    return [note for note in notes if note['status'] == status]
