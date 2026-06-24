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
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

from database import SessionLocal
from models import ActiveListing

load_dotenv()

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Settings:
    @property
    def rapidapi_headers(self) -> dict[str, str]:
        return {
            "x-rapidapi-host": "uae-real-estate2.p.rapidapi.com",
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", ""),
        }

settings = Settings()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8"),
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
        return None

def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        normalised = raw.replace("T", " ").replace("Z", "").strip()
        return datetime.strptime(normalised[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
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
# Phase 1 — collect property IDs
# ---------------------------------------------------------------------------

async def _collect_ids(
    client: httpx.AsyncClient,
    n: int,
) -> list[int]:
    url = "https://uae-real-estate2.p.rapidapi.com/properties_search"
    ids: list[int] = []
    page = 0
    page_size = int(os.getenv("SEARCH_PAGE_SIZE", "25"))

    while len(ids) < n:
        payload = {
            "purpose": "for-sale",
            "categories": ["apartments"],
            "locations_ids": [2],
            "index": "latest",
        }
        params = {"page": page}

        log.info("Search page %d — collected %d / %d IDs so far", page, len(ids), n)

        resp = await client.post(url, json=payload, params=params)
        resp.raise_for_status()
        body = resp.json()

        results: list[dict] = body.get("results") or []
        if not results:
            log.warning("Search returned no results on page %d — stopping early", page)
            break

        for item in results:
            pid = item.get("id")
            if pid and pid not in ids:
                ids.append(pid)
            if len(ids) >= n:
                break

        if len(results) < page_size:
            log.info("Reached last search page (%d results < %d page size)", len(results), page_size)
            break

        page += 1
        await asyncio.sleep(float(os.getenv("SCRAPER_REQUEST_DELAY", "0.5")))

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
) -> Optional[ApartmentListing]:
    url = f"https://uae-real-estate2.p.rapidapi.com/property/{property_id}"
    async with sem:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            if data.get("purpose") != "for-sale":
                log.debug("Skipping %d — purpose=%s", property_id, data.get("purpose"))
                return None

            listing = _parse_detail(data)
            log.info("[%d/%d] ✓ ID %d — %s", index, total, property_id, listing.area_name or "?")
            return listing

        except httpx.HTTPStatusError as exc:
            log.warning("HTTP %s for property %d — skipping", exc.response.status_code, property_id)
            return None
        except Exception as exc:
            log.warning("Error fetching property %d: %s — skipping", property_id, exc)
            return None

# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------

def _write_to_db(listings: list[ApartmentListing]) -> int:
    """Upsert listings into the active_listings table."""
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
        stmt = insert(ActiveListing).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["property_id"],
            set_={
                c.name: getattr(stmt.excluded, c.name)
                for c in ActiveListing.__table__.columns
                if c.name != "id"
            }
        )
        result = session.execute(stmt)
        session.commit()
        log.info("Upserted %d active listings into DB", result.rowcount)
        return result.rowcount

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

    async with httpx.AsyncClient(
        headers=settings.rapidapi_headers,
        timeout=20,
    ) as client:

        ids = await _collect_ids(client, n)
        log.info("Collected %d property IDs", len(ids))

        if not ids:
            log.error("No IDs found — check your API key and quota.")
            return []

        sem = asyncio.Semaphore(int(os.getenv("SCRAPER_CONCURRENCY", "3")))
        tasks = [
            _fetch_detail(client, pid, sem, i + 1, len(ids))
            for i, pid in enumerate(ids)
        ]
        results = await asyncio.gather(*tasks)

    listings = [r for r in results if r is not None]
    elapsed = time.monotonic() - t0
    log.info("Done — %d / %d listings fetched in %.1fs", len(listings), len(ids), elapsed)

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

    max_listings = int(os.getenv("SCRAPER_MAX_LISTINGS", "90"))
    if n > max_listings:
        print(
            f"Error: n={n} exceeds SCRAPER_MAX_LISTINGS={max_listings}. "
            "Raise the limit in .env if intentional.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(scrape(n, output))