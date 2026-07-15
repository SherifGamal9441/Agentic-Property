import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agents.state import AgentState
from ddgs import DDGS
from src.llm.factory import get_llm
import logging
import re
from datetime import date
from langgraph.graph import END, StateGraph

from pathlib import Path as _Path2
import yaml

_PROMPTS_DIR2 = _Path2(__file__).parent.parent / "prompts"

logger = logging.getLogger(__name__)

LLM = get_llm(streaming=True)

# thinking stripper
_THINK_PATTERNS = [
    r"</?think>$",
    r"\*\*\s*\n?"
]


def _strip_think(content: str) -> str:
    """Strip model thinking tokens, returning the substantive answer."""
    for pattern in _THINK_PATTERNS:
        parts = re.split(pattern, content, maxsplit=1)
        if len(parts) > 1:
            return parts[-1].strip()
    return content.strip()


def rewrite_to_search_query(state: AgentState) -> dict:
    """Rewrite the user query to a more specific web search query."""
    logger.info("Original query: %s", state.query)
    _PROMPTS = yaml.safe_load((_PROMPTS_DIR2 / "web_search.yaml").read_text(encoding="utf-8"))
    rewritten = _strip_think(LLM.invoke([
        {"role": "system", "content": _PROMPTS["rewrite_system"]},
        {"role": "user", "content": _PROMPTS["rewrite_user"].format(query=state.query)},
    ]).content)
    logger.info("Rewritten web search query: %s", rewritten)
    return {"web_search_query": rewritten}


def web_search(state: AgentState) -> dict:
    """Search the web."""
    logger.info("Searching the web for: %s", state.web_search_query)
    web_results = []
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(state.web_search_query, max_results=5))
        web_results = [
            {"title": r["title"], "url": r["href"], "snippet": r["body"], "publication_date": r.get("date"), "retrieved_at": date.today().isoformat()}
            for r in results
        ]
        if not web_results:
            raise ValueError("No results returned by DuckDuckGo")
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s. Falling back to Tavily.", e)
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            logger.error("TAVILY_API_KEY not found. Web search failed entirely.")
        else:
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=tavily_key)
                response = tavily.search(query=state.web_search_query, max_results=5)
                web_results = [
                    {"title": r["title"], "url": r["url"], "snippet": r["content"], "publication_date": r.get("published_date"), "retrieved_at": date.today().isoformat()}
                    for r in response.get("results", [])
                ]
            except Exception as tavily_e:
                logger.error("Tavily search also failed: %s", tavily_e)
        
    logger.info("Web search completed with %d results", len(web_results))
    return {"web_search_results": web_results}


def summarize_web_search_results(state: AgentState) -> dict:
    """Summarize web search results given the user question."""
    logger.info("Summarizing web search results")
    _PROMPTS = yaml.safe_load((_PROMPTS_DIR2 / "web_search.yaml").read_text(encoding="utf-8"))
    summary = _strip_think(LLM.invoke([
        {"role": "system", "content": _PROMPTS["summarize_system"]},
        {"role": "user", "content": _PROMPTS["summarize_user"].format(
            query=state.query,
            web_search_results=state.web_search_results
        )},
    ]).content)
    logger.info("Web search summary: %s", summary)
    return {"web_search_summary": summary}


def create_web_search_agent():
    """Create a web search agent with all the nodes."""
    web_search_agent = StateGraph(AgentState)

    web_search_agent.add_node("rewrite_query", rewrite_to_search_query)
    web_search_agent.add_node("web_search", web_search)
    web_search_agent.add_node("summarize_results", summarize_web_search_results)

    web_search_agent.set_entry_point("rewrite_query")

    web_search_agent.add_edge("rewrite_query", "web_search")
    web_search_agent.add_edge("web_search", "summarize_results")
    web_search_agent.add_edge("summarize_results", END)

    return web_search_agent.compile()
