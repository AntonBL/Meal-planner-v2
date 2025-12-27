"""Core LLM infrastructure - Provider protocol and Claude implementation.

This module provides the base LLM infrastructure that can be imported
by any module without circular dependencies.
"""

import logging
import os
from typing import Protocol

import anthropic
from google import genai

from lib.exceptions import LLMAPIError

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers (dependency inversion principle)."""

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt."""
        ...


class ClaudeProvider:
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            model: Model to use (default: reads from MODEL_SMART env var, falls back to claude-sonnet-4-5-20250929)

        Raises:
            LLMAPIError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise LLMAPIError(
                "ANTHROPIC_API_KEY not found. "
                "Please set it in your .env file or pass it to the constructor."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or os.getenv("MODEL_SMART", "claude-sonnet-4-5-20250929")

        logger.info(
            "Claude provider initialized",
            extra={"model": self.model},
        )

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Claude API.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from Claude

        Raises:
            LLMAPIError: If API call fails
        """
        logger.info(
            "Calling Claude API",
            extra={
                "model": self.model,
                "prompt_length": len(prompt),
                "max_tokens": max_tokens,
            },
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            logger.info(
                "Claude API call successful",
                extra={
                    "response_length": len(response_text),
                    "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
                },
            )

            return response_text

        except anthropic.APIError as e:
            logger.error(
                "Claude API call failed",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise LLMAPIError(f"API call failed: {e}") from e


class GeminiProvider:
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize Gemini provider.

        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_API_KEY env var)
            model: Model to use (default: reads from MODEL_SMART env var, falls back to gemini-2.0-flash-exp)

        Raises:
            LLMAPIError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise LLMAPIError(
                "GOOGLE_API_KEY not found. "
                "Please set it in your .env file or pass it to the constructor."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = model or os.getenv("MODEL_SMART", "gemini-3-flash-preview")

        logger.info(
            "Gemini provider initialized",
            extra={"model": self.model},
        )

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Gemini API.

        Args:
            prompt: The prompt to send to Gemini
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from Gemini

        Raises:
            LLMAPIError: If API call fails
        """
        logger.info(
            "Calling Gemini API",
            extra={
                "model": self.model,
                "prompt_length": len(prompt),
                "max_tokens": max_tokens,
            },
        )

        try:
            # Import types for proper configuration
            from google.genai import types

            # Configure generation parameters
            # Disable thinking for more predictable outputs
            generation_config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,  # Don't include thinking in response
                    thinking_budget=0  # Set thinking budget to 0
                ),
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generation_config
            )

            response_text = response.text if hasattr(response, 'text') else str(response)

            if not response_text:
                raise LLMAPIError("Empty response from Gemini API")

            logger.info(
                "Gemini API call successful",
                extra={
                    "response_length": len(response_text),
                },
            )

            return response_text

        except LLMAPIError:
            raise
        except Exception as e:
            logger.error(
                "Gemini API call failed",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise LLMAPIError(f"API call failed: {e}") from e


def get_smart_model() -> LLMProvider:
    """Get an LLM provider configured with the smart model.

    The provider is selected based on the LLM_PROVIDER environment variable:
    - "gemini" or "google": Uses GeminiProvider with MODEL_SMART
    - "claude" or "anthropic" (default): Uses ClaudeProvider with MODEL_SMART

    Returns:
        LLMProvider instance configured with MODEL_SMART

    Raises:
        LLMAPIError: If provider initialization fails
    """
    provider = os.getenv("LLM_PROVIDER", "claude").lower()

    if provider in ["gemini", "google"]:
        logger.info("Using Gemini as smart model provider")
        return GeminiProvider()
    else:
        logger.info("Using Claude as smart model provider")
        return ClaudeProvider()


def get_fast_model() -> ClaudeProvider:
    """Get a Claude provider configured with the fast model (Haiku).

    Returns:
        ClaudeProvider instance configured with MODEL_FAST
    """
    fast_model = os.getenv("MODEL_FAST", "claude-haiku-4-5")
    return ClaudeProvider(model=fast_model)
