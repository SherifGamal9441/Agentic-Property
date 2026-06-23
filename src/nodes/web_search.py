import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agents.state import AgentState
from ddgs import DDGS
from src.llm.factory import get_llm
import logging
import re
from langgraph.graph import END,StateGraph


logger = logging.getLogger(__name__)

#lets define the llm
LLM = get_llm(streaming=True)

# thinking stripper
# falls back to full content for non-thinking models

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


#lets create the user query to web search query rewriter node
#lets create the user query to web search query rewriter node
def rewrite_to_search_query(state: AgentState) -> AgentState:
    """Rewrite the user query to a more specific web search query."""
    logger.info(f"Original query: {state.query}")
    logger.info("Rewriting user query to web search query")
    query = state.query
    rewritten_query = _strip_think(LLM.invoke([
        {"role": "system", "content": """You are a professional query rewriter. Convert the user's query into a web-search-optimized query 
        for better search results about property listings in Dubai. Focus on extracting key entities and intent. Output ONLY the rewritten query. No explanation, no analysis."""},
        {"role": "user", "content": f"Rewrite this query for web search: {query}"}
    ]).content)
    state.web_search_query = rewritten_query
    logger.info(f"Rewritten web search query: {state.web_search_query}")
    return state

# Web search function
def web_search(state: AgentState) -> AgentState:
    """Search the web."""
    logger.info(f"Searching the web for: {state.web_search_query}")
    with DDGS() as ddgs:
        results = list(ddgs.text(state.web_search_query, max_results=5))

    state.web_search_results = [
        {
            "title": r["title"],
            "url": r["href"],
            "snippet": r["body"]
        }
        for r in results
    ]
    logger.info(f"Web search completed with {len(state.web_search_results)} results")
    return state



# now the node to summerise the web search results given the user question context too
def summarize_web_search_results(state: AgentState) -> AgentState:
    logger.info("Summarizing web search results")

    prompt = f"""
    User Question:
    {state.query}
    
    Web Search Results:
    {state.web_search_results}
    
    Summarize the search results relevant to answering the user's question.
    Focus on:
    - Property listings
    - Prices
    - Locations
    - Property features
    - Any market insights

    Ignore irrelevant information.
    Keep the summary concise and factual.
    """
    summary = _strip_think(
        LLM.invoke([
            {"role": "system", "content": "You summarize real estate search results for downstream reasoning."},
            {"role": "user", "content": prompt}]).content)
    state.web_search_summary = summary
    logger.info(f"Web search summary: {summary}")
    return state



# lets create a node to check if the web search was successful
def check_web_search_success(state: AgentState) -> AgentState:
    """Check if the web search was successful."""
    state.web_search_success = bool(state.web_search_summary)
    logger.info(f"Web search success: {state.web_search_success}")
    return state

#now lets create an agent for all the nodes so we integrate them with the rest of the system as one just node
def create_web_search_agent():
    """Create a web search agent with all the nodes."""
    web_search_agent = StateGraph(AgentState)
    
    # Add nodes
    web_search_agent.add_node("rewrite_query", rewrite_to_search_query)
    web_search_agent.add_node("web_search", web_search)
    web_search_agent.add_node("summarize_results", summarize_web_search_results)
    web_search_agent.add_node("check_success", check_web_search_success)
    
    # Set entry point
    web_search_agent.set_entry_point("rewrite_query")
    
    # Add edges
    web_search_agent.add_edge("rewrite_query", "web_search")
    web_search_agent.add_edge("web_search", "summarize_results")
    web_search_agent.add_edge("summarize_results", "check_success")
    web_search_agent.add_edge("check_success", END)
    
    # Compile
    return web_search_agent.compile()
