# Quick Reference Guide

**Fast access to common commands, patterns, and decisions for Plant Tracker development**

---

## Table of Contents

1. [Architecture Quick Reference](#architecture-quick-reference)
2. [Python Commands](#python-commands)
3. [FastAPI Commands](#fastapi-commands)
4. [Testing Commands](#testing-commands)
5. [Code Patterns Cheatsheet](#code-patterns-cheatsheet)
6. [Decision Guide](#decision-guide)
7. [Common Gotchas](#common-gotchas)

---

## Architecture Quick Reference

### System Overview

```
┌──────────────────┐
│   SwiftUI App    │  ← Camera, notifications, offline storage
│   (iOS)          │
└────────┬─────────┘
         │ HTTPS/REST
         ▼
┌──────────────────┐
│  FastAPI Backend │  ← Business logic, ML, database
│  (Python)        │
└──────────────────┘
```

### When to Use What

| Feature | SwiftUI (iOS) | FastAPI (Backend) |
|---------|---------------|-------------------|
| UI/Navigation | ✅ | ❌ |
| Camera/Photos | ✅ | ❌ |
| Local Notifications | ✅ | ❌ |
| Push Notifications | Setup | ✅ Send |
| Local Storage | ✅ SwiftData | ❌ |
| Database | ❌ | ✅ SQLite/Postgres |
| Image Analysis | ❌ | ✅ Claude Vision |
| Business Logic | Simple only | ✅ Complex |

### Development Phases

**Phase 1: Offline-First MVP**
- ✅ SwiftUI app with local storage (SwiftData)
- ✅ Local notifications
- ✅ Camera/photo library integration
- ❌ No backend yet

**Phase 2: Add Backend**
- ✅ FastAPI backend with endpoints
- ✅ Sync local data to server
- ✅ Image processing on server

**Phase 3: Advanced Features**
- ✅ Push notifications
- ✅ Multi-device sync
- ✅ Sharing with friends

---

## Python Commands

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or use uv (faster)
uv pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### Package Management

```bash
# Install package
pip install fastapi

# Install specific version
pip install fastapi==0.115.0

# Install with extras
pip install "fastapi[standard]"

# List installed packages
pip list

# Show package info
pip show fastapi

# Generate requirements.txt
pip freeze > requirements.txt
```

---

## FastAPI Commands

### Running the App

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (with workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With specific host/port
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

### API Documentation

```bash
# Start server, then visit:
http://localhost:8000/docs        # Swagger UI (interactive)
http://localhost:8000/redoc       # ReDoc (read-only)
```

### Project Setup

```bash
# Create FastAPI project structure
mkdir -p app/{api,services,repositories,models,utils}
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/dependencies.py
```

---

## Testing Commands

### Python Tests (pytest)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run specific test function
pytest tests/test_services.py::test_create_plant

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

### Code Quality

```bash
# Linting with ruff
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
ruff format .                   # Format code

# Type checking with mypy
mypy app/                       # Check types
mypy --strict app/              # Strict mode

# Combined check
ruff check . && mypy app/ && pytest
```

---

## Code Patterns Cheatsheet

### Python: Repository Pattern

```python
class PlantRepository:
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def load_all(self) -> list[Plant]:
        """Load all plants."""
        # Implementation

    def save(self, plant: Plant) -> bool:
        """Save a plant."""
        # Implementation

    def find_by_id(self, plant_id: str) -> Optional[Plant]:
        """Find plant by ID."""
        # Implementation
```

### Python: Service Pattern

```python
class PlantService:
    def __init__(self, repo: PlantRepository):
        self.repo = repo

    def create_plant(self, name: str, frequency: int) -> Plant:
        """Create a new plant."""
        plant = Plant(name=name, watering_frequency_days=frequency)
        self.repo.save(plant)
        return plant
```

### Python: FastAPI Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/plants", response_model=Plant)
async def create_plant(
    plant_data: PlantCreate,
    service: PlantService = Depends(get_plant_service)
):
    """Create a new plant."""
    try:
        return service.create_plant(
            name=plant_data.name,
            frequency=plant_data.watering_frequency_days
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Python: Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Plant created",
    extra={
        "plant_id": plant.id,
        "name": plant.name,
        "frequency": plant.watering_frequency_days
    }
)
```

### Swift: MVVM ViewModel

```swift
@MainActor
class PlantListViewModel: ObservableObject {
    @Published var plants: [Plant] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let service = PlantService()

    func loadPlants() async {
        isLoading = true
        defer { isLoading = false }

        do {
            plants = try await service.getAllPlants()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

### Swift: API Call

```swift
func getAllPlants() async throws -> [PlantDTO] {
    try await apiClient.request(endpoint: "/plants")
}
```

### Swift: SwiftData Query

```swift
@Query(sort: \Plant.name) var plants: [Plant]
```

---

## Decision Guide

### Should I build this feature now?

**Ask yourself:**
1. **Is it needed for MVP?** (No → defer to Phase 2)
2. **Does it solve a real problem?** (No → YAGNI)
3. **Is there a simpler alternative?** (Yes → use simpler)

### Where should this code live?

| Type of Code | Location |
|--------------|----------|
| API endpoint | `app/api/` |
| Business logic | `app/services/` |
| Data access | `app/repositories/` |
| Data models | `app/models/` |
| Utilities | `app/utils/` |
| UI (SwiftUI) | `Views/` |
| View logic | `ViewModels/` |
| Network calls | `Services/APIClient.swift` |

### Should I use local or push notifications?

| Use Case | Recommendation |
|----------|----------------|
| Watering reminders (personal) | **Local** |
| Friend shared a plant | **Push** |
| Scheduled reminders | **Local** |
| Server-triggered alerts | **Push** |

Start with **local**, add **push** only if needed.

### Should I store data locally or on server?

| Data Type | Storage |
|-----------|---------|
| User's plants | **Both** (local + sync) |
| Watering history | **Both** |
| Images | **Server** (reference locally) |
| User preferences | **Local first** |
| Shared data | **Server** |

**Pattern:** Offline-first (local), background sync to server.

---

## Common Gotchas

### Python

❌ **Using print() instead of logging**
```python
# Bad
print("Plant created")

# Good
logger.info("Plant created", extra={"plant_id": plant.id})
```

❌ **Missing type hints**
```python
# Bad
def create_plant(name, frequency):
    return Plant(name=name, frequency=frequency)

# Good
def create_plant(name: str, frequency: int) -> Plant:
    return Plant(name=name, watering_frequency_days=frequency)
```

❌ **Using os.path instead of pathlib**
```python
# Bad
import os
path = os.path.join("data", "plants.json")

# Good
from pathlib import Path
path = Path("data") / "plants.json"
```

❌ **Bare except clauses**
```python
# Bad
try:
    plant = load_plant(plant_id)
except:
    return None

# Good
try:
    plant = load_plant(plant_id)
except PlantNotFoundError:
    logger.warning(f"Plant not found: {plant_id}")
    return None
```

### FastAPI

❌ **Not using Depends for injection**
```python
# Bad
@router.get("/plants")
async def get_plants():
    service = PlantService()  # Creates new instance every time
    return service.get_all()

# Good
@router.get("/plants")
async def get_plants(service: PlantService = Depends(get_plant_service)):
    return service.get_all()
```

❌ **Not using response_model**
```python
# Bad
@router.get("/plants/{plant_id}")
async def get_plant(plant_id: str):
    return plant_service.get(plant_id)  # No validation

# Good
@router.get("/plants/{plant_id}", response_model=Plant)
async def get_plant(plant_id: str):
    return plant_service.get(plant_id)  # Validates response
```

### Swift

❌ **Business logic in Views**
```swift
// Bad
struct PlantListView: View {
    var body: some View {
        List {
            ForEach(plants) { plant in
                // Calculating next watering date in view
                let nextDate = plant.lastWatered.addingTimeInterval(...)
            }
        }
    }
}

// Good - Use ViewModel
struct PlantListView: View {
    @StateObject private var viewModel = PlantListViewModel()

    var body: some View {
        List {
            ForEach(viewModel.plants) { plant in
                // View just displays data
                Text(plant.nextWateringDate.formatted())
            }
        }
    }
}
```

❌ **Not handling async errors**
```swift
// Bad
Task {
    plants = try await service.getAllPlants()  // Crashes on error
}

// Good
Task {
    do {
        plants = try await service.getAllPlants()
    } catch {
        errorMessage = error.localizedDescription
    }
}
```

---

## Environment Variables

### Backend (.env)

```bash
# Required
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=sk-ant-...

# Optional
DEBUG=false
DATABASE_URL=sqlite:///./data/plants.db
DATA_DIR=./data
IMAGES_DIR=./data/images
```

### Load in Python

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/plant-health-analysis

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add plant health analysis endpoint

- Create HealthAnalysisService
- Add POST /api/health/analyze endpoint
- Include image upload handling
- Add tests for analysis service"

# Push to remote
git push origin feature/plant-health-analysis

# Create pull request (use GitHub CLI or web interface)
gh pr create --title "Add plant health analysis" --body "Implements #123"
```

---

## Useful Resources

### Python/FastAPI
- FastAPI docs: https://fastapi.tiangolo.com/
- Pydantic docs: https://docs.pydantic.dev/
- pytest docs: https://docs.pytest.org/

### Swift/SwiftUI
- SwiftUI docs: https://developer.apple.com/documentation/swiftui
- SwiftData docs: https://developer.apple.com/documentation/swiftdata
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/

### Design Patterns
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html
- MVVM: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel
- Dependency Injection: https://en.wikipedia.org/wiki/Dependency_injection

---

## Daily Workflow Checklist

### Starting a new feature

- [ ] Create feature branch
- [ ] Read related documentation
- [ ] Check existing similar code
- [ ] Plan the simplest solution
- [ ] Write failing test first (TDD)
- [ ] Implement feature
- [ ] Write tests for edge cases
- [ ] Run linter and type checker
- [ ] Run all tests
- [ ] Update documentation if needed
- [ ] Commit with descriptive message

### Before committing

- [ ] All tests pass: `pytest`
- [ ] Linting passes: `ruff check .`
- [ ] Type checking passes: `mypy app/`
- [ ] No print() statements
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No hardcoded credentials

---

## Summary

**Quick wins:**
- Use `claude.md` to maintain consistency
- Follow the established patterns
- Write tests as you go
- Run linters before committing
- Keep it simple (YAGNI)

**When stuck:**
1. Check this guide
2. Look at similar existing code
3. Ask Claude Code with specific questions
4. Review architecture docs

**Remember:** Build incrementally, test thoroughly, keep it simple.
