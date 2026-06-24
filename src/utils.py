"""Shared utilities for LLM response parsing."""

import json
import re


def parse_llm_json(raw: str) -> dict | None:
    """Parse JSON from an LLM response.

    Tries a direct json.loads first. If that fails, attempts to extract
    a JSON object from the raw text (handles markdown fences, surrounding
    prose, etc.). Returns None if both attempts fail.
    """
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
