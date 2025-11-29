"""Claude Vision API integration for pantry photo detection.

Uses Claude's Vision API to detect grocery items from photos.
Following agent.md guidelines for structure and error handling.
"""

import base64
import logging
from pathlib import Path
from typing import Optional

from lib.llm_agents import ClaudeProvider
from lib.exceptions import LLMAPIError

logger = logging.getLogger(__name__)


def detect_items_from_image(
    image_file,
    provider: Optional[ClaudeProvider] = None,
) -> list[dict]:
    """Detect grocery items from an uploaded image using Claude Vision API.

    Args:
        image_file: Streamlit UploadedFile object or file-like object
        provider: Optional ClaudeProvider instance (creates one if None)

    Returns:
        List of detected items with keys:
        - name: Item name (e.g., "Red bell peppers")
        - quantity: Estimated quantity (e.g., "3 peppers")
        - category: "Pantry Staple" or "Fresh Item"
        - confirmed: Boolean, default True (user can uncheck)

    Raises:
        LLMAPIError: If API call fails

    Example:
        >>> from lib.vision import detect_items_from_image
        >>> items = detect_items_from_image(uploaded_file)
        >>> len(items) > 0
        True
        >>> items[0]['name']
        'Red bell peppers'
    """
    if provider is None:
        provider = ClaudeProvider()

    logger.info(
        "Starting image analysis for grocery detection",
        extra={"image_name": getattr(image_file, "name", "unknown")},
    )

    try:
        # Read and encode image to base64
        image_bytes = image_file.read()
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        logger.debug(
            "Image encoded to base64",
            extra={"image_size_bytes": len(image_bytes)},
        )

        # Determine media type from file extension
        file_name = getattr(image_file, "name", "image.jpg")
        file_extension = Path(file_name).suffix.lower()

        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(file_extension, "image/jpeg")

        logger.debug("Media type determined", extra={"media_type": media_type})

        # Build prompt for grocery detection
        prompt = """Analyze this image and identify all food and grocery items you can see.

For each item, provide:
1. Item name (be specific, e.g., "red bell peppers" not just "vegetables")
2. Estimated quantity (e.g., "3 peppers", "1 gallon", "2 lbs", "1 bottle")
3. Category: either "Pantry Staple" (dry goods, canned items, spices, oils, condiments) or "Fresh Item" (produce, dairy, meat, eggs)

Format your response as a simple list with one item per line:
- Item name, Quantity, Category

Example:
- Red bell peppers, 3 peppers, Fresh Item
- Olive oil, 1 bottle, Pantry Staple
- Canned tomatoes, 4 cans, Pantry Staple
- Milk (2%), 1 gallon, Fresh Item
- Garlic, 2 bulbs, Fresh Item
- Dried pasta, 1 box, Pantry Staple

Only list items you can clearly identify. Be practical and specific.
If you see a grocery receipt, extract the items from it.
If uncertain about category, default to "Fresh Item"."""

        # Call Claude Vision API
        logger.info("Calling Claude Vision API")

        message = provider.client.messages.create(
            model=provider.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text
        items = parse_vision_response(response_text)

        logger.info(
            "Grocery detection completed successfully",
            extra={
                "image_name": file_name,
                "items_detected": len(items),
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            },
        )

        return items

    except Exception as e:
        logger.error(
            "Failed to detect items from image",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise LLMAPIError(f"Vision API error: {str(e)}") from e


def parse_vision_response(response_text: str) -> list[dict]:
    """Parse Claude's vision response into structured items.

    Args:
        response_text: Raw text response from Claude Vision API

    Returns:
        List of item dictionaries with keys:
        - name: Item name
        - quantity: Estimated quantity
        - category: "Pantry Staple" or "Fresh Item"
        - confirmed: Boolean (default True)

    Example:
        >>> response = "- Red peppers, 3 peppers, Fresh Item\\n- Olive oil, 1 bottle, Pantry Staple"
        >>> items = parse_vision_response(response)
        >>> len(items)
        2
        >>> items[0]['name']
        'Red peppers'
    """
    items = []
    lines = response_text.split("\n")

    logger.debug(
        "Parsing vision response",
        extra={"total_lines": len(lines)},
    )

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip empty lines and non-item lines
        if not line or not line.startswith("-"):
            continue

        # Remove leading dash and whitespace
        line = line[1:].strip()

        # Parse: "Item name, Quantity, Category"
        parts = [p.strip() for p in line.split(",")]

        if len(parts) >= 3:
            # Full format with all fields
            items.append(
                {
                    "name": parts[0],
                    "quantity": parts[1],
                    "category": parts[2],
                    "confirmed": True,
                }
            )
            logger.debug(
                f"Parsed item from line {line_num}",
                extra={"name": parts[0], "category": parts[2]},
            )

        elif len(parts) == 2:
            # Missing category, default to Fresh Item
            items.append(
                {
                    "name": parts[0],
                    "quantity": parts[1],
                    "category": "Fresh Item",
                    "confirmed": True,
                }
            )
            logger.debug(
                f"Parsed item from line {line_num} (defaulted category)",
                extra={"name": parts[0]},
            )

        else:
            logger.warning(
                f"Could not parse line {line_num} - insufficient parts",
                extra={"line": line, "parts_count": len(parts)},
            )

    logger.info(
        "Vision response parsing complete",
        extra={"items_parsed": len(items)},
    )

    return items
