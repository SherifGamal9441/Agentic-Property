from __future__ import annotations

import argparse
import asyncio
import csv
import dataclasses
import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_service.database import SessionLocal, is_sqlite
from src.data_service.db_tables import ActiveListing

load_dotenv()

_insert = sqlite_insert if is_sqlite else pg_insert

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

RAPIDAPI_HOST = "uae-real-estate2.p.rapidapi.com"


def _load_api_keys() -> list[str]:
    """Load API keys from RAPIDAPI_KEYS (comma-separated) or RAPIDAPI_KEY (single fallback)."""
    keys_raw = os.getenv("RAPIDAPI_KEYS", "")
    keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    if not keys:
        single = os.getenv("RAPIDAPI_KEY", "").strip()
        if single:
            keys = [single]
    return keys


class KeyRotator:
    """Round-robin API key rotation with per-key usage tracking and 429 exhaustion handling."""

    def __init__(self, keys: list[str]):
        if not keys:
            raise ValueError(
                "No API keys found. Set RAPIDAPI_KEYS (comma-separated) or RAPIDAPI_KEY in .env"
            )
        self.keys = keys
        self.usage: dict[str, int] = {k: 0 for k in keys}
        self.exhausted: set[str] = set()
        self._idx = 0
        self._lock = asyncio.Lock()

    async def get_key(self) -> str:
        """Return next available key (round-robin), skipping exhausted ones."""
        async with self._lock:
            available = [k for k in self.keys if k not in self.exhausted]
            if not available:
                raise RuntimeError("All API keys exhausted — add more keys or wait for quota reset")
            key = available[self._idx % len(available)]
            self._idx += 1
            self.usage[key] += 1
            return key

    async def mark_exhausted(self, key: str) -> None:
        """Mark a key as exhausted (hit 429 / monthly quota)."""
        async with self._lock:
            if key not in self.exhausted:
                self.exhausted.add(key)
                remaining = len(self.keys) - len(self.exhausted)
                log.warning(
                    "Key ...%s marked exhausted (%d keys remaining)",
                    key[-4:],
                    remaining,
                )

    @staticmethod
    def headers_for(key: str) -> dict[str, str]:
        return {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": key,
        }

    @property
    def available_count(self) -> int:
        return len(self.keys) - len(self.exhausted)

    def log_status(self) -> None:
        for k, v in self.usage.items():
            status = "EXHAUSTED" if k in self.exhausted else "active"
            log.info("  Key ...%s — %d requests (%s)", k[-4:], v, status)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log_dir = Path("logs/scraper")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(log_dir / "scraper.log", maxBytes=10*1024*1024, backupCount=3, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

@dataclass
class ApartmentListing:
    property_id: Optional[int]
    price: Optional[float]
    type: Optional[str]
    beds: Optional[int]
    baths: Optional[int]
    address: Optional[str]
    furnishing: Optional[str]
    completion_status: Optional[str]
    post_date: Optional[date]
    building_name: Optional[str]
    year_of_completion: Optional[int]
    total_parking_spaces: Optional[int]
    total_floors: Optional[int]
    total_building_area_sqft: Optional[float]
    elevators: Optional[int]
    area_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    link: Optional[str]

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_year(raw: Optional[str]) -> Optional[int]:
    if not raw:
        return None
    try:
        normalised = raw.replace("T", " ").replace("Z", "").strip()
        return datetime.strptime(normalised[:10], "%Y-%m-%d").year
    except (ValueError, TypeError):
        log.warning("Failed to parse year from '%s'", raw)
        return None

def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        normalised = raw.replace("T", " ").replace("Z", "").strip()
        return datetime.strptime(normalised[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        log.warning("Failed to parse date from '%s'", raw)
        return None

def _build_address(location: dict[str, Any]) -> Optional[str]:
    parts: list[str] = []
    for key in ("cluster", "sub_community", "community", "city", "country"):
        node = location.get(key)
        if isinstance(node, dict):
            name = node.get("name")
            if name:
                parts.append(name)
    return ", ".join(reversed(parts)) or None

def _parse_detail(data: dict[str, Any]) -> ApartmentListing:
    details = data.get("details") or {}
    location = data.get("location") or {}
    meta = data.get("meta") or {}
    building = data.get("building_info") or {}
    completion = details.get("completion_details") or {}
    coords = location.get("coordinates") or {}
    community = location.get("community") or {}

    is_furnished = details.get("is_furnished")
    furnishing = (
        "Furnished" if is_furnished is True else
        "Unfurnished" if is_furnished is False else
        None
    )

    year = _parse_year(building.get("completion_date")) or \
           _parse_year(completion.get("completion_date"))

    return ApartmentListing(
        property_id=data.get("id"),
        price=data.get("price"),
        type=(data.get("type") or {}).get("sub"),
        beds=details.get("bedrooms"),
        baths=details.get("bathrooms"),
        address=_build_address(location),
        furnishing=furnishing,
        completion_status=details.get("completion_status"),
        post_date=_parse_date(meta.get("created_at")),
        building_name=building.get("name"),
        year_of_completion=year,
        total_parking_spaces=building.get("total_parking_space"),
        total_floors=building.get("floors"),
        total_building_area_sqft=building.get("total_building_area"),
        elevators=building.get("elevators"),
        area_name=community.get("name"),
        latitude=coords.get("lat"),
        longitude=coords.get("lng"),
        link=meta.get("url"),
    )

# ---------------------------------------------------------------------------
# DB helpers — skip properties we already have
# ---------------------------------------------------------------------------

def _get_existing_ids() -> set[str]:
    """Return set of property_ids already in the active_listings table."""
    try:
        with SessionLocal() as session:
            rows = session.query(ActiveListing.property_id).all()
            return {r[0] for r in rows}
    except Exception as exc:
        log.warning("Could not query existing IDs from DB: %s — will fetch all", exc)
        return set()


# ---------------------------------------------------------------------------
# Phase 1 — collect property IDs
# ---------------------------------------------------------------------------

async def _collect_ids(
    client: httpx.AsyncClient,
    n: int,
    rotator: KeyRotator,
    existing_ids: set[str],
) -> list[int]:
    url = f"https://{RAPIDAPI_HOST}/properties_search"
    ids: list[int] = []
    page = 0
    page_size = int(os.getenv("SEARCH_PAGE_SIZE", "25"))
    skipped = 0

    while len(ids) < n:
        categories_raw = os.getenv("SCRAPER_CATEGORIES", "apartments")
        categories = [c.strip() for c in categories_raw.split(",") if c.strip()]
        payload = {
            "purpose": "for-sale",
            "categories": categories,
            "locations_ids": [2],
            "index": "latest",
        }
        params = {"page": page}

        log.info("Search page %d — collected %d / %d new IDs so far (skipped %d existing)", page, len(ids), n, skipped)

        key = await rotator.get_key()
        resp = await client.post(url, json=payload, params=params, headers=KeyRotator.headers_for(key))
        if resp.status_code == 429:
            await rotator.mark_exhausted(key)
            log.warning("Search page %d — key ...%s rate-limited, trying next key", page, key[-4:])
            continue
        resp.raise_for_status()
        body = resp.json()

        results: list[dict] = body.get("results") or []
        if not results:
            log.warning("Search returned no results on page %d — stopping early", page)
            break

        for item in results:
            pid = item.get("id")
            if pid and pid not in ids:
                pid_str = str(pid)
                if pid_str in existing_ids:
                    skipped += 1
                    continue
                ids.append(pid)
            if len(ids) >= n:
                break

        if len(results) < page_size:
            log.info("Reached last search page (%d results < %d page size)", len(results), page_size)
            break

        page += 1
        await asyncio.sleep(float(os.getenv("SCRAPER_REQUEST_DELAY", "0.5")))

    log.info("ID collection done: %d new, %d existing skipped", len(ids), skipped)
    return ids[:n]

# ---------------------------------------------------------------------------
# Phase 2 — fetch details
# ---------------------------------------------------------------------------

async def _fetch_detail(
    client: httpx.AsyncClient,
    property_id: int,
    sem: asyncio.Semaphore,
    index: int,
    total: int,
    rotator: KeyRotator,
) -> Optional[ApartmentListing]:
    url = f"https://{RAPIDAPI_HOST}/property/{property_id}"
    async with sem:
        max_retries = 3
        resp = None
        for attempt in range(max_retries):
            try:
                key = await rotator.get_key()
                resp = await client.get(url, headers=KeyRotator.headers_for(key))
                if resp.status_code == 429:
                    await rotator.mark_exhausted(key)
                    if rotator.available_count > 0 and attempt < max_retries - 1:
                        log.warning(
                            "Rate limited on ID %d with key ...%s, switching key (attempt %d/%d)",
                            property_id, key[-4:], attempt + 1, max_retries,
                        )
                        continue
                    log.warning("Rate limited on ID %d and no keys left — skipping", property_id)
                    return None
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (502, 503, 504) and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning("HTTP %d for property %d, retrying in %ds", exc.response.status_code, property_id, wait)
                    await asyncio.sleep(wait)
                    continue
                log.warning("HTTP %s for property %d — skipping", exc.response.status_code, property_id)
                return None
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning("Connection error on ID %d, retrying in %ds", property_id, wait)
                    await asyncio.sleep(wait)
                    continue
                log.warning("Failed to fetch property %d after %d attempts: %s", property_id, max_retries, exc)
                return None
        else:
            return None

        try:
            data = resp.json()
        except ValueError as exc:
            log.warning("Invalid JSON for property %d: %s", property_id, exc)
            return None

        if data.get("purpose") != "for-sale":
            log.debug("Skipping %d — purpose=%s", property_id, data.get("purpose"))
            return None

        listing = _parse_detail(data)
        log.info("[%d/%d] ✓ ID %d — %s", index, total, property_id, listing.area_name or "?")
        return listing

# ---------------------------------------------------------------------------
# Database append (dedup on property_id)
# ---------------------------------------------------------------------------

def _write_to_db(listings: list[ApartmentListing]) -> int:
    """Append new listings to the active_listings table (skip existing property_ids)."""
    if not listings:
        log.warning("No listings to write to DB.")
        return 0

    records = []
    for lst in listings:
        d = dataclasses.asdict(lst)
        if d.get("property_id") is not None:
            d["property_id"] = str(d["property_id"])
        records.append(d)

    with SessionLocal() as session:
        stmt = _insert(ActiveListing).values(records)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["property_id"],
        )
        result = session.execute(stmt)
        session.commit()
        inserted = result.rowcount or len(records)
        log.info("Appended %d new active listings to DB (dedup on property_id)", inserted)
        return inserted

# ---------------------------------------------------------------------------
# Output helpers (CSV kept as fallback)
# ---------------------------------------------------------------------------

def _to_dict(listing: ApartmentListing) -> dict[str, Any]:
    d = dataclasses.asdict(listing)
    for k, v in d.items():
        if isinstance(v, date):
            d[k] = v.isoformat()
    return d

def _write_csv(listings: list[ApartmentListing], path: str) -> None:
    if not listings:
        log.warning("No listings to write.")
        return
    fields = list(dataclasses.fields(ApartmentListing))
    fieldnames = [f.name for f in fields]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for lst in listings:
            writer.writerow(_to_dict(lst))
    log.info("Saved %d listings → %s", len(listings), p.resolve())

def _print_json(listings: list[ApartmentListing]) -> None:
    print(json.dumps([_to_dict(l) for l in listings], indent=2, ensure_ascii=False))

def _write_last_run(count: int) -> None:
    """Record a successful scrape timestamp to last_run.json."""
    p = Path(os.getenv("LAST_RUN_PATH", "last_run.json"))
    payload = {
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": count,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("last_run.json updated → %s (%d listings)", payload["last_run"], count)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def scrape(n: int, output_path: str = "") -> list[ApartmentListing]:
    log.info("Starting scrape: target=%d listings", n)
    t0 = time.monotonic()

    output_mode = os.getenv("SCRAPER_OUTPUT", "db").lower()
    log.info("Output mode: %s", output_mode)

    rotator = KeyRotator(_load_api_keys())
    log.info("Loaded %d API key(s) for rotation", len(rotator.keys))

    existing_ids: set[str] = set()
    if output_mode == "db":
        existing_ids = _get_existing_ids()
        if existing_ids:
            log.info("DB already has %d listings — will skip those IDs", len(existing_ids))

    async with httpx.AsyncClient(
        timeout=20,
    ) as client:

        ids = await _collect_ids(client, n, rotator, existing_ids)
        log.info("Collected %d new property IDs", len(ids))

        if not ids:
            log.error("No new IDs found — check your API key and quota, or DB may already have everything.")
            rotator.log_status()
            return []

        sem = asyncio.Semaphore(int(os.getenv("SCRAPER_CONCURRENCY", "3")))
        tasks = [
            _fetch_detail(client, pid, sem, i + 1, len(ids), rotator)
            for i, pid in enumerate(ids)
        ]
        results = await asyncio.gather(*tasks)

    listings = [r for r in results if r is not None]
    elapsed = time.monotonic() - t0
    log.info("Done — %d / %d listings fetched in %.1fs", len(listings), len(ids), elapsed)
    rotator.log_status()

    if output_mode == "csv":
        if not output_path:
            output_path = str(os.getenv("OUTPUT_CSV_PATH", "data/active_dld.csv"))
        _write_csv(listings, output_path)
        written_count = len(listings)
    else:
        written_count = _write_to_db(listings)

    _write_last_run(written_count)
    return listings

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Dubai for-sale apartment listings from Bayut API.",
    )
    parser.add_argument(
        "n",
        type=int,
        help="Number of apartment listings to scrape (e.g. 100)",
    )
    parser.add_argument(
        "--output",
        default="",
        help=(
            "CSV output path (used only when SCRAPER_OUTPUT=csv). "
            "Defaults to OUTPUT_CSV_PATH in .env when not provided."
        ),
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    n = args.n
    output = args.output

    if n < 1:
        print("Error: n must be ≥ 1", file=sys.stderr)
        sys.exit(1)

    max_listings = int(os.getenv("SCRAPER_MAX_LISTINGS", "3000"))
    if n > max_listings:
        print(
            f"Error: n={n} exceeds SCRAPER_MAX_LISTINGS={max_listings}. "
            "Raise the limit in .env if intentional.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(scrape(n, output))