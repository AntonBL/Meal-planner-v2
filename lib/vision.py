"""Gemini Vision API integration for pantry photo detection.

Uses Gemini's Vision API to detect grocery items from photos.
Following agent.md guidelines for structure and error handling.
"""

import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

from lib.exceptions import LLMAPIError

logger = logging.getLogger(__name__)


def detect_items_from_image(
    image_file,
    provider=None,  # Kept for backward compatibility but not used
) -> list[dict]:
    """Detect grocery items from an uploaded image using Gemini Vision API.

    Args:
        image_file: Streamlit UploadedFile object or file-like object
        provider: Unused (kept for backward compatibility)

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
    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise LLMAPIError(
            "GOOGLE_API_KEY not found. "
            "Please set it in your .env file for vision functionality."
        )

    client = genai.Client(api_key=api_key)
    model = os.getenv("VISION_MODEL", "gemini-3-flash-preview")

    logger.info(
        "Starting image analysis for grocery detection",
        extra={
            "image_name": getattr(image_file, "name", "unknown"),
            "model": model,
        },
    )

    try:
        # Read image bytes
        image_bytes = image_file.read()

        logger.debug(
            "Image loaded",
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
2. Estimated quantity WITH UNIT (e.g., "3 peppers", "1 gallon", "2 lbs", "1 bottle", "16 oz")
3. Category: either "Pantry Staple" (dry goods, canned items, spices, oils, condiments) or "Fresh Item" (produce, dairy, meat, eggs)

QUANTITY FORMAT REQUIREMENTS:
- ALWAYS include both a number AND a unit (e.g., "2 lbs", "1 gallon", "3 pieces", "16 oz")
- Be specific with measurements - never vague like "some" or "a bunch"
- For items without clear quantities, estimate reasonably (e.g., "1 head", "1 bunch", "1 bag")
- Include weight/volume from packaging when visible (e.g., "16 oz can", "32 oz bottle")

Format your response as a simple list with one item per line:
- Item name, Quantity with unit, Category

Examples:
- Red bell peppers, 3 peppers, Fresh Item
- Olive oil, 1 bottle (16 oz), Pantry Staple
- Canned tomatoes, 4 cans (14 oz each), Pantry Staple
- Milk (2%), 1 gallon, Fresh Item
- Garlic, 2 bulbs, Fresh Item
- Dried pasta, 1 box (16 oz), Pantry Staple
- Fresh spinach, 1 bag (5 oz), Fresh Item

Only list items you can clearly identify. Be practical and specific.
If you see a grocery receipt, extract the items from it with quantities.
If uncertain about category, default to "Fresh Item".
IMPORTANT: Every item MUST have a quantity with a unit."""

        # Call Gemini Vision API
        logger.info("Calling Gemini Vision API")

        # Configure generation with thinking disabled
        generation_config = types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=1.0,
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=0,
            ),
        )

        # Create content with image and text
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                types.Part.from_text(text=prompt),
            ],
            config=generation_config,
        )

        # Parse response
        response_text = response.text if hasattr(response, "text") else str(response)

        if not response_text:
            raise LLMAPIError("Empty response from Gemini Vision API")

        items = parse_vision_response(response_text)

        logger.info(
            "Grocery detection completed successfully",
            extra={
                "image_name": file_name,
                "items_detected": len(items),
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
                extra={"item_name": parts[0], "category": parts[2]},
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
                extra={"item_name": parts[0]},
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


def extract_recipe_from_images(image_files: list) -> dict:
    """Extract recipe information from multiple images (e.g., multi-page recipe).

    Args:
        image_files: List of Streamlit UploadedFile objects or file-like objects

    Returns:
        Recipe dictionary with keys:
        - name: Recipe name
        - description: Brief description
        - time_minutes: Estimated cooking time
        - difficulty: easy/medium/hard
        - ingredients: List of ingredient strings
        - instructions: Cooking steps
        - cuisine: Optional cuisine type
        - tags: List of tags

    Raises:
        LLMAPIError: If API call fails or recipe cannot be extracted

    Example:
        >>> from lib.vision import extract_recipe_from_images
        >>> recipe = extract_recipe_from_images([file1, file2])
        >>> recipe['name']
        'Vegetarian Pad Thai'
    """
    # If only one image, use the single-image function
    if len(image_files) == 1:
        return extract_recipe_from_image(image_files[0])

    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise LLMAPIError(
            "GOOGLE_API_KEY not found. "
            "Please set it in your .env file for vision functionality."
        )

    client = genai.Client(api_key=api_key)
    model = os.getenv("VISION_MODEL", "gemini-3-flash-preview")

    logger.info(
        "Starting multi-image analysis for recipe extraction",
        extra={
            "num_images": len(image_files),
            "model": model,
        },
    )

    try:
        # Build prompt for multi-page recipe extraction
        prompt = f"""Analyze these {len(image_files)} images of a recipe (shown in order). This may be a multi-page recipe from a cookbook, website, or screenshot.

Extract the following details by combining information from ALL images:
1. Recipe name
2. Brief description (1-2 sentences)
3. Complete list of ingredients with FULL QUANTITIES AND UNITS from all pages
4. Step-by-step cooking instructions from all pages
5. Estimated cooking time in minutes
6. Difficulty level (easy/medium/hard)

INGREDIENT FORMAT REQUIREMENTS:
- ALWAYS include the quantity and unit for every ingredient (e.g., "2 cups", "1 lb", "3 cloves", "1/2 tsp")
- Be specific with measurements - never vague quantities like "some" or "a little"
- Include modifiers when present (e.g., "diced", "fresh", "chopped", "minced")
- Format: "[quantity] [unit] [modifier] [ingredient name]"
- Examples: "2 cups fresh spinach", "1 lb tomatoes (diced)", "3 cloves garlic (minced)", "1/4 cup olive oil"

MULTI-PAGE INSTRUCTIONS:
- The images are shown in order (Image 1, Image 2, etc.)
- Combine ingredients from all pages into one complete list
- Combine instructions from all pages in the correct order
- If the recipe spans multiple pages, merge them into a single coherent recipe

Format your response EXACTLY like this:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INGREDIENTS:
- [quantity unit modifier ingredient, e.g., "2 cups fresh spinach"]
- [quantity unit modifier ingredient, e.g., "1 lb tomatoes (diced)"]
[continue for all ingredients from ALL pages - MUST include quantities and units]
INSTRUCTIONS:
1. [First step with specific quantities and timing]
2. [Second step with specific quantities and timing]
3. [Third step with specific quantities and timing]
[Continue with all steps from ALL pages needed]
---END---

IMPORTANT:
- Combine information from ALL {len(image_files)} images
- If ingredients or steps continue across pages, merge them properly
- EVERY ingredient MUST have a quantity and unit - if unclear, estimate reasonably
- Keep instructions clear and numbered with specific amounts
- If the images don't contain a recipe, respond with: NO_RECIPE_FOUND

Analyze all images now:"""

        # Prepare image parts
        content_parts = []

        for idx, image_file in enumerate(image_files):
            # Read image bytes
            image_bytes = image_file.read()

            # Determine media type from file extension
            file_name = getattr(image_file, "name", f"image{idx}.jpg")
            file_extension = Path(file_name).suffix.lower()

            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(file_extension, "image/jpeg")

            logger.debug(
                f"Image {idx + 1} loaded",
                extra={"image_size_bytes": len(image_bytes), "media_type": media_type}
            )

            # Add image part
            content_parts.append(
                types.Part.from_bytes(data=image_bytes, mime_type=media_type)
            )

        # Add text prompt at the end
        content_parts.append(types.Part.from_text(text=prompt))

        # Call Gemini Vision API with all images
        logger.info(f"Calling Gemini Vision API with {len(image_files)} images for recipe extraction")

        # Configure generation with thinking disabled and higher token limit
        generation_config = types.GenerateContentConfig(
            max_output_tokens=3072,  # More tokens for multi-page recipes
            temperature=1.0,
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=0,
            ),
        )

        # Create content with all images and text
        response = client.models.generate_content(
            model=model,
            contents=content_parts,
            config=generation_config,
        )

        # Parse response
        response_text = response.text if hasattr(response, "text") else str(response)

        if not response_text:
            raise LLMAPIError("Empty response from Gemini Vision API")

        recipe = parse_recipe_vision_response(response_text)

        if not recipe:
            raise LLMAPIError("Could not extract recipe from images. Please ensure the images contain a clear recipe.")

        logger.info(
            "Multi-image recipe extraction completed successfully",
            extra={
                "num_images": len(image_files),
                "recipe_name": recipe.get("name", "Unknown"),
            },
        )

        return recipe

    except Exception as e:
        logger.error(
            "Failed to extract recipe from multiple images",
            extra={"error": str(e), "error_type": type(e).__name__, "num_images": len(image_files)},
            exc_info=True,
        )
        raise LLMAPIError(f"Vision API error: {str(e)}") from e


def extract_recipe_from_image(image_file) -> dict:
    """Extract recipe information from a screenshot or website image.

    Args:
        image_file: Streamlit UploadedFile object or file-like object

    Returns:
        Recipe dictionary with keys:
        - name: Recipe name
        - description: Brief description
        - time_minutes: Estimated cooking time
        - difficulty: easy/medium/hard
        - ingredients: List of ingredient strings
        - instructions: Cooking steps
        - cuisine: Optional cuisine type
        - tags: List of tags

    Raises:
        LLMAPIError: If API call fails or recipe cannot be extracted

    Example:
        >>> from lib.vision import extract_recipe_from_image
        >>> recipe = extract_recipe_from_image(uploaded_file)
        >>> recipe['name']
        'Vegetarian Pad Thai'
    """
    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise LLMAPIError(
            "GOOGLE_API_KEY not found. "
            "Please set it in your .env file for vision functionality."
        )

    client = genai.Client(api_key=api_key)
    model = os.getenv("VISION_MODEL", "gemini-3-flash-preview")

    logger.info(
        "Starting image analysis for recipe extraction",
        extra={
            "image_name": getattr(image_file, "name", "unknown"),
            "model": model,
        },
    )

    try:
        # Read image bytes
        image_bytes = image_file.read()

        logger.debug(
            "Image loaded",
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

        # Build prompt for recipe extraction
        prompt = """Analyze this image of a recipe (screenshot, photo, or website) and extract the complete recipe information.

Extract the following details:
1. Recipe name
2. Brief description (1-2 sentences)
3. Complete list of ingredients with FULL QUANTITIES AND UNITS
4. Step-by-step cooking instructions
5. Estimated cooking time in minutes
6. Difficulty level (easy/medium/hard)

INGREDIENT FORMAT REQUIREMENTS:
- ALWAYS include the quantity and unit for every ingredient (e.g., "2 cups", "1 lb", "3 cloves", "1/2 tsp")
- Be specific with measurements - never vague quantities like "some" or "a little"
- Include modifiers when present (e.g., "diced", "fresh", "chopped", "minced")
- Format: "[quantity] [unit] [modifier] [ingredient name]"
- Examples: "2 cups fresh spinach", "1 lb tomatoes (diced)", "3 cloves garlic (minced)", "1/4 cup olive oil"

Format your response EXACTLY like this:

---RECIPE---
NAME: [Recipe Name]
DESCRIPTION: [1-2 sentence description]
TIME: [number only, e.g., 30]
DIFFICULTY: [easy/medium/hard]
INGREDIENTS:
- [quantity unit modifier ingredient, e.g., "2 cups fresh spinach"]
- [quantity unit modifier ingredient, e.g., "1 lb tomatoes (diced)"]
[continue for all ingredients - MUST include quantities and units]
INSTRUCTIONS:
1. [First step with specific quantities and timing]
2. [Second step with specific quantities and timing]
3. [Third step with specific quantities and timing]
[Continue with all steps needed]
---END---

IMPORTANT:
- If any information is unclear or missing, make reasonable assumptions
- EVERY ingredient MUST have a quantity and unit - if unclear, estimate reasonably
- Keep instructions clear and numbered with specific amounts
- If the image doesn't contain a recipe, respond with: NO_RECIPE_FOUND

Analyze the image now:"""

        # Call Gemini Vision API
        logger.info("Calling Gemini Vision API for recipe extraction")

        # Configure generation with thinking disabled and higher token limit for recipes
        generation_config = types.GenerateContentConfig(
            max_output_tokens=2048,  # Recipes can be longer than grocery lists
            temperature=1.0,
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=0,
            ),
        )

        # Create content with image and text
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                types.Part.from_text(text=prompt),
            ],
            config=generation_config,
        )

        # Parse response
        response_text = response.text if hasattr(response, "text") else str(response)

        if not response_text:
            raise LLMAPIError("Empty response from Gemini Vision API")

        recipe = parse_recipe_vision_response(response_text)

        if not recipe:
            raise LLMAPIError("Could not extract recipe from image. Please ensure the image contains a clear recipe.")

        logger.info(
            "Recipe extraction completed successfully",
            extra={
                "image_name": file_name,
                "recipe_name": recipe.get("name", "Unknown"),
            },
        )

        return recipe

    except Exception as e:
        logger.error(
            "Failed to extract recipe from image",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise LLMAPIError(f"Vision API error: {str(e)}") from e


def parse_recipe_vision_response(response_text: str) -> dict | None:
    """Parse vision API response into recipe dictionary.

    Args:
        response_text: Raw text response from Vision API

    Returns:
        Recipe dictionary or None if parsing fails

    Example:
        >>> response = '''---RECIPE---
        ... NAME: Vegetable Stir Fry
        ... DESCRIPTION: Quick and easy
        ... TIME: 20
        ... DIFFICULTY: easy
        ... INGREDIENTS:
        ... - 2 cups vegetables
        ... INSTRUCTIONS:
        ... 1. Heat oil
        ... 2. Add vegetables
        ... ---END---'''
        >>> recipe = parse_recipe_vision_response(response)
        >>> recipe['name']
        'Vegetable Stir Fry'
    """
    logger.debug("Parsing recipe vision response")

    if "NO_RECIPE_FOUND" in response_text:
        logger.warning("Vision API indicated no recipe found in image")
        return None

    if "---RECIPE---" not in response_text or "---END---" not in response_text:
        logger.warning("Recipe markers not found in response")
        return None

    # Extract content between markers
    start = response_text.find("---RECIPE---") + len("---RECIPE---")
    end = response_text.find("---END---")
    content = response_text[start:end].strip()

    recipe = {}
    ingredients = []
    instructions_lines = []
    in_ingredients = False
    in_instructions = False

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("NAME:"):
            recipe["name"] = line.replace("NAME:", "").strip()
            in_ingredients = False
            in_instructions = False
        elif line.startswith("DESCRIPTION:"):
            recipe["description"] = line.replace("DESCRIPTION:", "").strip()
            in_ingredients = False
            in_instructions = False
        elif line.startswith("TIME:"):
            time_str = line.replace("TIME:", "").strip()
            try:
                recipe["time_minutes"] = int(time_str)
            except ValueError:
                recipe["time_minutes"] = time_str
            in_ingredients = False
            in_instructions = False
        elif line.startswith("DIFFICULTY:"):
            recipe["difficulty"] = line.replace("DIFFICULTY:", "").strip()
            in_ingredients = False
            in_instructions = False
        elif line.startswith("INGREDIENTS:"):
            in_ingredients = True
            in_instructions = False
        elif line.startswith("INSTRUCTIONS:"):
            in_ingredients = False
            in_instructions = True
        elif in_ingredients and line.startswith("-"):
            ingredients.append(line[1:].strip())
        elif in_instructions:
            # Collect instruction lines (numbered steps)
            instructions_lines.append(line)

    recipe["ingredients"] = ingredients
    recipe["instructions"] = "\n".join(instructions_lines)

    # Validate required fields
    required = ["name", "ingredients", "instructions"]
    if not all(field in recipe and recipe[field] for field in required):
        logger.warning(
            "Recipe missing required fields",
            extra={"recipe": recipe, "required": required}
        )
        return None

    # Set defaults for optional fields
    if "description" not in recipe:
        recipe["description"] = ""
    if "time_minutes" not in recipe:
        recipe["time_minutes"] = 30
    if "difficulty" not in recipe:
        recipe["difficulty"] = "medium"

    logger.info(
        "Recipe parsed successfully",
        extra={
            "recipe_name": recipe.get("name"),
            "ingredients_count": len(ingredients),
            "has_instructions": bool(recipe.get("instructions")),
        }
    )

    return recipe
