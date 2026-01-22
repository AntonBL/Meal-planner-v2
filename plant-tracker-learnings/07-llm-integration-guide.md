# LLM Integration Guide

**Connecting to Claude, Gemini, and Vision APIs for Plant Health Analysis**

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Provider Protocol Pattern](#provider-protocol-pattern)
4. [Text Generation (Claude & Gemini)](#text-generation-claude--gemini)
5. [Vision API Integration](#vision-api-integration)
6. [Error Handling](#error-handling)
7. [Cost Optimization](#cost-optimization)
8. [Testing LLM Integration](#testing-llm-integration)
9. [Real-World Examples](#real-world-examples)

---

## Overview

### Why Use LLMs in Plant Tracker?

**Primary Use Case: Plant Health Analysis**
- User uploads photo of plant
- Claude Vision API analyzes the image
- Returns health status, issues, recommendations

**Additional Use Cases:**
- Generate watering schedules based on plant type
- Answer plant care questions
- Identify plant species from photos

### Available Providers

| Provider | Best For | Cost | Models |
|----------|----------|------|--------|
| **Claude (Anthropic)** | Vision analysis, complex reasoning | $$$ | Sonnet 4.5, Opus 4.5, Haiku 4.5 |
| **Gemini (Google)** | Fast text generation, budget-friendly | $ | Gemini 3 Flash, Gemini 2.0 Flash |

**Recommendation for Plant Tracker:**
- **Vision**: Claude Vision (best quality for plant analysis)
- **Text**: Gemini Flash (cheaper for simple text tasks)

---

## Environment Setup

### 1. Install SDKs

```bash
# Install both SDKs
pip install anthropic google-genai

# Or add to pyproject.toml
[project]
dependencies = [
    "anthropic>=0.40.0",
    "google-genai>=1.56.0",
]
```

### 2. Get API Keys

**Claude (Anthropic):**
1. Go to https://console.anthropic.com/
2. Create account
3. Settings → API Keys → Create Key
4. Copy key (starts with `sk-ant-...`)

**Gemini (Google AI):**
1. Go to https://ai.google.dev/
2. Create account (free tier available!)
3. Get API Key
4. Copy key

### 3. Configure Environment Variables

Create `.env` file:

```bash
# LLM Provider Selection
# Options: "claude" (default) | "gemini"
LLM_PROVIDER=claude

# API Keys (get both for flexibility)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
GOOGLE_API_KEY=AIzaSy-your-key-here

# Model Configuration (optional - smart defaults)
# Text generation models
MODEL_SMART=claude-sonnet-4-5-20250929    # For complex tasks
MODEL_FAST=claude-haiku-4-5               # For simple tasks

# Vision model (for image analysis)
VISION_MODEL=claude-sonnet-4-5-20250929   # Best for plant health
```

### 4. Load Environment Variables

```python
# app/main.py or service initialization
from dotenv import load_dotenv
import os

load_dotenv()

# Verify keys are loaded
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

if not anthropic_key:
    print("Warning: ANTHROPIC_API_KEY not found")
if not google_key:
    print("Warning: GOOGLE_API_KEY not found")
```

---

## Provider Protocol Pattern

### Why Use Protocol Pattern?

**Benefits:**
- Swap LLM providers without changing service code
- Easy to test with mock providers
- Dependency inversion principle (SOLID)

### Define the Protocol

```python
# app/utils/llm_protocol.py
from typing import Protocol

class LLMProvider(Protocol):
    """Protocol for LLM providers (text generation)."""

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from the LLM
        """
        ...

class VisionProvider(Protocol):
    """Protocol for vision-enabled LLM providers."""

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 1000
    ) -> str:
        """Analyze an image with a prompt.

        Args:
            image_bytes: Image data as bytes
            prompt: Analysis instructions
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result as text
        """
        ...
```

### Implement Claude Provider

```python
# app/services/llm_providers.py
import logging
import os
from typing import Optional

import anthropic
from app.utils.exceptions import LLMAPIError

logger = logging.getLogger(__name__)

class ClaudeProvider:
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key (reads from env if None)
            model: Model to use (reads from MODEL_SMART env if None)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise LLMAPIError(
                "ANTHROPIC_API_KEY not found. "
                "Please set it in your .env file."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or os.getenv(
            "MODEL_SMART",
            "claude-sonnet-4-5-20250929"
        )

        logger.info(
            "Claude provider initialized",
            extra={"model": self.model}
        )

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
                extra={
                    "response_length": len(response_text),
                    "tokens_used": (
                        message.usage.input_tokens +
                        message.usage.output_tokens
                    )
                }
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude API call failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise LLMAPIError(f"API call failed: {e}") from e

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 1000
    ) -> str:
        """Analyze image using Claude Vision API."""
        import base64

        logger.info(
            "Calling Claude Vision API",
            extra={
                "model": self.model,
                "image_size_bytes": len(image_bytes),
                "prompt_length": len(prompt)
            }
        )

        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Create message with image
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = message.content[0].text

            logger.info(
                "Claude Vision API call successful",
                extra={
                    "response_length": len(response_text),
                    "tokens_used": (
                        message.usage.input_tokens +
                        message.usage.output_tokens
                    )
                }
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude Vision API call failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise LLMAPIError(f"Vision API call failed: {e}") from e
```

### Implement Gemini Provider

```python
from google import genai
from google.genai import types

class GeminiProvider:
    """Google Gemini LLM provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize Gemini provider."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise LLMAPIError(
                "GOOGLE_API_KEY not found. "
                "Please set it in your .env file."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = model or os.getenv(
            "MODEL_SMART",
            "gemini-3-flash-preview"
        )

        logger.info(
            "Gemini provider initialized",
            extra={"model": self.model}
        )

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Gemini API."""
        logger.info(
            "Calling Gemini API",
            extra={
                "model": self.model,
                "prompt_length": len(prompt),
                "max_tokens": max_tokens
            }
        )

        try:
            # Configure generation (disable thinking for predictable output)
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,
                    thinking_budget=0
                )
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            response_text = response.text if hasattr(response, 'text') else str(response)

            if not response_text:
                raise LLMAPIError("Empty response from Gemini API")

            logger.info(
                "Gemini API call successful",
                extra={"response_length": len(response_text)}
            )

            return response_text

        except Exception as e:
            logger.error(
                "Gemini API call failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise LLMAPIError(f"API call failed: {e}") from e
```

### Factory Function

```python
# app/services/llm_providers.py

def get_llm_provider() -> LLMProvider:
    """Get LLM provider based on environment configuration.

    Returns:
        LLMProvider instance (Claude or Gemini)
    """
    provider_name = os.getenv("LLM_PROVIDER", "claude").lower()

    if provider_name in ["gemini", "google"]:
        logger.info("Using Gemini as LLM provider")
        return GeminiProvider()
    else:
        logger.info("Using Claude as LLM provider")
        return ClaudeProvider()

def get_vision_provider() -> VisionProvider:
    """Get vision provider for image analysis.

    Returns:
        VisionProvider instance (Claude Vision recommended)
    """
    # Always use Claude for vision (best quality for plant analysis)
    vision_model = os.getenv("VISION_MODEL", "claude-sonnet-4-5-20250929")
    logger.info("Using Claude Vision API", extra={"model": vision_model})
    return ClaudeProvider(model=vision_model)
```

---

## Text Generation (Claude & Gemini)

### Basic Usage

```python
from app.services.llm_providers import get_llm_provider

# Get provider (Claude or Gemini based on .env)
llm = get_llm_provider()

# Generate text
prompt = "What are the best practices for watering a Monstera plant?"
response = llm.generate(prompt, max_tokens=500)

print(response)
# Output: "Monstera plants prefer to dry out slightly between waterings..."
```

### Structured Output

For the Plant Tracker, you'll want structured responses:

```python
def generate_watering_schedule(
    plant_name: str,
    plant_type: str,
    llm: LLMProvider
) -> dict:
    """Generate watering schedule for a plant.

    Args:
        plant_name: Name of the plant (e.g., "My Monstera")
        plant_type: Type/species (e.g., "Monstera deliciosa")
        llm: LLM provider instance

    Returns:
        Dictionary with watering schedule details
    """
    prompt = f"""Generate a watering schedule for this plant:

Plant Name: {plant_name}
Plant Type: {plant_type}

Provide the following information in this exact format:

FREQUENCY: [number of days between waterings]
AMOUNT: [description of water amount]
SEASON_ADJUST: [how to adjust for seasons]
SIGNS_NEEDS_WATER: [signs that plant needs water]
SIGNS_OVERWATERED: [signs of overwatering]

Be specific and practical."""

    response = llm.generate(prompt, max_tokens=500)

    # Parse response
    schedule = {}
    for line in response.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            schedule[key.strip().lower()] = value.strip()

    return schedule

# Usage
llm = get_llm_provider()
schedule = generate_watering_schedule(
    plant_name="My Monstera",
    plant_type="Monstera deliciosa",
    llm=llm
)

print(schedule)
# {
#     'frequency': '7-10 days',
#     'amount': '1-2 cups until water drains from bottom',
#     ...
# }
```

---

## Vision API Integration

### Plant Health Analysis (Primary Use Case)

```python
from pathlib import Path
from app.services.llm_providers import get_vision_provider
from app.utils.exceptions import LLMAPIError

def analyze_plant_health(image_path: Path) -> dict:
    """Analyze plant health from image.

    Args:
        image_path: Path to plant image

    Returns:
        Dictionary with health analysis:
        - status: "healthy" | "needs_attention" | "critical"
        - confidence: 0.0 to 1.0
        - issues: List of identified issues
        - recommendations: List of care recommendations
    """
    # Get vision provider
    vision = get_vision_provider()

    # Read image
    image_bytes = image_path.read_bytes()

    # Build analysis prompt
    prompt = """Analyze this plant photo and provide a health assessment.

Identify:
1. Overall health status (healthy, needs attention, or critical)
2. Specific issues (yellowing leaves, brown spots, wilting, pests, etc.)
3. Recommendations for care

Format your response EXACTLY like this:

STATUS: [healthy/needs_attention/critical]
CONFIDENCE: [0.0-1.0]
ISSUES:
- [Issue 1 with description]
- [Issue 2 with description]
RECOMMENDATIONS:
- [Recommendation 1]
- [Recommendation 2]

Be specific and actionable in your recommendations."""

    # Call vision API
    try:
        response = vision.analyze_image(
            image_bytes=image_bytes,
            prompt=prompt,
            max_tokens=1000
        )

        # Parse response
        result = _parse_health_analysis(response)

        logger.info(
            "Plant health analysis completed",
            extra={
                "status": result['status'],
                "confidence": result['confidence'],
                "issues_count": len(result['issues'])
            }
        )

        return result

    except LLMAPIError as e:
        logger.error(f"Plant health analysis failed: {e}")
        raise

def _parse_health_analysis(response: str) -> dict:
    """Parse vision API response into structured health data."""
    result = {
        'status': 'unknown',
        'confidence': 0.0,
        'issues': [],
        'recommendations': []
    }

    current_section = None

    for line in response.split('\n'):
        line = line.strip()

        if line.startswith('STATUS:'):
            result['status'] = line.replace('STATUS:', '').strip().lower()

        elif line.startswith('CONFIDENCE:'):
            try:
                result['confidence'] = float(
                    line.replace('CONFIDENCE:', '').strip()
                )
            except ValueError:
                result['confidence'] = 0.8

        elif line.startswith('ISSUES:'):
            current_section = 'issues'

        elif line.startswith('RECOMMENDATIONS:'):
            current_section = 'recommendations'

        elif line.startswith('-') and current_section:
            item = line[1:].strip()
            result[current_section].append(item)

    return result

# Usage
health_report = analyze_plant_health(Path("plant_photo.jpg"))

print(f"Status: {health_report['status']}")
print(f"Confidence: {health_report['confidence']}")
print(f"Issues: {health_report['issues']}")
print(f"Recommendations: {health_report['recommendations']}")
```

### Plant Species Identification

```python
def identify_plant_species(image_path: Path) -> dict:
    """Identify plant species from photo.

    Returns:
        - species: Common and scientific name
        - confidence: 0.0 to 1.0
        - care_tips: Basic care information
    """
    vision = get_vision_provider()
    image_bytes = image_path.read_bytes()

    prompt = """Identify the plant species in this image.

Provide:
1. Common name
2. Scientific name
3. Confidence level (0.0-1.0)
4. Basic care requirements

Format:

COMMON_NAME: [name]
SCIENTIFIC_NAME: [name]
CONFIDENCE: [0.0-1.0]
LIGHT: [light requirements]
WATER: [watering frequency]
DIFFICULTY: [easy/medium/hard]"""

    response = vision.analyze_image(image_bytes, prompt, max_tokens=500)

    # Parse and return
    return _parse_species_identification(response)
```

### Multi-Image Analysis

For analyzing multiple photos of the same plant:

```python
def analyze_plant_progress(
    image_paths: list[Path],
    days_between: int
) -> dict:
    """Analyze plant health progress from multiple photos.

    Args:
        image_paths: List of plant photos (chronological order)
        days_between: Days between each photo

    Returns:
        Progress analysis with trends
    """
    # Note: For multi-image, need to send all images in one API call
    # Claude supports up to 20 images per request

    vision = get_vision_provider()

    # Load all images
    images = [path.read_bytes() for path in image_paths]

    prompt = f"""Analyze these {len(images)} photos of the same plant, taken {days_between} days apart.

Compare the plant's health across the photos and identify:
1. Overall trend (improving, stable, declining)
2. Changes in leaf color, size, or condition
3. New growth or problems
4. Recommendations based on progression

Format:

TREND: [improving/stable/declining]
CHANGES:
- [Change 1]
- [Change 2]
RECOMMENDATIONS:
- [Recommendation 1]"""

    # For Claude, send multiple images in content
    # (Implementation depends on provider SDK)

    # This is a simplified example - actual implementation
    # would need provider-specific multi-image handling
    pass
```

---

## Error Handling

### Custom Exceptions

```python
# app/utils/exceptions.py

class LLMAPIError(Exception):
    """Base exception for LLM API errors."""
    pass

class RateLimitError(LLMAPIError):
    """Raised when API rate limit is exceeded."""
    pass

class ImageTooLargeError(LLMAPIError):
    """Raised when image exceeds size limit."""
    pass

class InvalidImageError(LLMAPIError):
    """Raised when image format is invalid."""
    pass
```

### Retry Logic with Exponential Backoff

```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: tuple = (LLMAPIError,)
) -> T:
    """Retry function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        retry_exceptions: Exceptions to catch and retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()

        except retry_exceptions as e:
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

    # Should never reach here, but for type safety
    return func()

# Usage
def analyze_with_retry(image_path: Path) -> dict:
    """Analyze plant health with automatic retry."""
    def api_call():
        return analyze_plant_health(image_path)

    return retry_with_backoff(
        api_call,
        max_retries=3,
        initial_delay=1.0
    )
```

### Graceful Degradation

```python
def analyze_plant_health_safe(image_path: Path) -> dict:
    """Analyze plant health with fallback to basic analysis.

    Returns default assessment if API fails.
    """
    try:
        return analyze_plant_health(image_path)

    except LLMAPIError as e:
        logger.error(f"Vision API failed, using fallback: {e}")

        # Return safe default
        return {
            'status': 'unknown',
            'confidence': 0.0,
            'issues': ['Unable to analyze - API error'],
            'recommendations': [
                'Check soil moisture',
                'Ensure adequate light',
                'Monitor for changes'
            ]
        }
```

---

## Cost Optimization

### Model Selection by Task

```python
# Use cheaper models for simple tasks

def get_llm_by_complexity(complex: bool = False) -> LLMProvider:
    """Get appropriate LLM based on task complexity.

    Args:
        complex: True for complex tasks, False for simple

    Returns:
        LLMProvider instance
    """
    if complex:
        # Use smart model (Sonnet/Opus for complex analysis)
        model = os.getenv("MODEL_SMART", "claude-sonnet-4-5-20250929")
    else:
        # Use fast model (Haiku for simple tasks)
        model = os.getenv("MODEL_FAST", "claude-haiku-4-5")

    return ClaudeProvider(model=model)

# Usage
# Complex: Plant health analysis
vision = ClaudeProvider(model=os.getenv("VISION_MODEL"))
health = vision.analyze_image(image, prompt)

# Simple: Parse plant name
llm = get_llm_by_complexity(complex=False)
parsed_name = llm.generate("Extract plant name from: My Monstera Plant")
```

### Caching Results

```python
from functools import lru_cache
import hashlib

def hash_image(image_bytes: bytes) -> str:
    """Create hash of image for caching."""
    return hashlib.sha256(image_bytes).hexdigest()

# Simple in-memory cache
_analysis_cache: dict[str, dict] = {}

def analyze_plant_health_cached(image_path: Path) -> dict:
    """Analyze plant health with caching to avoid duplicate API calls."""
    image_bytes = image_path.read_bytes()
    image_hash = hash_image(image_bytes)

    # Check cache
    if image_hash in _analysis_cache:
        logger.info("Returning cached health analysis")
        return _analysis_cache[image_hash]

    # Perform analysis
    result = analyze_plant_health(image_path)

    # Cache result
    _analysis_cache[image_hash] = result

    return result
```

### Prompt Optimization

```python
# ❌ Inefficient: Long prompt
prompt = """
I have a plant and I want to know everything about it.
Can you tell me what species it is? And also what are all
the care requirements? Like how much water and light and
temperature and humidity and fertilizer and soil type and
when to repot and common pests and diseases and propagation
methods and seasonal care adjustments...
"""

# ✅ Efficient: Concise, structured prompt
prompt = """Identify plant species and provide care summary.

Format:
SPECIES: [name]
LIGHT: [requirements]
WATER: [frequency]
TEMP: [range]"""
```

---

## Testing LLM Integration

### Mock Provider for Tests

```python
# tests/mocks.py

class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, responses: dict[str, str] = None):
        self.responses = responses or {}
        self.calls: list[dict] = []

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Mock generate method."""
        self.calls.append({
            'type': 'generate',
            'prompt': prompt,
            'max_tokens': max_tokens
        })

        # Return canned response based on prompt keywords
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt.lower():
                return response

        return "Mock LLM response"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 1000
    ) -> str:
        """Mock image analysis."""
        self.calls.append({
            'type': 'analyze_image',
            'image_size': len(image_bytes),
            'prompt': prompt,
            'max_tokens': max_tokens
        })

        # Return canned health analysis
        return """STATUS: healthy
CONFIDENCE: 0.95
ISSUES:
- No issues detected
RECOMMENDATIONS:
- Continue current care routine"""

# Usage in tests
def test_plant_health_service():
    """Test plant health analysis service."""
    # Arrange
    mock_llm = MockLLMProvider()
    service = PlantHealthService(vision_provider=mock_llm)

    # Act
    result = service.analyze_health("plant-123", image_bytes=b"fake_image")

    # Assert
    assert result['status'] == 'healthy'
    assert len(mock_llm.calls) == 1
    assert mock_llm.calls[0]['type'] == 'analyze_image'
```

---

## Real-World Examples

### Complete Plant Health Service

```python
# app/services/plant_health_service.py

from pathlib import Path
from datetime import datetime
import logging

from app.services.llm_providers import get_vision_provider
from app.repositories.plant_repository import PlantRepository
from app.repositories.health_repository import HealthReportRepository
from app.models.health import HealthReport
from app.utils.exceptions import LLMAPIError

logger = logging.getLogger(__name__)

class PlantHealthService:
    """Service for analyzing and managing plant health."""

    def __init__(
        self,
        plant_repo: PlantRepository,
        health_repo: HealthReportRepository,
        vision_provider = None
    ):
        self.plant_repo = plant_repo
        self.health_repo = health_repo
        self.vision = vision_provider or get_vision_provider()

    def analyze_and_save(
        self,
        plant_id: str,
        image_path: Path
    ) -> HealthReport:
        """Analyze plant health and save report.

        Args:
            plant_id: ID of the plant
            image_path: Path to plant photo

        Returns:
            HealthReport with analysis results
        """
        logger.info(
            "Starting plant health analysis",
            extra={"plant_id": plant_id, "image": str(image_path)}
        )

        # Get plant
        plant = self.plant_repo.get_by_id(plant_id)
        if not plant:
            raise ValueError(f"Plant not found: {plant_id}")

        # Analyze image
        image_bytes = image_path.read_bytes()

        prompt = f"""Analyze this {plant.species or 'plant'} for health issues.

Plant Name: {plant.name}
Species: {plant.species or 'Unknown'}

Provide detailed health assessment:

STATUS: [healthy/needs_attention/critical]
CONFIDENCE: [0.0-1.0]
ISSUES:
- [Issue with specific description]
RECOMMENDATIONS:
- [Specific actionable recommendation]"""

        try:
            response = self.vision.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                max_tokens=1000
            )

            # Parse response
            analysis = self._parse_analysis(response)

            # Create health report
            report = HealthReport(
                plant_id=plant_id,
                analyzed_at=datetime.now(),
                status=analysis['status'],
                confidence=analysis['confidence'],
                issues=analysis['issues'],
                recommendations=analysis['recommendations'],
                image_path=str(image_path)
            )

            # Save report
            self.health_repo.save(report)

            # Update plant health status
            plant.health_status = analysis['status']
            self.plant_repo.save(plant)

            logger.info(
                "Health analysis completed and saved",
                extra={
                    "plant_id": plant_id,
                    "status": analysis['status'],
                    "issues_count": len(analysis['issues'])
                }
            )

            return report

        except LLMAPIError as e:
            logger.error(
                "Health analysis failed",
                extra={"plant_id": plant_id, "error": str(e)},
                exc_info=True
            )
            raise

    def _parse_analysis(self, response: str) -> dict:
        """Parse vision API response."""
        # Implementation from earlier example
        pass
```

---

## Summary

**Key Takeaways:**

1. **Use Protocol Pattern** - Easy to swap providers, test with mocks
2. **Environment Configuration** - API keys in `.env`, never hardcode
3. **Structured Prompts** - Get consistent, parseable responses
4. **Error Handling** - Retry logic, graceful degradation
5. **Cost Optimization** - Right model for the task, caching
6. **Logging** - Track API calls, costs, performance

**For Plant Tracker:**
- **Vision**: Claude Vision for plant health analysis
- **Text**: Gemini Flash for cheaper text tasks
- **Cache**: Don't re-analyze same image twice
- **Fallback**: Provide basic recommendations if API fails

---

## Next Steps

1. Copy `.env.example` to `.env` and add your API keys
2. Implement `PlantHealthService` following the example
3. Add caching to avoid duplicate API calls
4. Test with mock providers before using real APIs
5. Monitor costs in provider dashboards

**You're now ready to integrate LLM capabilities into your Plant Tracker! 🌱**
