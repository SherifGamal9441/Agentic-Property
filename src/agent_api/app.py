"""Public FastAPI/SSE boundary for the Aizen decision journey."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from src.buyer_brief import BuyerBrief, brief_to_filters
from src.llm.factory import get_llm
from src.utils import parse_llm_json


SNAPSHOT_DATE = os.getenv("AIZEN_SNAPSHOT_DATE", "2026-07-02")
SNAPSHOT_ID = os.getenv("AIZEN_SNAPSHOT_ID", f"active-{SNAPSHOT_DATE}-v1")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8000").rstrip("/")
RUN_TIMEOUT_SECONDS = float(os.getenv("AIZEN_RUN_TIMEOUT_SECONDS", "120"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Aizen Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class BriefInterpretRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1_000)
    thread_id: str | None = None


class RunRequest(BaseModel):
    brief: BuyerBrief
    thread_id: str | None = None


class AreaCompareRequest(BaseModel):
    areas: list[str] = Field(min_length=2, max_length=3)
    property_type: str | None = None
    beds: int | None = Field(default=None, ge=0)


_NODE_LABELS = {
    "memory": "Restoring this research session",
    "query_relevancy": "Checking Dubai property scope",
    "query_understanding": "Validating your structured brief",
    "query_routing": "Searching the listing data snapshot",
    "web_search": "Checking cited market sources",
    "comparison_engine": "Evaluating criteria deterministically",
    "reflection": "Auditing evidence and score arithmetic",
    "answer_generation": "Preparing concise buyer guidance",
}


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"


def _safe_failure(_: Exception) -> dict[str, Any]:
    return {
        "code": "agent_unavailable",
        "message": "Aizen could not complete this live run. Check the selected model provider and try again.",
        "retryable": True,
    }


def _interpret_brief(query: str) -> BuyerBrief:
    """Use the configured live model, allowing one schema-repair attempt."""
    schema = json.dumps(BuyerBrief.model_json_schema(), ensure_ascii=False)
    system = SystemMessage(content=(
        "Extract a Dubai property buyer brief as JSON only. Use only fields allowed by the schema. "
        "Lifestyle wishes that the dataset cannot prove must use field/operator/value null and verifiable false. "
        "Use stable short ids and buyer-readable labels. Never invent a criterion. Schema: " + schema
    ))
    llm = get_llm(streaming=False)
    response = llm.invoke([system, HumanMessage(content=query)])
    raw = str(response.content).strip()
    for attempt in range(2):
        try:
            return BuyerBrief.model_validate(parse_llm_json(raw))
        except (ValidationError, json.JSONDecodeError, TypeError, ValueError):
            if attempt == 1:
                break
            repair = llm.invoke([
                system,
                HumanMessage(content=(
                    "The previous response was not valid for the schema. Return one corrected JSON object only. "
                    f"Original buyer request: {query}"
                )),
            ])
            raw = str(repair.content).strip()
    raise ValueError("The selected model could not produce a valid buyer brief.")


def _market_context(area: str, property_type: str | None = None, beds: int | None = None) -> dict[str, Any]:
    try:
        query: dict[str, Any] = {"area": area}
        if property_type:
            query["property_type"] = property_type
        if beds is not None:
            query["beds"] = beds
        with urlopen(f"{DATA_SERVICE_URL}/market-context?{urlencode(query)}", timeout=3) as response:
            return json.loads(response.read())
    except Exception:
        return {"area": area, "unavailable": True, "evidence_quality": "insufficient"}


def _property_payloads(state: dict[str, Any]) -> list[dict[str, Any]]:
    listings = state.get("retrieved_properties") or []
    raw_by_id = {str(item.get("property_id") or item.get("id") or index): item for index, item in enumerate(listings)}
    comparisons = (state.get("comparison_result") or {}).get("properties") or []
    properties: list[dict[str, Any]] = []
    for index, comparison in enumerate(comparisons):
        if comparison.get("suitability") == "excluded":
            continue
        key = str(comparison.get("id") or comparison.get("property_id") or index)
        raw = raw_by_id.get(key)
        if raw is None:
            continue
        area = raw.get("area_name") or raw.get("location") or "Dubai"
        latitude, longitude = raw.get("latitude"), raw.get("longitude")
        matched = comparison.get("matched_criteria") or []
        conflicts = comparison.get("conflicting_criteria") or []
        properties.append({
            "id": key,
            "title": comparison.get("title") or raw.get("title") or raw.get("building_name") or raw.get("address") or f"{area} residence",
            "area": area,
            "price": raw.get("price"),
            "currency": "AED",
            "beds": raw.get("beds") if raw.get("beds") is not None else raw.get("bedrooms"),
            "baths": raw.get("baths") if raw.get("baths") is not None else raw.get("bathrooms"),
            "property_type": raw.get("type") or raw.get("property_type"),
            "furnishing": raw.get("furnishing"),
            "completion_status": raw.get("completion_status"),
            "building_name": raw.get("building_name"),
            "building_total_area_sqft": raw.get("building_total_area_sqft", raw.get("total_building_area_sqft")),
            "building_total_parking_spaces": raw.get("building_total_parking_spaces", raw.get("total_parking_spaces")),
            "building_floors": raw.get("building_floors", raw.get("total_floors")),
            "building_elevators": raw.get("building_elevators", raw.get("elevators")),
            "year_of_completion": raw.get("year_of_completion"),
            "latitude": latitude,
            "longitude": longitude,
            "location_status": "exact" if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)) else "unavailable",
            "source_url": raw.get("link"),
            "source_name": "Captured listing source" if raw.get("link") else None,
            "observed_at": str(raw["post_date"]) if raw.get("post_date") else None,
            "snapshot_id": SNAPSHOT_ID,
            "dataset_snapshot_at": SNAPSHOT_DATE,
            "data_status": "listing_snapshot",
            "fit_score": comparison.get("fit_score"),
            "evidence_coverage": comparison.get("evidence_coverage"),
            "suitability": comparison.get("suitability", "conditional"),
            "evaluations": comparison.get("evaluations", []),
            "score_factors": matched or [],
            "matched_criteria": matched or [],
            "conflicting_criteria": conflicts or [],
            "unknown_criteria": comparison.get("unknown_criteria", []),
            "unsupported_criteria": comparison.get("unsupported_criteria", []),
            "unmatched_criteria": comparison.get("unmatched_criteria", conflicts or []),
            "price_assessment": "unavailable",
            "data_intent": "recommend",
            "data_source": "active",
        })
    return properties


def _source_items(properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"title": item["title"], "url": item["source_url"], "observed_at": item["observed_at"], "kind": "captured_listing"}
        for item in properties if item.get("source_url")
    ]


def _web_source_items(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": item.get("title") or "Web source",
            "url": item.get("url"),
            "observed_at": item.get("publication_date") or item.get("retrieved_at"),
            "kind": "web_research",
        }
        for item in state.get("web_search_results", [])
        if item.get("url")
    ]


def _active_match_count(brief: BuyerBrief) -> int:
    body = json.dumps(brief_to_filters(brief)).encode("utf-8")
    request = Request(f"{DATA_SERVICE_URL}/search/active", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=3) as response:
            return int(json.loads(response.read()).get("total_matches", 0))
    except Exception:
        return 0


async def _relaxation_options(brief: BuyerBrief) -> list[dict[str, Any]]:
    options = []
    for criterion in brief.criteria:
        if criterion.priority not in {"must_have", "deal_breaker"}:
            continue
        relaxed = brief.model_copy(update={"criteria": [item for item in brief.criteria if item.id != criterion.id]})
        count = await asyncio.to_thread(_active_match_count, relaxed)
        options.append({"criterion_id": criterion.id, "resulting_match_count": count})
    return options


async def _live_events(request: RunRequest) -> AsyncIterator[str]:
    yield _sse("run_started", {"thread_id": request.thread_id, "snapshot_id": SNAPSHOT_ID})
    async_checkpointer = None
    started: dict[str, float] = {}
    try:
        from src.agents.graph import build_graph
        from src.memory.long_term_memory import create_async_checkpointer

        async_checkpointer = await create_async_checkpointer()
        graph = build_graph(checkpointer=async_checkpointer)
        config = {"configurable": {"thread_id": request.thread_id}}
        final_state: dict[str, Any] = {}
        graph_input = {"query": request.brief.original_query, "buyer_brief": request.brief.model_dump()}
        async with asyncio.timeout(RUN_TIMEOUT_SECONDS):
            async for event in graph.astream_events(graph_input, config=config, version="v2"):
                name, kind = event.get("name", ""), event.get("event", "")
                if kind == "on_chain_start" and name in _NODE_LABELS:
                    started[name] = time.perf_counter()
                    yield _sse("agent_step", {"node": name, "label": _NODE_LABELS[name], "status": "started"})
                elif kind == "on_chain_end" and name in _NODE_LABELS:
                    duration = round((time.perf_counter() - started.get(name, time.perf_counter())) * 1000)
                    yield _sse("agent_step", {"node": name, "label": _NODE_LABELS[name], "status": "completed", "duration_ms": duration})
                elif (
                    request.brief.mode != "property_search"
                    and kind == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") == "answer_generation"
                ):
                    token = event["data"]["chunk"].content
                    if token:
                        yield _sse("answer_token", {"token": token})
                elif kind == "on_chain_end" and name == "LangGraph":
                    output = event["data"].get("output", {})
                    final_state = output.model_dump() if hasattr(output, "model_dump") else output

        properties = _property_payloads(final_state)
        comparison = final_state.get("comparison_result") or {}
        candidate_count = int(final_state.get("candidate_count") or comparison.get("candidate_count") or min(20, len(final_state.get("retrieved_properties") or [])))
        audited_count = int(final_state.get("audited_count") or comparison.get("audited_count") or candidate_count)
        yield _sse("properties", {
            "candidate_count": candidate_count,
            "audited_count": audited_count,
            "total_matches": len(properties),
            "shown_count": min(6, len(properties)),
            "properties": properties,
        })
        yield _sse("sources", {"items": _source_items(properties) + _web_source_items(final_state)})
        if request.brief.mode == "property_search" and final_state.get("buyer_guidance"):
            guidance = final_state["buyer_guidance"]
            yield _sse("guidance", {"guidance": guidance.model_dump() if hasattr(guidance, "model_dump") else guidance})
        if request.brief.mode == "property_search" and not properties:
            yield _sse("relaxation_options", {"criteria": await _relaxation_options(request.brief)})
        coverages = [item.get("evidence_coverage", 0) or 0 for item in properties]
        quality = "strong" if coverages and min(coverages) >= 0.8 else ("limited" if properties else "insufficient")
        yield _sse("run_completed", {"route": final_state.get("route"), "data_source": final_state.get("data_source"), "evidence_quality": quality})
    except Exception as exc:
        logger.exception("Live agent run failed for thread %s", request.thread_id)
        yield _sse("run_failed", _safe_failure(exc))
    finally:
        if async_checkpointer and getattr(async_checkpointer, "conn", None):
            await async_checkpointer.conn.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/briefs/interpret", response_model=BuyerBrief)
async def interpret_brief(request: BriefInterpretRequest) -> BuyerBrief:
    try:
        return await asyncio.to_thread(_interpret_brief, request.query)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Aizen could not structure that request. Rephrase it with area, budget, and home requirements.") from exc


@app.get("/api/market-context")
async def market_context(area: str = Query(min_length=1), property_type: str | None = Query(default=None, min_length=1), beds: int | None = Query(default=None, ge=0)) -> dict[str, Any]:
    return _market_context(area, property_type, beds)


@app.post("/api/areas/compare")
async def compare_areas(request: AreaCompareRequest) -> dict[str, Any]:
    return {"areas": [_market_context(area, request.property_type, request.beds) for area in request.areas]}


@app.get("/api/conversations/{thread_id}")
async def conversation_history(thread_id: uuid.UUID) -> dict[str, Any]:
    from src.agents.graph import build_graph
    from src.memory.long_term_memory import create_async_checkpointer

    checkpointer = await create_async_checkpointer()
    try:
        state = await build_graph(checkpointer=checkpointer).aget_state({"configurable": {"thread_id": str(thread_id)}})
        values = getattr(state, "values", {}) or {}
        messages = [{"role": item["role"], "content": item["content"]} for item in values.get("conversation_history", []) if item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str)]
        if not messages:
            raise HTTPException(status_code=404, detail="Research conversation is unavailable.")
        brief = values.get("buyer_brief")
        if hasattr(brief, "model_dump"):
            brief = brief.model_dump()
        return {
            "thread_id": str(thread_id),
            "messages": messages,
            "last_confirmed_brief": brief,
            "properties": _property_payloads(values),
            "snapshot": {"id": SNAPSHOT_ID, "date": SNAPSHOT_DATE},
        }
    finally:
        if getattr(checkpointer, "conn", None):
            await checkpointer.conn.close()


@app.post("/api/runs")
async def run_agent(request: RunRequest) -> StreamingResponse:
    request.thread_id = request.thread_id or str(uuid.uuid4())
    return StreamingResponse(
        _live_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
