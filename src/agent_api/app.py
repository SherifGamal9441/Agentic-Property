"""Thin SSE facade over the existing Aizen graph."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Aizen Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1_000)
    thread_id: str | None = None


_NODE_LABELS = {
    "memory": "Reviewing your brief",
    "query_relevancy": "Checking Dubai property scope",
    "query_understanding": "Understanding your criteria",
    "query_routing": "Searching property data",
    "web_search": "Checking market sources",
    "comparison_engine": "Ranking best matches",
    "reflection": "Reviewing recommendation quality",
    "answer_generation": "Preparing your recommendation",
}


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"


def _safe_failure(_: Exception) -> dict[str, Any]:
    return {
        "code": "agent_unavailable",
        "message": "Property research is temporarily unavailable. Please try again.",
        "retryable": True,
    }


def _market_context(area: str) -> dict[str, Any]:
    endpoint = os.getenv("DATA_SERVICE_URL", "http://localhost:8000").rstrip("/")
    try:
        with urlopen(f"{endpoint}/market-context?{urlencode({'area': area})}", timeout=3) as response:
            return json.loads(response.read())
    except Exception:
        return {"area": area, "unavailable": True}


def _score_factors(raw: dict[str, Any], parsed_query: dict[str, Any]) -> tuple[list[str], list[str]]:
    matches: list[str] = []
    gaps: list[str] = []
    area = parsed_query.get("area_name")
    if area:
        if str(area).lower() in str(raw.get("area_name") or raw.get("location") or "").lower():
            matches.append(f"Matches {area}")
        else:
            gaps.append(f"Outside {area}")
    beds = parsed_query.get("property_beds_minimum")
    if beds is not None:
        actual_beds = raw.get("beds") if raw.get("beds") is not None else raw.get("bedrooms")
        if isinstance(actual_beds, (int, float)) and actual_beds >= beds:
            matches.append(f"Meets {beds}+ bedrooms")
        else:
            gaps.append(f"Below {beds} bedrooms")
    maximum_price = parsed_query.get("property_price_maximum")
    if maximum_price is not None:
        price = raw.get("price")
        if isinstance(price, (int, float)) and price <= maximum_price:
            matches.append("Within target budget")
        else:
            gaps.append("Above target budget")
    return matches, gaps


def _property_payloads(state: dict[str, Any]) -> list[dict[str, Any]]:
    listings = state.get("retrieved_properties") or []
    raw_by_id = {
        str(item.get("id") or item.get("property_id")): item
        for item in listings
    }
    comparisons = (state.get("comparison_result") or {}).get("properties") or listings
    parsed_query = state.get("parsed_query") or {}
    properties = []

    for index, comparison in enumerate(comparisons):
        key = str(comparison.get("id") or comparison.get("property_id") or index)
        raw = raw_by_id.get(key, comparison)
        area = raw.get("area_name") or raw.get("location") or "Dubai"
        title = (
            comparison.get("title")
            or raw.get("title")
            or raw.get("building_name")
            or raw.get("address")
            or f"{area} residence"
        )
        matched_criteria, unmatched_criteria = _score_factors(raw, parsed_query)
        if not matched_criteria and not unmatched_criteria:
            matched_criteria = comparison.get("matched_criteria", [])
            unmatched_criteria = comparison.get("unmatched_criteria", [])
        criteria_count = len(matched_criteria) + len(unmatched_criteria)
        fit_score = len(matched_criteria) / criteria_count if criteria_count else comparison.get("fit_score")
        latitude = raw.get("latitude")
        longitude = raw.get("longitude")
        has_coordinates = isinstance(latitude, (int, float)) and isinstance(longitude, (int, float))
        data_intent = state.get("data_intent", "recommend")
        properties.append(
            {
                "id": key,
                "title": title,
                "area": area,
                "price": raw.get("price"),
                "currency": "AED",
                "beds": raw.get("beds") or raw.get("bedrooms"),
                "baths": raw.get("baths") if raw.get("baths") is not None else raw.get("bathrooms"),
                "property_type": raw.get("type") if raw.get("type") is not None else raw.get("property_type"),
                "size_sqft": raw.get("total_building_area_sqft") if raw.get("total_building_area_sqft") is not None else raw.get("area_sqft"),
                "furnishing": raw.get("furnishing"),
                "completion_status": raw.get("completion_status"),
                "parking_spaces": raw.get("total_parking_spaces"),
                "year_of_completion": raw.get("year_of_completion"),
                "latitude": latitude,
                "longitude": longitude,
                "location_status": "exact" if has_coordinates else "unavailable",
                "source_url": raw.get("link"),
                "source_name": "Listing source" if raw.get("link") else None,
                "observed_at": str(raw["post_date"]) if raw.get("post_date") else None,
                "dataset_snapshot_at": str(raw["post_date"]) if raw.get("post_date") else None,
                "data_status": "historical_insight" if data_intent == "insights_only" else "active_dataset_listing",
                "fit_score": fit_score,
                "score_factors": matched_criteria,
                "matched_criteria": matched_criteria,
                "unmatched_criteria": unmatched_criteria,
                "price_assessment": comparison.get("price_assessment"),
                "data_intent": data_intent,
                "data_source": state.get("data_source", "active"),
                "visual_key": "marina" if "marina" in area.lower() else "city",
            }
        )
    return properties


async def _live_events(request: RunRequest) -> AsyncIterator[str]:
    yield _sse("run_started", {"thread_id": request.thread_id, "mode": "active_dataset"})
    async_checkpointer = None
    try:
        from src.agents.graph import build_graph
        from src.memory.long_term_memory import create_async_checkpointer

        async_checkpointer = await create_async_checkpointer()
        graph = build_graph(checkpointer=async_checkpointer)
        config = {"configurable": {"thread_id": request.thread_id}}
        final_state: dict[str, Any] = {}

        async for event in graph.astream_events({"query": request.query}, config=config, version="v2"):
            name = event.get("name", "")
            kind = event.get("event", "")
            if kind == "on_chain_start" and name in _NODE_LABELS:
                yield _sse("agent_step", {"node": name, "label": _NODE_LABELS[name], "status": "active"})
            elif kind == "on_chat_model_stream" and event.get("metadata", {}).get("langgraph_node") == "answer_generation":
                token = event["data"]["chunk"].content
                if token:
                    yield _sse("answer_token", {"token": token})
            elif kind == "on_chain_end" and name == "LangGraph":
                output = event["data"].get("output", {})
                final_state = output.model_dump() if hasattr(output, "model_dump") else output

        yield _sse("properties", {"properties": _property_payloads(final_state)})
        yield _sse(
            "run_completed",
            {
                "thread_id": request.thread_id,
                "route": final_state.get("route"),
                "data_source": final_state.get("data_source"),
                "data_intent": final_state.get("data_intent"),
            },
        )
    except Exception as exc:
        yield _sse("run_failed", _safe_failure(exc))
    finally:
        if async_checkpointer and getattr(async_checkpointer, "conn", None):
            await async_checkpointer.conn.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/market-context")
async def market_context(area: str = Query(min_length=1)) -> dict[str, Any]:
    return _market_context(area)


@app.post("/api/runs")
async def run_agent(request: RunRequest) -> StreamingResponse:
    request.thread_id = request.thread_id or str(uuid.uuid4())
    return StreamingResponse(
        _live_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
