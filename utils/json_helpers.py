"""
CareFlow AI — JSON Parsing & Repair Utilities

Handles Claude's occasional markdown-wrapped or malformed JSON responses
with robust extraction and repair logic.
"""

from __future__ import annotations

import json
import re
import logging

logger = logging.getLogger("careflow.json")


def extract_json(text: str) -> dict:
    """
    Extract and parse JSON from AI response text.
    
    Handles:
    - Raw JSON
    - Markdown code-fenced JSON (```json ... ```)
    - JSON with trailing text
    - Minor formatting issues
    
    Returns parsed dict or raises ValueError.
    """
    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        # Find content between first ``` and last ```
        parts = cleaned.split("```")
        if len(parts) >= 3:
            inner = parts[1]
            # Remove optional language identifier (json, JSON, etc.)
            if inner.startswith("json"):
                inner = inner[4:]
            elif inner.startswith("JSON"):
                inner = inner[4:]
            cleaned = inner.strip()
        else:
            # Single fence — strip it
            cleaned = cleaned.lstrip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Attempt JSON repair — common issues
    repaired = _repair_json(cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed after repair: {e}")
        raise ValueError(f"Could not extract valid JSON: {e}")


def _repair_json(text: str) -> str:
    """
    Attempt to repair common JSON malformations from LLM output.
    """
    repaired = text

    # Remove trailing commas before } or ]
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

    # Fix single quotes to double quotes (crude but effective for simple cases)
    # Only if there are no double quotes already
    if '"' not in repaired and "'" in repaired:
        repaired = repaired.replace("'", '"')

    # Remove control characters
    repaired = re.sub(r'[\x00-\x1f]+', ' ', repaired)

    # Fix unquoted keys (simple cases)
    repaired = re.sub(r'(?<={|,)\s*(\w+)\s*:', r' "\1":', repaired)

    return repaired


def safe_parse(text: str, fallback: dict | None = None) -> dict:
    """
    Parse JSON from text with a fallback value if parsing fails.
    
    Args:
        text: Raw text potentially containing JSON
        fallback: Default value if parsing fails (empty dict if None)
    
    Returns:
        Parsed dict or fallback value
    """
    try:
        return extract_json(text)
    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"JSON parse failed, using fallback: {e}")
        return fallback if fallback is not None else {}
