import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agents.state import AgentState
from ddgs import DDGS
from src.llm.factory import get_llm
import logging
from langgraph.graph import END,StateGraph


logger = logging.getLogger(__name__)

#lets define the llm
LLM = get_llm()



#lets create the user query to web search query rewriter node
def rewrite_to_search_query(state: AgentState) -> AgentState:
    """Rewrite the user query to a more specific web search query."""
    logger.info(f"Original query: {state.query}")
    logger.info("Rewriting user query to web search query")
    query = state.query
    rewritten_query = LLM.invoke([
        {"role": "system", "content": "You are a query to web search professional rewriter. Convert the user's query into a concise, web-search-optimized query."},
        {"role": "user", "content": f"Rewrite this query for web search: {query}"}
    ]).content.split("</think>")[1].strip()
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
    """Summarize the web search results given the user question context."""
    logger.info("Summarizing web search results")
    summary = LLM.invoke([
        {"role": "system", "content": "You are a web search result summarizer. Summarize the web search results given the user question context."},
        {"role": "user", "content": f"Summarize the following web search results: {state.web_search_results}\n\nThe user's question is: {state.web_search_query}"}
    ]).content.split("</think>")[1].strip()
    state.web_search_summary = summary
    logger.info(f"Web search summary: {state.web_search_summary}")
    return state


# lets create a node to check if the web search was successful
def check_web_search_success(state: AgentState) -> AgentState:
    """Check if the web search was successful."""
    logger.info("Checking web search success")
    if state.web_search_summary:
        state.web_search_success = True
    else:
        state.web_search_success = False
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


#lets test the web search agent
if __name__ == "__main__":
    web_search_agent = create_web_search_agent()
    result = web_search_agent.invoke(AgentState(query="france vs iraq world cup last night"))
    print(type(result))



