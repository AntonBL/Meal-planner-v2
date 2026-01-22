# Claude AI Assistant Instructions

**Instructions for Claude when working on the Plant Tracker project**

---

## Overview

You are working on a professional plant health tracking application with:
- **SwiftUI iOS app** - Native iOS experience with camera, notifications, local storage
- **Python FastAPI backend** - Image processing, ML analysis, data persistence

This is production-quality code. Follow professional software engineering practices at all times.

---

## Required Reading

**BEFORE writing any code, you MUST:**

1. Review the architecture documentation in `docs/` (if you copied the learnings folder)
   - `01-architecture-principles.md` - System design
   - `02-programming-patterns.md` - Code patterns
   - `03-fastapi-backend-guide.md` - Backend patterns
   - `04-swiftui-frontend-guide.md` - iOS patterns

2. Read existing code to understand current patterns

3. Check if similar functionality already exists (DRY principle)

---

## Core Principles

### Code Quality Standards

✅ **ALWAYS:**

**Python:**
- Use structured logging with `logging` module (never `print()`)
- Include complete type hints on all functions
- Write Google-style docstrings for all public functions/classes
- Use `pathlib.Path` instead of string paths
- Validate inputs early (fail fast)
- Handle errors with specific exception classes

**Swift:**
- Follow MVVM architecture pattern
- Keep business logic in ViewModels, not Views
- Use SwiftData for local storage
- Handle async operations with proper error handling
- Use proper access control (private, internal, public)

**Both:**
- Follow DRY, YAGNI, KISS, and SOLID principles
- Write tests for all new features
- Keep functions small and focused (SRP)
- Document complex logic

❌ **NEVER:**
- Use `print()` for output in Python (use `logging` module)
- Commit code without type hints (Python)
- Leave public functions without docstrings
- Repeat code (extract into functions)
- Over-engineer solutions (YAGNI)
- Ignore errors or use bare `except:` clauses in Python
- Put business logic in SwiftUI Views

### Testing Requirements

Every new feature MUST include:

**Python (pytest):**
- Unit tests with AAA pattern (Arrange, Act, Assert)
- Tests for happy path AND error cases
- Mocked external dependencies (API calls, file I/O)
- Isolated tests that don't depend on each other
- Type hints in test functions

**Swift (XCTest):**
- Unit tests for ViewModels
- Tests for business logic
- Mocked services and repositories
- Test both success and failure cases

**Test outcomes, not implementation details.**

---

## Architecture Patterns

### Backend (FastAPI)

**3-Layer Architecture:**
```
API Layer (app/api/)
    ↓
Service Layer (app/services/)
    ↓
Repository Layer (app/repositories/)
```

**Patterns to follow:**
- **Repository Pattern** - Data access logic
- **Service Layer** - Business logic
- **Dependency Injection** - Use FastAPI's `Depends()`
- **Pydantic Models** - Request/response validation

### Frontend (SwiftUI)

**MVVM Architecture:**
```
View (UI only)
    ↓
ViewModel (Business logic, @Published properties)
    ↓
Service (API calls, data operations)
    ↓
Repository (SwiftData, local storage)
```

**Patterns to follow:**
- **MVVM** - Separate UI from business logic
- **ObservableObject** - ViewModels publish state changes
- **@Published** - Properties that trigger UI updates
- **async/await** - For asynchronous operations
- **Offline-first** - Load from local storage, sync in background

---

## File Organization

### Python Backend
```
app/
├── api/              # API routes (POST /plants, etc.)
├── services/         # Business logic (PlantService)
├── repositories/     # Data access (PlantRepository)
├── models/          # Data models (Plant, WateringEvent)
└── utils/           # Utilities (logging, exceptions)
```

### SwiftUI Frontend
```
PlantTracker/
├── Models/          # Data models (Plant, WateringEvent)
├── Views/           # UI (PlantListView, PlantDetailView)
├── ViewModels/      # MVVM ViewModels
├── Services/        # API client, notification service
└── Storage/         # SwiftData, Keychain helper
```

---

## Development Workflow

### 1. Before Writing Code

- [ ] Understand the requirement completely
- [ ] Check if similar code already exists (DRY)
- [ ] Consider if this feature is actually needed (YAGNI)
- [ ] Plan the simplest solution (KISS)
- [ ] Identify which layer this belongs to (API/Service/Repository/View/ViewModel)

### 2. While Writing Code

**Python:**
- [ ] Use type hints everywhere
- [ ] Add structured logging with context (`extra={}`)
- [ ] Write docstrings as you go
- [ ] Use pathlib for file paths
- [ ] Validate inputs early

**Swift:**
- [ ] Follow MVVM (logic in ViewModel, not View)
- [ ] Use @Published for state
- [ ] Handle errors properly (try/catch)
- [ ] Use proper async/await

### 3. After Writing Code

**Python:**
- [ ] Write tests: `pytest`
- [ ] Run linter: `ruff check --fix .`
- [ ] Run type checker: `mypy app/`
- [ ] Ensure all tests pass: `pytest --cov=app`

**Swift:**
- [ ] Write tests (XCTest)
- [ ] Build and run: Cmd+R
- [ ] Fix warnings
- [ ] Test on device (if using camera/notifications)

### 4. Code Review Checklist

Before considering code "done":

**Python:**
- [ ] No `print()` statements remain
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Tests are written and passing
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Logging provides useful context

**Swift:**
- [ ] Business logic is in ViewModel, not View
- [ ] Errors are handled properly
- [ ] Tests are written
- [ ] No force unwrapping (`!`) unless justified
- [ ] Code builds without warnings

---

## Common Patterns

### Python: Loading Data Files

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_plants(data_path: Path) -> list[Plant]:
    """Load all plants from JSON file.

    Args:
        data_path: Path to plants.json file

    Returns:
        List of Plant objects

    Raises:
        FileNotFoundError: If data file doesn't exist
    """
    logger.info("Loading plants", extra={"path": str(data_path)})

    if not data_path.exists():
        logger.warning("Plants file not found", extra={"path": str(data_path)})
        return []

    try:
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)

        plants = [Plant(**p) for p in data.get('plants', [])]
        logger.info(f"Loaded {len(plants)} plants")
        return plants

    except json.JSONDecodeError as e:
        logger.error("Failed to parse plants JSON", exc_info=True)
        return []
```

### Python: FastAPI Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/plants", response_model=Plant, status_code=201)
async def create_plant(
    plant_data: PlantCreate,
    service: PlantService = Depends(get_plant_service)
):
    """Create a new plant.

    Args:
        plant_data: Plant creation data
        service: Injected plant service

    Returns:
        Created plant with generated ID

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        plant = service.create_plant(
            name=plant_data.name,
            watering_frequency_days=plant_data.watering_frequency_days
        )
        return plant

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Python: Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Good: Rich context
logger.info(
    "Plant watered successfully",
    extra={
        "plant_id": plant.id,
        "plant_name": plant.name,
        "watered_at": watered_at.isoformat(),
        "next_watering": next_watering.isoformat()
    }
)

# Bad: No context
logger.info("Plant watered")
```

### Swift: ViewModel Pattern

```swift
@MainActor
class PlantListViewModel: ObservableObject {
    @Published var plants: [Plant] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let plantService: PlantService
    private let plantStore: PlantStore

    init(plantService: PlantService, plantStore: PlantStore) {
        self.plantService = plantService
        self.plantStore = plantStore
    }

    func loadPlants() async {
        isLoading = true
        errorMessage = nil

        // Load from local storage first (offline-first)
        plants = plantStore.fetchAll()

        // Then sync with API
        do {
            let remotePlants = try await plantService.getAllPlants()
            // Update local storage
            for plant in remotePlants {
                plantStore.save(plant)
            }
            plants = plantStore.fetchAll()
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }
}
```

### Swift: API Call

```swift
class PlantService {
    private let apiClient = APIClient.shared

    func getAllPlants() async throws -> [PlantDTO] {
        try await apiClient.request(endpoint: "/plants")
    }

    func createPlant(_ plant: PlantDTO) async throws -> PlantDTO {
        try await apiClient.request(
            endpoint: "/plants",
            method: "POST",
            body: plant
        )
    }
}
```

---

## Communication with User

When presenting code changes to the user:

1. **Explain the reasoning**: Why you chose this approach
2. **Reference principles**: Mention which principles you applied (DRY, SRP, etc.)
3. **Highlight testing**: Show what tests you wrote
4. **Note trade-offs**: If you made any compromises, explain them
5. **Provide examples**: Show how to use the new code

Example:
> "I've implemented the plant watering feature following the Service Layer pattern.
> The WateringService handles the business logic (calculating next watering date,
> updating the plant), while the Repository handles data persistence. This maintains
> the separation of concerns and makes the code easily testable. I've included 5 tests
> covering both happy paths and error cases. The code passes ruff, mypy, and all tests."

---

## Pragmatic Decision Making

While following best practices is important, be pragmatic:

- **Don't over-engineer**: YAGNI applies - build what's needed now
- **Don't under-engineer**: But also don't skip logging, types, or tests
- **Balance is key**: Professional code is both robust AND simple

When in doubt, ask yourself:
1. Is this the simplest solution that works?
2. Can I test this easily?
3. Will another developer understand this in 6 months?
4. Does this follow the principles in this document?

---

## Development Phases

### Phase 1: Offline-First MVP
**Focus:** Working iOS app with local storage

Build:
- SwiftUI app with basic UI
- Local storage (SwiftData)
- CRUD operations for plants
- Watering tracking
- Local notifications
- Camera integration

**No backend needed yet!**

### Phase 2: Add Backend
**Focus:** API backend and sync

Build:
- FastAPI backend
- API endpoints
- Background sync (iOS → API)
- Image upload

### Phase 3: Advanced Features
**Focus:** Image analysis, push notifications

Build:
- Plant health analysis (Claude Vision)
- Push notifications (if needed)
- Sharing with friends

---

## Remember

You are building **production-quality software**. Every line of code should reflect professional software engineering practices.

**Quality over speed. Simplicity over cleverness. Tests over hope.**

When in doubt:
- Check existing code for patterns
- Follow DRY, YAGNI, KISS
- Write tests
- Log with context
- Keep it simple
