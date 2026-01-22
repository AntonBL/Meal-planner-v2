# Programming Patterns & Best Practices

**Practical code patterns from Meal Planner v2 for Plant Tracker**

---

## Table of Contents

1. [Python Code Quality Standards](#python-code-quality-standards)
2. [Logging Patterns](#logging-patterns)
3. [Type Safety Patterns](#type-safety-patterns)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Testing Patterns](#testing-patterns)
6. [Data Access Patterns](#data-access-patterns)
7. [API Integration Patterns](#api-integration-patterns)

---

## Python Code Quality Standards

### Always Use Type Hints

**Pattern:**
```python
from typing import Optional, Protocol
from pathlib import Path
from datetime import datetime

# Function signatures with types
def water_plant(plant_id: str, watered_at: datetime) -> bool:
    """Record a watering event.

    Args:
        plant_id: Unique identifier for the plant
        watered_at: Timestamp when plant was watered

    Returns:
        True if watering was recorded successfully
    """
    pass

# Class with typed attributes
class Plant:
    def __init__(
        self,
        id: str,
        name: str,
        watering_frequency_days: int,
        last_watered: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.watering_frequency_days = watering_frequency_days
        self.last_watered = last_watered

# Protocol for dependency inversion
class ImageAnalyzer(Protocol):
    def analyze(self, image_path: Path) -> dict[str, any]:
        """Analyze plant health from image."""
        ...
```

**Tools to enforce:**
```bash
# Type checking
mypy app/ --strict

# Configure in pyproject.toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = true
strict_equality = true
```

### Use Pathlib, Not String Paths

**Pattern:**
```python
from pathlib import Path

# ✅ GOOD: Using pathlib
def save_plant_image(plant_id: str, image_data: bytes) -> Path:
    """Save plant image to disk."""
    images_dir = Path("data/images")
    images_dir.mkdir(parents=True, exist_ok=True)

    image_path = images_dir / f"{plant_id}.jpg"
    image_path.write_bytes(image_data)

    return image_path

# ❌ BAD: Using string concatenation
def save_plant_image_bad(plant_id: str, image_data: bytes) -> str:
    import os
    images_dir = "data/images"
    os.makedirs(images_dir, exist_ok=True)

    image_path = os.path.join(images_dir, f"{plant_id}.jpg")
    with open(image_path, 'wb') as f:
        f.write(image_data)

    return image_path
```

**Benefits of pathlib:**
- Cross-platform (Windows/Unix)
- Cleaner syntax
- Built-in operations (mkdir, read_text, etc.)

### Use Structured Logging

**Pattern:**
```python
import logging

logger = logging.getLogger(__name__)

def analyze_plant_health(plant_id: str, image_path: Path) -> dict:
    """Analyze plant health from image."""
    logger.info(
        "Starting plant health analysis",
        extra={
            "plant_id": plant_id,
            "image_path": str(image_path),
            "image_size_bytes": image_path.stat().st_size
        }
    )

    try:
        # Analysis logic
        result = perform_analysis(image_path)

        logger.info(
            "Plant health analysis completed",
            extra={
                "plant_id": plant_id,
                "health_status": result['status'],
                "confidence": result['confidence']
            }
        )

        return result

    except Exception as e:
        logger.error(
            "Plant health analysis failed",
            extra={
                "plant_id": plant_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise
```

**Configure logging:**
```python
# lib/logging_config.py
import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log')
        ]
    )
```

---

## Logging Patterns

### Pattern: Structured Context

**Always log with context:**
```python
# ✅ GOOD: Rich context
logger.info(
    "Watering reminder sent",
    extra={
        "plant_id": plant.id,
        "plant_name": plant.name,
        "notification_type": "push",
        "scheduled_time": scheduled_time.isoformat(),
        "user_id": user.id
    }
)

# ❌ BAD: No context
logger.info("Reminder sent")
```

### Pattern: Log Levels

**Use appropriate log levels:**
```python
# DEBUG: Detailed information for debugging
logger.debug(
    "Fetching plant details",
    extra={"plant_id": plant_id, "include_history": include_history}
)

# INFO: General informational messages
logger.info(
    "Plant watered successfully",
    extra={"plant_id": plant_id, "watered_at": watered_at.isoformat()}
)

# WARNING: Something unexpected but not critical
logger.warning(
    "Plant overdue for watering",
    extra={"plant_id": plant_id, "days_overdue": days_overdue}
)

# ERROR: An error occurred
logger.error(
    "Failed to send watering reminder",
    extra={"plant_id": plant_id, "error": str(e)},
    exc_info=True  # Include stack trace
)
```

---

## Type Safety Patterns

### Pattern: Literal Types for Fixed Options

**Use Literal for type-safe enums:**
```python
from typing import Literal

# Define valid options
HealthStatus = Literal['healthy', 'needs_attention', 'critical']
NotificationType = Literal['local', 'push']

def update_plant_health(
    plant_id: str,
    status: HealthStatus  # Only accepts valid statuses
) -> bool:
    """Update plant health status."""
    # Type checker ensures status is one of: 'healthy', 'needs_attention', 'critical'
    pass

# This will fail type checking:
# update_plant_health("plant-123", "sick")  # ❌ Type error
```

### Pattern: Optional Types

**Use Optional for nullable values:**
```python
from typing import Optional
from datetime import datetime

class Plant:
    def __init__(
        self,
        id: str,
        name: str,
        last_watered: Optional[datetime] = None,  # May be None
        notes: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.last_watered = last_watered
        self.notes = notes

def get_plant(plant_id: str) -> Optional[Plant]:
    """Get plant by ID, returns None if not found."""
    plants = load_plants()
    return next((p for p in plants if p.id == plant_id), None)

# Usage
plant = get_plant("plant-123")
if plant:  # Type checker knows to check for None
    print(plant.name)
else:
    print("Plant not found")
```

### Pattern: Protocol for Duck Typing

**Define interfaces with Protocol:**
```python
from typing import Protocol
from pathlib import Path

class ImageAnalyzer(Protocol):
    """Protocol for plant health image analyzers."""

    def analyze_health(self, image_path: Path) -> dict[str, any]:
        """Analyze plant health from image."""
        ...

class ClaudeVisionAnalyzer:
    """Analyzes plant health using Claude Vision API."""

    def analyze_health(self, image_path: Path) -> dict[str, any]:
        # Claude-specific implementation
        return {
            'status': 'healthy',
            'confidence': 0.95,
            'issues': []
        }

class LocalMLAnalyzer:
    """Analyzes plant health using local ML model."""

    def analyze_health(self, image_path: Path) -> dict[str, any]:
        # Local ML implementation
        return {
            'status': 'needs_attention',
            'confidence': 0.87,
            'issues': ['yellowing_leaves']
        }

# Service accepts any ImageAnalyzer
class PlantHealthService:
    def __init__(self, analyzer: ImageAnalyzer):
        self.analyzer = analyzer  # Type-safe, works with any implementation
```

---

## Error Handling Patterns

### Pattern: Custom Exceptions

**Define domain-specific exceptions:**
```python
# lib/exceptions.py

class PlantTrackerError(Exception):
    """Base exception for plant tracker errors."""
    pass

class PlantNotFoundError(PlantTrackerError):
    """Raised when a plant is not found."""

    def __init__(self, plant_id: str):
        self.plant_id = plant_id
        super().__init__(f"Plant not found: {plant_id}")

class InvalidWateringFrequencyError(PlantTrackerError):
    """Raised when watering frequency is invalid."""

    def __init__(self, frequency: int):
        self.frequency = frequency
        super().__init__(f"Invalid watering frequency: {frequency} (must be >= 1)")

class ImageProcessingError(PlantTrackerError):
    """Raised when image processing fails."""
    pass
```

**Use custom exceptions:**
```python
from lib.exceptions import PlantNotFoundError, InvalidWateringFrequencyError

def add_plant(name: str, watering_frequency_days: int) -> Plant:
    """Add a new plant."""
    # Validate inputs
    if watering_frequency_days < 1:
        raise InvalidWateringFrequencyError(watering_frequency_days)

    if not name.strip():
        raise ValueError("Plant name cannot be empty")

    # Create plant
    plant = Plant(
        id=str(uuid.uuid4()),
        name=name,
        watering_frequency_days=watering_frequency_days
    )

    return plant

def get_plant(plant_id: str) -> Plant:
    """Get plant by ID."""
    plant = plant_repo.find_by_id(plant_id)

    if not plant:
        raise PlantNotFoundError(plant_id)

    return plant
```

### Pattern: Fail Fast Validation

**Validate early, fail fast:**
```python
def schedule_watering_reminder(
    plant_id: str,
    reminder_time: datetime,
    notification_type: NotificationType
) -> bool:
    """Schedule a watering reminder."""

    # Validate all inputs first (fail fast)
    if not plant_id.strip():
        raise ValueError("Plant ID cannot be empty")

    if reminder_time < datetime.now():
        raise ValueError("Reminder time must be in the future")

    if notification_type not in ['local', 'push']:
        raise ValueError(f"Invalid notification type: {notification_type}")

    # All inputs valid, proceed with business logic
    plant = get_plant(plant_id)
    notification_service.schedule(plant, reminder_time, notification_type)

    logger.info(
        "Watering reminder scheduled",
        extra={
            "plant_id": plant_id,
            "reminder_time": reminder_time.isoformat(),
            "notification_type": notification_type
        }
    )

    return True
```

### Pattern: Graceful Error Handling in API

**Handle errors gracefully in FastAPI:**
```python
from fastapi import HTTPException, status

@app.post("/plants/{plant_id}/water")
async def water_plant(plant_id: str, watered_at: datetime):
    """Record a watering event."""
    try:
        result = plant_service.record_watering(plant_id, watered_at)
        return {"success": True, "next_watering": result.next_watering_date}

    except PlantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(
            "Unexpected error recording watering",
            extra={"plant_id": plant_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

---

## Testing Patterns

### Pattern: AAA (Arrange, Act, Assert)

**Structure tests clearly:**
```python
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

def test_record_watering_updates_last_watered_date():
    """Test that recording a watering updates the last watered date."""
    # Arrange
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = Plant(
        id="plant-123",
        name="Monstera",
        watering_frequency_days=7,
        last_watered=None
    )

    service = PlantService(plant_repo=mock_repo)
    watered_at = datetime(2025, 1, 15, 10, 0, 0)

    # Act
    result = service.record_watering("plant-123", watered_at)

    # Assert
    assert result.success is True
    mock_repo.update.assert_called_once()
    updated_plant = mock_repo.update.call_args[0][0]
    assert updated_plant.last_watered == watered_at
```

### Pattern: Fixtures for Test Data

**Use pytest fixtures:**
```python
import pytest
from datetime import datetime

@pytest.fixture
def sample_plant():
    """Sample plant for testing."""
    return Plant(
        id="plant-123",
        name="Monstera Deliciosa",
        watering_frequency_days=7,
        last_watered=datetime(2025, 1, 10)
    )

@pytest.fixture
def mock_plant_repository():
    """Mock plant repository."""
    repo = Mock()
    repo.load_all.return_value = []
    repo.save.return_value = True
    return repo

@pytest.fixture
def plant_service(mock_plant_repository):
    """Plant service with mocked dependencies."""
    return PlantService(plant_repo=mock_plant_repository)

# Use fixtures in tests
def test_add_plant(plant_service, mock_plant_repository):
    """Test adding a new plant."""
    # Arrange
    name = "Pothos"
    frequency = 5

    # Act
    plant = plant_service.add_plant(name, frequency)

    # Assert
    assert plant.name == name
    assert plant.watering_frequency_days == frequency
    mock_plant_repository.save.assert_called_once()
```

### Pattern: Test Outcomes, Not Implementation

**Focus on behavior, not implementation details:**
```python
# ✅ GOOD: Testing outcomes
def test_watering_reminder_scheduled_for_correct_date(plant_service):
    """Test that watering reminder is scheduled for the correct date."""
    # Arrange
    plant = Plant(id="p1", name="Monstera", watering_frequency_days=7)
    watered_at = datetime(2025, 1, 15)

    # Act
    result = plant_service.record_watering(plant.id, watered_at)

    # Assert - test the outcome
    expected_next_watering = datetime(2025, 1, 22)
    assert result.next_watering_date == expected_next_watering

# ❌ BAD: Testing implementation details
def test_watering_calls_repository_update(plant_service, mock_repo):
    """Test that watering calls repository update method."""
    # This is too coupled to implementation
    plant_service.record_watering("p1", datetime.now())

    # Testing internal calls is brittle
    mock_repo.update.assert_called_once()
    assert mock_repo.update.call_args[0][0].id == "p1"
```

### Pattern: Parametrized Tests

**Test multiple scenarios efficiently:**
```python
import pytest

@pytest.mark.parametrize(
    "frequency_days,last_watered,expected_next",
    [
        (7, datetime(2025, 1, 1), datetime(2025, 1, 8)),
        (3, datetime(2025, 1, 10), datetime(2025, 1, 13)),
        (14, datetime(2025, 1, 15), datetime(2025, 1, 29)),
    ]
)
def test_next_watering_date_calculation(
    frequency_days,
    last_watered,
    expected_next
):
    """Test next watering date calculation for various frequencies."""
    plant = Plant(
        id="p1",
        name="Test Plant",
        watering_frequency_days=frequency_days,
        last_watered=last_watered
    )

    next_watering = plant.calculate_next_watering_date()

    assert next_watering == expected_next
```

---

## Data Access Patterns

### Pattern: Repository with JSON Storage

**Centralized JSON data access:**
```python
import json
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

class PlantRepository:
    """Repository for plant data storage using JSON."""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> list[Plant]:
        """Load all plants from JSON."""
        if not self.data_path.exists():
            return []

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            plants = [Plant(**p) for p in data.get('plants', [])]
            logger.info(f"Loaded {len(plants)} plants")
            return plants

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plants JSON: {e}", exc_info=True)
            return []

    def save_all(self, plants: list[Plant]) -> bool:
        """Save all plants to JSON."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'plants': [p.to_dict() for p in plants]
            }

            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(plants)} plants")
            return True

        except Exception as e:
            logger.error(f"Failed to save plants: {e}", exc_info=True)
            return False

    def find_by_id(self, plant_id: str) -> Optional[Plant]:
        """Find plant by ID."""
        plants = self.load_all()
        return next((p for p in plants if p.id == plant_id), None)

    def save(self, plant: Plant) -> bool:
        """Save or update a single plant."""
        plants = self.load_all()

        # Update existing or add new
        existing_index = next(
            (i for i, p in enumerate(plants) if p.id == plant.id),
            None
        )

        if existing_index is not None:
            plants[existing_index] = plant
            logger.info(f"Updated plant: {plant.name}")
        else:
            plants.append(plant)
            logger.info(f"Added new plant: {plant.name}")

        return self.save_all(plants)

    def delete(self, plant_id: str) -> bool:
        """Delete a plant by ID."""
        plants = self.load_all()
        original_count = len(plants)

        plants = [p for p in plants if p.id != plant_id]

        if len(plants) == original_count:
            logger.warning(f"Plant not found for deletion: {plant_id}")
            return False

        logger.info(f"Deleted plant: {plant_id}")
        return self.save_all(plants)
```

### Pattern: Data Models with to_dict/from_dict

**Serialization helpers:**
```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Plant:
    """Plant data model."""
    id: str
    name: str
    species: Optional[str]
    watering_frequency_days: int
    last_watered: Optional[datetime] = None
    health_status: str = "healthy"
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO string
        if self.last_watered:
            data['last_watered'] = self.last_watered.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Plant':
        """Create Plant from dictionary."""
        # Convert ISO string to datetime
        if data.get('last_watered'):
            data['last_watered'] = datetime.fromisoformat(data['last_watered'])
        return cls(**data)

    def needs_watering(self) -> bool:
        """Check if plant needs watering."""
        if not self.last_watered:
            return True

        days_since_watered = (datetime.now() - self.last_watered).days
        return days_since_watered >= self.watering_frequency_days
```

---

## API Integration Patterns

### Pattern: LLM Provider with Protocol

**Abstraction for LLM providers:**
```python
from typing import Protocol
import anthropic
import os

class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt."""
        ...

class ClaudeProvider:
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or "claude-sonnet-4-5-20250929"

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Claude API."""
        logger.info(
            "Calling Claude API",
            extra={
                "model": self.model,
                "prompt_length": len(prompt),
                "max_tokens": max_tokens
            }
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            logger.info(
                "Claude API call successful",
                extra={"response_length": len(response_text)}
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude API call failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

# Usage
def analyze_plant_health_with_llm(image_path: Path, llm: LLMProvider) -> dict:
    """Analyze plant health using LLM."""
    prompt = f"Analyze the health of the plant in this image: {image_path}"
    response = llm.generate(prompt)
    return parse_health_response(response)
```

### Pattern: Retry Logic for External APIs

**Retry failed API calls:**
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """Retry function with exponential backoff."""
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()

        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"All {max_retries} retry attempts failed",
                    extra={"error": str(e)},
                    exc_info=True
                )
                raise

            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {delay}s",
                extra={"error": str(e)}
            )
            time.sleep(delay)
            delay *= backoff_factor

# Usage
def call_vision_api(image_path: Path) -> dict:
    """Call vision API with retry logic."""
    def api_call():
        return claude_vision.analyze(image_path)

    return retry_with_backoff(api_call, max_retries=3)
```

---

## Quick Reference Checklist

When writing code, ensure:

- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Using `pathlib.Path` instead of string paths
- [ ] Using `logging` instead of `print()`
- [ ] Logging includes structured context (extra={})
- [ ] Custom exceptions for domain errors
- [ ] Input validation (fail fast)
- [ ] Tests follow AAA pattern
- [ ] Tests use fixtures for setup
- [ ] Tests focus on outcomes, not implementation
- [ ] Code passes `mypy` type checking
- [ ] Code passes `ruff` linting

---

## Next Steps

1. Review `03-fastapi-backend-guide.md` for FastAPI-specific patterns
2. Check `04-swiftui-frontend-guide.md` for iOS patterns
3. Read `05-claude-collaboration.md` for working with Claude Code
