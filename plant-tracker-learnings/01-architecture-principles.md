# Architecture Principles for Plant Tracker App

**Learnings from Meal Planner v2 Applied to Plant Health Tracking**

---

## Overview

This document captures the architectural principles and patterns that worked well in the Meal Planner v2 project and should be applied to the Plant Tracker app (SwiftUI + FastAPI).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Design Principles](#design-principles)
3. [Layer Separation](#layer-separation)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Key Learnings](#key-learnings)

---

## System Architecture

### Recommended Stack for Plant Tracker

```
┌─────────────────────────────────────────┐
│         SwiftUI iOS App                 │
│  • UI + Navigation                      │
│  • Camera / Photo Library               │
│  • Local/Push Notifications             │
│  • Keychain (token storage)             │
│  • Offline-first capability             │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTPS / REST API
                  │
┌─────────────────▼───────────────────────┐
│      Python FastAPI Backend             │
│  • REST endpoints                       │
│  • Business logic                       │
│  • Image processing / ML                │
│  • Database (SQLite/Postgres)           │
│  • Authentication (JWT)                 │
└─────────────────────────────────────────┘
```

### Why This Architecture?

**Separation of Concerns:**
- **SwiftUI handles**: Native iOS features (camera, notifications, widgets)
- **FastAPI handles**: Data persistence, complex logic, ML/image processing
- **Benefit**: Use each platform's strengths; keep complex logic in Python where you're faster

**Offline-First Capability:**
- Start with local storage on device (SwiftData/CoreData)
- Add API sync later without major refactoring
- Users can track plants even without internet

---

## Design Principles

### 1. SOLID Principles

#### Single Responsibility Principle (SRP)
> Each class/module should have one reason to change

**Example from Meal Planner:**
```python
# ❌ BAD: RecipeManager does too much
class RecipeManager:
    def generate_recipe(self):
        # Calls LLM
        # Parses response
        # Saves to file
        # Updates UI state
        pass

# ✅ GOOD: Separated responsibilities
class RecipeGenerator:
    """Handles LLM interaction for recipe generation."""
    def generate(self, ingredients: list[str]) -> str:
        pass

class RecipeParser:
    """Parses LLM responses into structured data."""
    def parse(self, raw_text: str) -> Recipe:
        pass

class RecipeRepository:
    """Handles recipe storage and retrieval."""
    def save(self, recipe: Recipe) -> bool:
        pass
```

**Apply to Plant Tracker:**
- `PlantHealthAnalyzer`: Analyzes plant images
- `WateringScheduler`: Manages watering schedules
- `PlantRepository`: Handles plant data persistence
- `NotificationManager`: Manages watering reminders

#### Dependency Inversion Principle (DIP)
> Depend on abstractions, not concrete implementations

**Example from Meal Planner:**
```python
from typing import Protocol

# Define the interface (abstraction)
class LLMProvider(Protocol):
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        ...

# Concrete implementations
class ClaudeProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        # Claude-specific implementation
        pass

class GeminiProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        # Gemini-specific implementation
        pass

# Service depends on abstraction, not concrete class
class RecipeService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm  # Can be any LLM provider
```

**Benefits:**
- Easy to swap LLM providers (Claude → Gemini)
- Testable with mock providers
- Loose coupling between components

**Apply to Plant Tracker:**
```python
class ImageAnalyzer(Protocol):
    def analyze_health(self, image: bytes) -> HealthReport:
        ...

# Could swap between different ML models
class LocalMLAnalyzer:
    def analyze_health(self, image: bytes) -> HealthReport:
        # Use local ML model
        pass

class ClaudeVisionAnalyzer:
    def analyze_health(self, image: bytes) -> HealthReport:
        # Use Claude vision API
        pass
```

### 2. DRY (Don't Repeat Yourself)

**Pattern: Centralized Data File Management**

From Meal Planner:
```python
from typing import Literal
from pathlib import Path

DataFile = Literal['staples', 'fresh', 'shopping_list', 'preferences']

def get_data_file_path(file_type: DataFile) -> Path:
    """Get the path for a data file."""
    file_map = {
        'staples': 'data/pantry/staples.md',
        'fresh': 'data/pantry/fresh.md',
        'shopping_list': 'data/pantry/shopping_list.md',
        'preferences': 'data/preferences.md',
    }
    return Path(file_map[file_type])
```

**Apply to Plant Tracker:**
```python
PlantDataFile = Literal['plants', 'watering_log', 'health_reports']

def get_plant_data_path(file_type: PlantDataFile) -> Path:
    file_map = {
        'plants': 'data/plants.json',
        'watering_log': 'data/watering_log.json',
        'health_reports': 'data/health_reports.json',
    }
    return Path(file_map[file_type])
```

### 3. YAGNI (You Aren't Gonna Need It)

**Don't over-engineer early.**

**Example from Meal Planner:**
- Started with simple file-based storage (Markdown)
- Only added JSON storage when needed for structured queries
- Avoided premature database integration

**Apply to Plant Tracker:**
1. **Phase 1**: Local storage only (SwiftData on iOS)
2. **Phase 2**: Add FastAPI backend when you need:
   - Multi-device sync
   - Server-side ML processing
   - Sharing with friends
3. **Phase 3**: Add push notifications only if local notifications aren't enough

**Don't build:**
- Multi-user authentication (start with single user)
- Complex role systems (YAGNI until you share with others)
- Caching layers (add when you have performance issues)
- Microservices (start with monolith)

### 4. KISS (Keep It Simple, Stupid)

**Simplest solution that works.**

**Example from Meal Planner:**
```python
# ✅ GOOD: Simple, readable
def count_pantry_items(file_path: Path) -> int:
    """Count items in pantry file (lines starting with '-')."""
    content = file_path.read_text()
    return len([line for line in content.split('\n')
                if line.strip().startswith('-')])

# ❌ BAD: Overly complex for the same task
def count_pantry_items(file_path: Path) -> int:
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        counter = 0
        for row in reader:
            if row.get('type') == 'item':
                counter += 1
    return counter
```

---

## Layer Separation

### 3-Layer Architecture (FastAPI Backend)

```
┌────────────────────────────────────────┐
│         API Layer (FastAPI)            │
│  • Route handlers                      │
│  • Request/response validation         │
│  • Authentication middleware           │
└───────────────┬────────────────────────┘
                │
┌───────────────▼────────────────────────┐
│       Service/Business Layer           │
│  • Business logic                      │
│  • Orchestration                       │
│  • Domain rules                        │
└───────────────┬────────────────────────┘
                │
┌───────────────▼────────────────────────┐
│      Repository/Data Layer             │
│  • Database queries                    │
│  • File I/O                            │
│  • External API calls                  │
└────────────────────────────────────────┘
```

### Example: Plant Watering Feature

**API Layer (FastAPI):**
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class WaterPlantRequest(BaseModel):
    plant_id: str
    watered_at: datetime

@router.post("/plants/{plant_id}/water")
async def water_plant(
    plant_id: str,
    request: WaterPlantRequest,
    plant_service: PlantService = Depends(get_plant_service)
):
    """Record a watering event."""
    result = plant_service.record_watering(plant_id, request.watered_at)
    return {"success": True, "next_watering": result.next_watering_date}
```

**Service Layer:**
```python
class PlantService:
    def __init__(self, plant_repo: PlantRepository, watering_repo: WateringRepository):
        self.plant_repo = plant_repo
        self.watering_repo = watering_repo

    def record_watering(self, plant_id: str, watered_at: datetime) -> WateringResult:
        # Business logic
        plant = self.plant_repo.get_by_id(plant_id)
        if not plant:
            raise PlantNotFoundError(plant_id)

        # Record watering
        self.watering_repo.add_event(plant_id, watered_at)

        # Calculate next watering (business rule)
        next_watering = watered_at + timedelta(days=plant.watering_frequency_days)

        return WateringResult(next_watering_date=next_watering)
```

**Repository Layer:**
```python
class PlantRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_by_id(self, plant_id: str) -> Optional[Plant]:
        # Data access logic
        plants = self._load_plants()
        return next((p for p in plants if p.id == plant_id), None)

    def _load_plants(self) -> list[Plant]:
        with open(self.db_path, 'r') as f:
            data = json.load(f)
        return [Plant(**p) for p in data['plants']]
```

**Why this matters:**
- **Testable**: Mock repositories in service tests
- **Flexible**: Swap file storage for database without changing service layer
- **Maintainable**: Each layer has clear responsibility

---

## Data Flow Patterns

### Pattern 1: Repository Pattern

**Definition:** Separate data access logic from business logic.

**Benefits:**
- Single place to change storage mechanism
- Easy to test business logic (mock repository)
- Consistent interface for data operations

**Example from Meal Planner:**
```python
class RecipeRepository:
    """Handles all recipe storage operations."""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def load_all(self) -> list[Recipe]:
        """Load all recipes from storage."""
        pass

    def save(self, recipe: Recipe) -> bool:
        """Save a recipe to storage."""
        pass

    def find_by_name(self, name: str) -> Optional[Recipe]:
        """Find recipe by name."""
        pass
```

**Apply to Plant Tracker:**
```python
class PlantRepository:
    def load_all(self) -> list[Plant]:
        pass

    def save(self, plant: Plant) -> bool:
        pass

    def find_by_id(self, plant_id: str) -> Optional[Plant]:
        pass

    def find_needing_water(self, threshold_date: datetime) -> list[Plant]:
        """Find plants that need watering before threshold_date."""
        pass
```

### Pattern 2: Service Layer Pattern

**Definition:** Encapsulate business logic in service classes.

**Benefits:**
- Clear place for complex operations
- Orchestrates multiple repositories
- Contains domain logic

**Example from Meal Planner:**
```python
class RecipeGenerationService:
    """Handles recipe generation workflow."""

    def __init__(
        self,
        llm: LLMProvider,
        pantry_repo: PantryRepository,
        recipe_repo: RecipeRepository
    ):
        self.llm = llm
        self.pantry_repo = pantry_repo
        self.recipe_repo = recipe_repo

    def generate_recipes(
        self,
        cuisines: list[str],
        count: int = 5
    ) -> list[Recipe]:
        """Generate recipes based on current pantry."""
        # 1. Get current pantry
        pantry = self.pantry_repo.get_current_items()

        # 2. Build prompt
        prompt = self._build_prompt(cuisines, pantry)

        # 3. Call LLM
        response = self.llm.generate(prompt)

        # 4. Parse response
        recipes = self._parse_recipes(response)

        # 5. Save recipes
        for recipe in recipes:
            self.recipe_repo.save(recipe)

        return recipes
```

### Pattern 3: Dependency Injection

**Definition:** Pass dependencies to classes rather than creating them internally.

**Benefits:**
- Testable (inject mocks)
- Flexible (swap implementations)
- Explicit dependencies

**Example:**
```python
# ✅ GOOD: Dependencies injected
class PlantHealthService:
    def __init__(
        self,
        plant_repo: PlantRepository,
        image_analyzer: ImageAnalyzer,
        notification_service: NotificationService
    ):
        self.plant_repo = plant_repo
        self.analyzer = image_analyzer
        self.notifications = notification_service

# Easy to test with mocks
def test_health_analysis():
    mock_repo = Mock(spec=PlantRepository)
    mock_analyzer = Mock(spec=ImageAnalyzer)
    mock_notifier = Mock(spec=NotificationService)

    service = PlantHealthService(mock_repo, mock_analyzer, mock_notifier)
    # Test service logic
```

---

## Key Learnings

### 1. Start Simple, Iterate

**From Meal Planner:**
- Started with Streamlit (simpler than React)
- File-based storage before databases
- Basic auth before OAuth

**Apply to Plant Tracker:**
- Start offline-first (local SwiftData)
- Add backend when you need sync
- Local notifications before push notifications

### 2. Logging is Critical

**From Meal Planner:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Recipe generated successfully",
    extra={
        "cuisine": cuisine,
        "ingredient_count": len(ingredients),
        "execution_time_ms": elapsed_ms
    }
)
```

**Benefits:**
- Debug production issues
- Track performance
- Understand user behavior

**Apply to Plant Tracker:**
- Log all API calls
- Log image processing times
- Log notification deliveries

### 3. Type Hints Everywhere

**From Meal Planner:**
```python
from typing import Protocol, Optional
from pathlib import Path

def load_pantry_file(file_path: Path) -> str:
    """Load pantry file contents."""
    return file_path.read_text()

def parse_ingredients(text: str) -> list[Ingredient]:
    """Parse ingredients from text."""
    pass
```

**Benefits:**
- Catch bugs before runtime
- Better IDE autocomplete
- Self-documenting code

### 4. Fail Fast with Validation

**From Meal Planner:**
```python
def generate_recipes(ingredients: list[str]) -> list[Recipe]:
    # Validate early
    if not ingredients:
        raise ValueError("Ingredients list cannot be empty")

    if len(ingredients) > 50:
        raise ValueError("Too many ingredients (max 50)")

    # Continue with logic
    ...
```

**Apply to Plant Tracker:**
```python
def add_plant(name: str, watering_frequency_days: int) -> Plant:
    # Validate early
    if not name.strip():
        raise ValueError("Plant name cannot be empty")

    if watering_frequency_days < 1:
        raise ValueError("Watering frequency must be at least 1 day")

    # Create plant
    ...
```

### 5. Test Outcomes, Not Implementation

**From Meal Planner:**
```python
def test_recipe_generation_success():
    """Test successful recipe generation."""
    # Arrange
    service = RecipeService(repository=mock_repo, llm=mock_llm)

    # Act
    recipes = service.generate_recipes(["italian"], ["pasta", "tomato"])

    # Assert - test outcomes
    assert len(recipes) > 0
    assert all(r.name for r in recipes)  # All recipes have names
    assert all(r.ingredients for r in recipes)  # All have ingredients

    # Don't test implementation details
    # ❌ mock_llm.generate.assert_called_once()  # Too brittle
```

### 6. JSON Over Custom Formats

**From Meal Planner:**
- Started with Markdown (human-readable but hard to query)
- Migrated to JSON for structured data
- Kept Markdown for user-facing content only

**Lesson:** Use JSON for data you need to query/process.

**Apply to Plant Tracker:**
```json
{
  "plants": [
    {
      "id": "uuid-1234",
      "name": "Monstera Deliciosa",
      "species": "Monstera",
      "watering_frequency_days": 7,
      "last_watered": "2025-01-15T10:00:00Z",
      "next_watering": "2025-01-22T10:00:00Z",
      "health_status": "healthy",
      "location": "living_room"
    }
  ]
}
```

---

## Recommended File Structure

### FastAPI Backend
```
plant-tracker-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration
│   ├── dependencies.py          # Dependency injection setup
│   │
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── plants.py            # Plant endpoints
│   │   ├── watering.py          # Watering endpoints
│   │   ├── health.py            # Health check endpoints
│   │   └── auth.py              # Authentication endpoints
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── plant_service.py
│   │   ├── watering_service.py
│   │   ├── health_analyzer.py
│   │   └── notification_service.py
│   │
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py
│   │   ├── plant_repository.py
│   │   ├── watering_repository.py
│   │   └── health_repository.py
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── plant.py
│   │   ├── watering.py
│   │   └── health.py
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── logging_config.py
│       └── exceptions.py
│
├── tests/
│   ├── test_services/
│   ├── test_repositories/
│   └── test_api/
│
├── data/                        # Local data files
├── .env                         # Environment variables
├── pyproject.toml              # Dependencies
└── README.md
```

### SwiftUI Frontend
```
PlantTracker/
├── PlantTrackerApp.swift        # App entry point
├── Models/                      # Data models
│   ├── Plant.swift
│   ├── WateringEvent.swift
│   └── HealthReport.swift
│
├── Views/                       # UI views
│   ├── PlantListView.swift
│   ├── PlantDetailView.swift
│   ├── AddPlantView.swift
│   └── WateringHistoryView.swift
│
├── ViewModels/                  # View models (MVVM)
│   ├── PlantListViewModel.swift
│   └── PlantDetailViewModel.swift
│
├── Services/                    # Business logic
│   ├── APIClient.swift          # Network layer
│   ├── PlantService.swift
│   └── NotificationService.swift
│
└── Utilities/
    ├── ImagePicker.swift
    └── KeychainHelper.swift
```

---

## Next Steps

1. Read `02-programming-patterns.md` for specific code patterns
2. Review `03-fastapi-backend-guide.md` for FastAPI implementation details
3. Check `04-swiftui-frontend-guide.md` for iOS-specific patterns
4. Use `05-claude-collaboration.md` for working with Claude Code effectively
