"""
Fuzzy area name matcher.

Normalises LLM-produced area names against the canonical set of area names
found in the CSV data files (active_dld.csv + historical_dld.csv).

Flow:
    LLM output → fuzzy match against CSV area names → lowercase + strip
    suffixes like (JLT), (JVC), (JBR) → return normalised name

If no good match is found (below threshold), the input is passed through
unchanged (lowercased) so the ilike query can still attempt a partial match.
"""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path

from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CSV_FILES = [
    _PROJECT_ROOT / "data" / "active_dld.csv",
    _PROJECT_ROOT / "data" / "historical_dld.csv",
]

_SUFFIX_PATTERN = re.compile(r"\s*\([^)]*\)\s*$")


@lru_cache(maxsize=1)
def load_area_names() -> list[str]:
    """Load unique area names from both CSV files. Cached at module level."""
    names: set[str] = set()
    for csv_path in _CSV_FILES:
        if not csv_path.exists():
            logger.warning("Area matcher: CSV not found: %s", csv_path)
            continue
        try:
            with csv_path.open("r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    name = row.get("area_name")
                    if name and name.strip():
                        names.add(name.strip())
        except Exception as exc:
            logger.warning("Area matcher: could not read %s: %s", csv_path, exc)
    logger.info("Area matcher: loaded %d unique area names", len(names))
    return sorted(names)


def _normalise(name: str) -> str:
    """Lowercase and strip suffixes like (JLT), (JVC), (JBR), (DIP), (D3), etc."""
    cleaned = _SUFFIX_PATTERN.sub("", name).strip().lower()
    return cleaned


def fuzzy_match_area(input_name: str, threshold: int = 75) -> str | None:
    """
    Fuzzy-match an LLM-produced area name against canonical CSV area names.

    Args:
        input_name: Raw area name from the LLM (e.g. "Jumeirah Lakes", "JLT").
        threshold: Minimum fuzzy score (0-100). Below this, pass through unchanged.

    Returns:
        Normalised area name (lowercase, suffixes stripped), or None if input
        is empty. If no match meets the threshold, returns the input lowercased
        so the ilike query can still attempt a partial match.
    """
    if not input_name or not input_name.strip():
        return None

    area_names = load_area_names()
    if not area_names:
        return input_name.strip().lower()

    best = process.extractOne(
        input_name.strip(),
        area_names,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold,
    )

    if best is None:
        logger.debug("fuzzy: no match for %r (threshold=%d) — pass through", input_name, threshold)
        return input_name.strip().lower()

    matched_name, score, _ = best
    normalised = _normalise(matched_name)
    logger.debug("fuzzy: %r → %r (matched %r, score=%d)", input_name, normalised, matched_name, score)
    return normalised