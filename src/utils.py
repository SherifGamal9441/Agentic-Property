"""
Shared JSON parsing utilities for LLM node responses.

LLMs often return JSON with markdown fences, trailing text, or other noise.
These helpers extract valid JSON from noisy LLM output.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str) -> dict:
    """
    Extract and parse JSON from LLM output.

    Tries:
      1. Direct json.loads (clean output).
      2. Balanced-brace extraction (handles nesting, trailing text).

    Args:
        raw: Raw LLM response string.

    Returns:
        Parsed dict.

    Raises:
        json.JSONDecodeError: If no valid JSON found.
    """
    stripped = raw.strip()

    # 1. Direct parse (happy path)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2. Balanced-brace extraction — count { and } to find the first complete
    #    JSON object, handling nested objects/arrays correctly.
    start = stripped.find("{")
    if start == -1:
        raise json.JSONDecodeError("No opening brace found", stripped, 0)

    depth = 0
    for i in range(start, len(stripped)):
        ch = stripped[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = stripped[start:i + 1]
                return json.loads(candidate)

    # Unclosed brace — fall back to greedy regex as last resort
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise json.JSONDecodeError("No balanced JSON object found", stripped, 0)
