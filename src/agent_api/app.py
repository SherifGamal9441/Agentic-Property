"""Thin SSE facade over the existing Aizen graph."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Iterable
from typing import Any, Literal

from fastapi import FastAPI
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
    mode: Literal["demo", "live"] = "demo"
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


def _property_payloads(state: dict[str, Any]) -> list[dict[str, Any]]:
    listings = state.get("retrieved_properties") or []
    raw_by_id = {
        str(item.get("id") or item.get("property_id")): item
        for item in listings
    }
    comparisons = (state.get("comparison_result") or {}).get("properties") or listings
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
        properties.append(
            {
                "id": key,
                "title": title,
                "area": area,
                "price": raw.get("price"),
                "currency": "AED",
                "beds": raw.get("beds") or raw.get("bedrooms"),
                "baths": raw.get("baths") or raw.get("bathrooms"),
                "property_type": raw.get("type") or raw.get("property_type"),
                "size_sqft": raw.get("total_building_area_sqft") or raw.get("area_sqft"),
                "furnishing": raw.get("furnishing"),
                "completion_status": raw.get("completion_status"),
                "parking_spaces": raw.get("total_parking_spaces"),
                "year_of_completion": raw.get("year_of_completion"),
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
                "source_url": raw.get("link"),
                "fit_score": comparison.get("fit_score"),
                "matched_criteria": comparison.get("matched_criteria", []),
                "unmatched_criteria": comparison.get("unmatched_criteria", []),
                "price_assessment": comparison.get("price_assessment"),
                "data_intent": state.get("data_intent", "recommend"),
                "data_source": state.get("data_source", "active"),
                "visual_key": "marina" if "marina" in area.lower() else "city",
            }
        )
    return properties


def _demo_state(query: str) -> dict[str, Any]:
    historical = "invest" in query.lower() or "off-plan" in query.lower()
    properties = [
        {
            "id": "demo-marina-vista",
            "title": "Marina Vista Residence",
            "price": 1_850_000,
            "beds": 2,
            "baths": 2,
            "type": "Apartment",
            "total_building_area_sqft": 1_108,
            "area_name": "Dubai Marina",
            "furnishing": "Furnished",
            "completion_status": "completed",
            "total_parking_spaces": 1,
            "year_of_completion": 2022,
            "latitude": 25.0806,
            "longitude": 55.1396,
            "link": "https://dubailand.gov.ae/",
        },
        {
            "id": "demo-cove",
            "title": "Harbour Cove Apartment",
            "price": 2_040_000,
            "beds": 2,
            "baths": 3,
            "type": "Apartment",
            "total_building_area_sqft": 1_244,
            "area_name": "Dubai Marina",
            "furnishing": "Unfurnished",
            "completion_status": "under-construction",
            "total_parking_spaces": 2,
            "year_of_completion": 2027,
            "latitude": 25.0779,
            "longitude": 55.1375,
            "link": "https://dubailand.gov.ae/",
        },
    ]
    comparisons = [
        {
            "id": item["id"],
            "title": item["title"],
            "fit_score": 0.94 if index == 0 else 0.79,
            "matched_criteria": ["Dubai Marina", "2 bedrooms", "budget"],
            "unmatched_criteria": [] if index == 0 else ["completed home"],
            "price_assessment": "fair",
        }
        for index, item in enumerate(properties)
    ]
    return {
        "query": query,
        "retrieved_properties": properties,
        "comparison_result": {"properties": comparisons},
        "data_source": "historical" if historical else "active",
        "data_intent": "insights_only" if historical else "recommend",
        "final_answer": (
            "Marina Vista Residence is your strongest match: it meets the two-bedroom "
            "brief, sits within the target segment, and is ready to view. Harbour Cove "
            "is the higher-spec alternative if an off-plan timeline works for you."
        ),
    }


def _token_chunks(text: str) -> Iterable[str]:
    words = text.split(" ")
    for index in range(0, len(words), 5):
        yield " ".join(words[index:index + 5]) + (" " if index + 5 < len(words) else "")


async def _demo_events(request: RunRequest) -> AsyncIterator[str]:
    yield _sse("run_started", {"thread_id": request.thread_id, "mode": "demo"})
    for node in ("memory", "query_understanding", "query_routing", "comparison_engine", "reflection"):
        yield _sse("agent_step", {"node": node, "label": _NODE_LABELS[node], "status": "complete"})

    state = _demo_state(request.query)
    yield _sse("properties", {"properties": _property_payloads(state)})
    for token in _token_chunks(state["final_answer"]):
        yield _sse("answer_token", {"token": token})
    yield _sse(
        "run_completed",
        {
            "thread_id": request.thread_id,
            "route": "query_routing",
            "data_source": state["data_source"],
            "data_intent": state["data_intent"],
        },
    )


async def _live_events(request: RunRequest) -> AsyncIterator[str]:
    yield _sse("run_started", {"thread_id": request.thread_id, "mode": "live"})
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
        yield _sse("run_failed", {"message": str(exc), "can_use_demo": True})
    finally:
        if async_checkpointer and getattr(async_checkpointer, "conn", None):
            await async_checkpointer.conn.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/runs")
async def run_agent(request: RunRequest) -> StreamingResponse:
    request.thread_id = request.thread_id or str(uuid.uuid4())
    events = _demo_events(request) if request.mode == "demo" else _live_events(request)
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
