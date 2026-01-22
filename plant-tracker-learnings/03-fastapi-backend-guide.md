# FastAPI Backend Guide

**Building the Plant Tracker Backend with FastAPI**

---

## Table of Contents

1. [Project Setup](#project-setup)
2. [FastAPI Application Structure](#fastapi-application-structure)
3. [API Route Patterns](#api-route-patterns)
4. [Dependency Injection](#dependency-injection)
5. [Request/Response Models](#requestresponse-models)
6. [Authentication](#authentication)
7. [Error Handling](#error-handling)
8. [Testing FastAPI](#testing-fastapi)
9. [Deployment Considerations](#deployment-considerations)

---

## Project Setup

### Initial Setup

```bash
# Create project directory
mkdir plant-tracker-api
cd plant-tracker-api

# Create virtual environment (using uv - faster than pip)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install FastAPI and dependencies
pip install fastapi uvicorn python-dotenv

# For production
pip install gunicorn  # WSGI server
```

### Project Structure

```
plant-tracker-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration
│   ├── dependencies.py          # Dependency injection
│   │
│   ├── api/                     # API routes
│   │   ├── __init__.py
│   │   ├── plants.py
│   │   ├── watering.py
│   │   ├── health.py
│   │   └── auth.py
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── plant_service.py
│   │   ├── watering_service.py
│   │   └── health_service.py
│   │
│   ├── repositories/            # Data access
│   │   ├── __init__.py
│   │   ├── plant_repository.py
│   │   └── watering_repository.py
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── plant.py
│   │   └── watering.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py
│       └── exceptions.py
│
├── tests/
├── data/
├── .env
├── pyproject.toml
└── README.md
```

### pyproject.toml Configuration

```toml
[project]
name = "plant-tracker-api"
version = "0.1.0"
description = "FastAPI backend for plant health tracking"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.9",  # For file uploads
    "python-jose[cryptography]>=3.3.0",  # For JWT
    "passlib[bcrypt]>=1.7.4",  # For password hashing
    "pillow>=10.0.0",  # For image processing
    "anthropic>=0.40.0",  # For Claude API
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",  # For testing FastAPI
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = true
strict_equality = true
```

---

## FastAPI Application Structure

### Main Application (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

from app.api import plants, watering, health, auth
from app.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Plant Tracker API",
    description="API for tracking plant health and watering schedules",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# CORS middleware (for SwiftUI app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(plants.router, prefix="/api/plants", tags=["Plants"])
app.include_router(watering.router, prefix="/api/watering", tags=["Watering"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Plant Tracker API",
        "docs": "/docs",
        "version": "0.1.0"
    }

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Plant Tracker API starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Plant Tracker API shutting down")
```

### Configuration (app/config.py)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App config
    app_name: str = "Plant Tracker API"
    debug: bool = False

    # API keys
    anthropic_api_key: Optional[str] = None

    # Auth
    secret_key: str  # Required for JWT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database (if using SQLite/Postgres)
    database_url: str = "sqlite:///./data/plants.db"

    # File storage
    data_dir: str = "./data"
    images_dir: str = "./data/images"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

---

## API Route Patterns

### Plants Router (app/api/plants.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

from app.models.plant import Plant, PlantCreate, PlantUpdate
from app.services.plant_service import PlantService
from app.dependencies import get_plant_service
from app.utils.exceptions import PlantNotFoundError

router = APIRouter()

@router.post("/", response_model=Plant, status_code=status.HTTP_201_CREATED)
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
    """
    try:
        plant = service.create_plant(
            name=plant_data.name,
            species=plant_data.species,
            watering_frequency_days=plant_data.watering_frequency_days,
            notes=plant_data.notes
        )
        return plant

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[Plant])
async def get_all_plants(
    service: PlantService = Depends(get_plant_service)
):
    """Get all plants."""
    plants = service.get_all_plants()
    return plants

@router.get("/{plant_id}", response_model=Plant)
async def get_plant(
    plant_id: str,
    service: PlantService = Depends(get_plant_service)
):
    """Get a plant by ID."""
    try:
        plant = service.get_plant(plant_id)
        return plant

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )

@router.put("/{plant_id}", response_model=Plant)
async def update_plant(
    plant_id: str,
    plant_data: PlantUpdate,
    service: PlantService = Depends(get_plant_service)
):
    """Update a plant."""
    try:
        plant = service.update_plant(plant_id, plant_data)
        return plant

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )

@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(
    plant_id: str,
    service: PlantService = Depends(get_plant_service)
):
    """Delete a plant."""
    try:
        service.delete_plant(plant_id)
        return None

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )

@router.get("/{plant_id}/needs-watering", response_model=bool)
async def check_needs_watering(
    plant_id: str,
    service: PlantService = Depends(get_plant_service)
):
    """Check if a plant needs watering."""
    try:
        needs_watering = service.check_needs_watering(plant_id)
        return needs_watering

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )
```

### Watering Router (app/api/watering.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List

from app.models.watering import WateringEvent, WateringEventCreate
from app.services.watering_service import WateringService
from app.dependencies import get_watering_service
from app.utils.exceptions import PlantNotFoundError

router = APIRouter()

@router.post("/", response_model=WateringEvent, status_code=status.HTTP_201_CREATED)
async def record_watering(
    event_data: WateringEventCreate,
    service: WateringService = Depends(get_watering_service)
):
    """Record a watering event."""
    try:
        event = service.record_watering(
            plant_id=event_data.plant_id,
            watered_at=event_data.watered_at or datetime.now(),
            notes=event_data.notes
        )
        return event

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {event_data.plant_id}"
        )

@router.get("/plant/{plant_id}", response_model=List[WateringEvent])
async def get_watering_history(
    plant_id: str,
    limit: int = 10,
    service: WateringService = Depends(get_watering_service)
):
    """Get watering history for a plant."""
    try:
        history = service.get_watering_history(plant_id, limit=limit)
        return history

    except PlantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_id}"
        )
```

### File Upload Pattern (Image Upload)

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import uuid

from app.services.health_service import HealthAnalysisService
from app.dependencies import get_health_service

router = APIRouter()

@router.post("/analyze")
async def analyze_plant_health(
    plant_id: str,
    image: UploadFile = File(...),
    service: HealthAnalysisService = Depends(get_health_service)
):
    """Analyze plant health from uploaded image."""
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    try:
        # Save image temporarily
        image_id = str(uuid.uuid4())
        image_path = Path(f"data/temp/{image_id}.jpg")
        image_path.parent.mkdir(parents=True, exist_ok=True)

        # Read and save image
        contents = await image.read()
        image_path.write_bytes(contents)

        # Analyze health
        result = service.analyze_health(plant_id, image_path)

        # Clean up temp file
        image_path.unlink()

        return result

    except Exception as e:
        logger.error(f"Health analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health analysis failed"
        )
```

---

## Dependency Injection

### Dependencies Module (app/dependencies.py)

```python
from functools import lru_cache
from pathlib import Path

from app.services.plant_service import PlantService
from app.services.watering_service import WateringService
from app.services.health_service import HealthAnalysisService
from app.repositories.plant_repository import PlantRepository
from app.repositories.watering_repository import WateringRepository
from app.config import settings

# Repository singletons
@lru_cache()
def get_plant_repository() -> PlantRepository:
    """Get plant repository instance."""
    data_path = Path(settings.data_dir) / "plants.json"
    return PlantRepository(data_path)

@lru_cache()
def get_watering_repository() -> WateringRepository:
    """Get watering repository instance."""
    data_path = Path(settings.data_dir) / "watering.json"
    return WateringRepository(data_path)

# Service factories
def get_plant_service(
    plant_repo: PlantRepository = Depends(get_plant_repository)
) -> PlantService:
    """Get plant service with injected dependencies."""
    return PlantService(plant_repo=plant_repo)

def get_watering_service(
    plant_repo: PlantRepository = Depends(get_plant_repository),
    watering_repo: WateringRepository = Depends(get_watering_repository)
) -> WateringService:
    """Get watering service with injected dependencies."""
    return WateringService(
        plant_repo=plant_repo,
        watering_repo=watering_repo
    )

def get_health_service(
    plant_repo: PlantRepository = Depends(get_plant_repository)
) -> HealthAnalysisService:
    """Get health analysis service."""
    return HealthAnalysisService(
        plant_repo=plant_repo,
        api_key=settings.anthropic_api_key
    )
```

---

## Request/Response Models

### Pydantic Models (app/models/plant.py)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PlantBase(BaseModel):
    """Base plant model."""
    name: str = Field(..., min_length=1, max_length=100)
    species: Optional[str] = Field(None, max_length=100)
    watering_frequency_days: int = Field(..., ge=1, le=365)
    notes: Optional[str] = None

class PlantCreate(PlantBase):
    """Model for creating a plant."""
    pass

class PlantUpdate(BaseModel):
    """Model for updating a plant."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[str] = Field(None, max_length=100)
    watering_frequency_days: Optional[int] = Field(None, ge=1, le=365)
    notes: Optional[str] = None

class Plant(PlantBase):
    """Complete plant model with ID and timestamps."""
    id: str
    created_at: datetime
    last_watered: Optional[datetime] = None
    health_status: str = "unknown"

    class Config:
        from_attributes = True  # For ORM compatibility

class WateringEvent(BaseModel):
    """Watering event model."""
    id: str
    plant_id: str
    watered_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class WateringEventCreate(BaseModel):
    """Model for creating a watering event."""
    plant_id: str
    watered_at: Optional[datetime] = None
    notes: Optional[str] = None
```

**Benefits of Pydantic:**
- Automatic validation
- Type coercion
- Clear error messages
- JSON serialization
- OpenAPI schema generation

---

## Authentication

### JWT Authentication Pattern

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
bearer_scheme = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Use in routes
@router.get("/protected")
async def protected_route(token_data: dict = Depends(verify_token)):
    """Protected endpoint requiring authentication."""
    user_id = token_data.get("sub")
    return {"message": f"Hello, user {user_id}"}
```

---

## Error Handling

### Global Exception Handlers

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.utils.exceptions import PlantNotFoundError, InvalidWateringFrequencyError

@app.exception_handler(PlantNotFoundError)
async def plant_not_found_handler(request: Request, exc: PlantNotFoundError):
    """Handle PlantNotFoundError."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "plant_not_found",
            "detail": str(exc),
            "plant_id": exc.plant_id
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "detail": str(exc)
        }
    )
```

---

## Testing FastAPI

### Test Configuration (tests/conftest.py)

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.main import app
from app.dependencies import get_plant_service

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_plant_service():
    """Mock plant service."""
    return Mock()

@pytest.fixture
def client_with_mock_service(mock_plant_service):
    """Test client with mocked service."""
    app.dependency_overrides[get_plant_service] = lambda: mock_plant_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### API Tests (tests/test_api/test_plants.py)

```python
def test_create_plant(client):
    """Test creating a plant."""
    response = client.post(
        "/api/plants/",
        json={
            "name": "Monstera",
            "species": "Monstera deliciosa",
            "watering_frequency_days": 7
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Monstera"
    assert "id" in data

def test_get_plant_not_found(client_with_mock_service, mock_plant_service):
    """Test getting non-existent plant."""
    from app.utils.exceptions import PlantNotFoundError

    mock_plant_service.get_plant.side_effect = PlantNotFoundError("plant-123")

    response = client_with_mock_service.get("/api/plants/plant-123")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

---

## Deployment Considerations

### Running the App

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables (.env)

```bash
# App
DEBUG=false
SECRET_KEY=your-secret-key-here

# API Keys
ANTHROPIC_API_KEY=your-anthropic-key

# Database
DATABASE_URL=sqlite:///./data/plants.db

# File Storage
DATA_DIR=./data
IMAGES_DIR=./data/images
```

---

## Next Steps

1. Review `04-swiftui-frontend-guide.md` for iOS client implementation
2. Check `05-claude-collaboration.md` for working with Claude Code
3. See `06-quick-reference.md` for command cheatsheet
