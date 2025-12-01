"""Core LLM infrastructure - Provider protocol and Claude implementation.

This module provides the base LLM infrastructure that can be imported
by any module without circular dependencies.
"""

import logging
import os
from typing import Protocol

import anthropic

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
            model: Model to use (default: claude-haiku-4-5)

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
        self.model = model or "claude-haiku-4-5"

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
