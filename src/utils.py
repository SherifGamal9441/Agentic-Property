"""
Shared JSON parsing utilities for LLM node responses.

LLMs often return JSON with markdown fences, trailing text, or other noise.
These helpers extract valid JSON from noisy LLM output.
"""

import json
import logging
import re

from langchain_core.utils.json import parse_json_markdown

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str) -> dict:
    """
    Extract and parse JSON from LLM output.

    Uses LangChain's parse_json_markdown which handles:
      1. Direct parsing
      2. Markdown fences
      3. Partial/truncated JSON output

    Args:
        raw: Raw LLM response string.

    Returns:
        Parsed dict.

    Raises:
        json.JSONDecodeError: If no valid JSON found.
    """
    try:
        return parse_json_markdown(raw.strip())
    except Exception as e:
        # Re-raise as JSONDecodeError to match previous behavior and upstream expectations
        raise json.JSONDecodeError(f"Failed to parse JSON: {e}", raw, 0)
