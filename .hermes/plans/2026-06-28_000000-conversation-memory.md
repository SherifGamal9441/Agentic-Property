# Conversation Memory — Long-Term Memory for LangGraph Agent with Streamlit Chat UI

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Give the agent true conversational memory: each chat in the Streamlit sidebar is an isolated thread that persists across sessions, the agent remembers prior turns and can answer meta-questions like "what was my last question?", and conversation history survives both Streamlit restarts and agent restarts.

**Architecture:** A new `memory` node runs first in the graph, building a `conversation_context` string from persisted `conversation_history`. The `answer_generation` node appends each user/assistant pair to history. The `thread_id` (UUID per chat) is passed via `graph.invoke(config=...)` so LangGraph's `SqliteSaver` isolates state per chat. The Streamlit UI generates thread IDs and persists chat metadata to a JSON file so the sidebar survives restarts.

**Tech Stack:** LangGraph 1.x + SqliteSaver (already in place), Pydantic v2, Streamlit 1.58

**Current gap:** The `SqliteSaver` singleton and `graph.compile(checkpointer=...)` are correct. LangGraph IS persisting state. But:
1. `main.py` calls `graph.invoke({"query": prompt})` — no `config` with `thread_id`, so every query is a fresh, unthreaded invocation
2. `scripts/run_cli.py` uses a single hardcoded `thread_id="user1"` for all queries
3. `AgentState` has no conversation history field — no node reads or writes past turns
4. No LLM prompt includes prior conversation context
5. The Streamlit sidebar stores chat history in `st.session_state` only (lost on restart)

---

## Design Decisions

### D1: Where to inject conversation context
**Decision:** A dedicated `memory` node at `START → memory → query_relevancy → ...`.

**Why not inject in query_relevancy directly:** That node is a gatekeeper — it rejects non-Dubai queries. If we inject context there, meta-questions ("what was my last question?") still get rejected before the LLM sees the conversation context. A separate node BEFORE the gatekeeper can detect meta-questions and short-circuit the pipeline.

**Why not inject in every node:** Each node already has its own prompt structure. Adding conversation context to all 5+ nodes is high blast radius and easy to miss. A single `conversation_context` field built once at the start is DRY.

### D2: Thread ID management
**Decision:** UUID per chat, generated in Streamlit, stored alongside chat metadata in a JSON file.

**Why UUID:** Guarantees uniqueness across sessions. LangGraph's `SqliteSaver` already indexes by `thread_id` — no schema changes needed.

**Why JSON file, not SQLite for chat metadata:** The SqliteSaver DB is LangGraph's internal format. Chat metadata (titles, timestamps, thread_id → display mapping) is app-level and needs to survive Streamlit restarts independently. A simple JSON file is adequate for O(100) chats.

### D3: Meta-question handling
**Decision:** The `memory` node detects meta-questions (queries about the conversation itself) and short-circuits straight to `answer_generation`, skipping the property pipeline entirely.

**Why not let the Dubai gatekeeper handle it:** A meta-question like "what did I ask before?" isn't about Dubai real estate. The query_relevancy gatekeeper will reject it. Instead, the memory node routes meta-questions directly to answer_generation with the conversation history as the data source.

### D4: Conversation history format
**Decision:** `list[dict]` with `{"role": "user"|"assistant", "content": str}` — same shape as OpenAI/LangChain message format.

**Why not LangChain Message objects:** LangChain messages are not trivially JSON-serializable for checkpoint persistence. Plain dicts serialize cleanly and are easy to format into prompt strings.

---

## Task List

### Phase 1: State Schema Changes

#### Task 1: Add conversation fields to AgentState
**Objective:** Add `conversation_history` and `conversation_context` fields to the pydantic state model.

**Files:**
- Modify: `src/agents/state.py`

**Step 1: Add fields**

Add after the `final_answer` field (end of class):

```python
    # ── Conversation memory ──────────────────────────────────────────────────
    conversation_history: list[dict] = []
    """Accumulated user/assistant message pairs across turns.
    Shape: [{"role": "user"|"assistant", "content": str}, ...]"""

    conversation_context: str = ""
    """Pre-formatted string of recent conversation history, ready to inject
    into LLM prompts. Built by the memory node at the start of each turn."""
```

**Step 2: Verify**
Run: `python -c "from src.agents.state import AgentState; s = AgentState(); print(s.conversation_history, s.conversation_context)"`
Expected: `[]` and `""`

---

### Phase 2: Memory Node

#### Task 2: Create the memory node
**Objective:** A new node that runs FIRST in the graph. It builds `conversation_context` from history, detects meta-questions, and either short-circuits or lets the pipeline continue.

**Files:**
- Create: `src/nodes/memory.py`
- Create: `src/prompts/memory.yaml`

**Step 1: Create prompt file `src/prompts/memory.yaml`**

```yaml
system_prompt: |
  You are a conversation memory manager for a Dubai real estate assistant.

  Your job is to determine if the user's query is a "meta" question ABOUT the conversation itself.
  
  Meta questions are queries where the user asks about:
  - What they asked previously ("what was my last question?", "what did I ask before?")
  - Summarizing the conversation ("summarize what we discussed", "what have we talked about?")
  - The conversation history ("do you remember what I said?", "what did you tell me earlier?")
  - Clarifying or repeating previous answers ("can you repeat that?", "what was that property again?")
  
  Non-meta questions are normal Dubai property queries — even if they reference prior conversation
  (like "compare it with the previous one" — that's a property query with context, not a meta question).

  Return ONLY valid JSON — no prose, no markdown fences:
  {
    "is_meta": true | false,
    "reason": "<one short sentence>"
  }

user_prompt_template: "User query: {query}\n\nConversation history so far:\n{conversation_history}"
```

**Step 2: Create memory node `src/nodes/memory.py`**

```python
"""
Memory Node

Runs FIRST in the graph pipeline. Two responsibilities:
  1. Build conversation_context from conversation_history for downstream nodes.
  2. Detect meta-questions (queries about the conversation itself) and
     short-circuit the pipeline — skipping the property nodes entirely
     and passing only conversation history to answer_generation.

Writes to state:
    conversation_context: str
    route: str | None        — set to "memory_direct" for meta-questions
"""

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("memory.yaml")
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]

_MAX_HISTORY_TURNS = 10  # keep context manageable for small models


def _format_history_for_context(history: list[dict]) -> str:
    """Format conversation history as a readable string for prompt injection."""
    if not history:
        return "(No prior conversation — this is the first message.)"
    
    # Take last N messages to keep context window small
    recent = history[-(_MAX_HISTORY_TURNS * 2):]
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate long messages
        if len(content) > 300:
            content = content[:297] + "..."
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def memory_node(state: AgentState) -> dict:
    """
    LangGraph node: prepare conversation context and detect meta-questions.

    Args:
        state: Current AgentState. Reads conversation_history and query.

    Returns:
        Partial state dict with conversation_context populated.
        If meta-question detected, also sets route="memory_direct".
    """
    logger.info("memory: building conversation context (%d prior turns)",
                len(state.conversation_history) // 2)

    # Build conversation context for downstream nodes
    context = _format_history_for_context(state.conversation_history)

    # Check if this is a meta-question about the conversation itself
    if state.conversation_history:
        llm = get_llm(streaming=False)
        user_message = _USER_PROMPT_TEMPLATE.format(
            query=state.query,
            conversation_history=context,
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                logger.warning("memory: could not parse meta-detection response, assuming non-meta")
                result = {"is_meta": False}

        is_meta = result.get("is_meta", False)
        if is_meta:
            logger.info("memory: meta-question detected — short-circuiting to answer_generation")
            return {
                "conversation_context": context,
                "route": "memory_direct",
            }

    return {"conversation_context": context}


def route_after_memory(state: AgentState) -> str:
    """
    Called by LangGraph's add_conditional_edges after memory_node runs.

    Returns:
        "query_relevancy" — normal pipeline
        "answer_generation" — meta-question, skip the pipeline
    """
    if state.route == "memory_direct":
        return "answer_generation"
    return "query_relevancy"
```

**Step 3: Verify**
Run: `python -c "from src.nodes.memory import memory_node; print('import ok')"`
Expected: `import ok`

---

### Phase 3: Wire Memory Node into Graph

#### Task 3: Add memory node to graph
**Objective:** Add the memory node at START → memory → (conditional edge), and add history-appending after answer_generation.

**Files:**
- Modify: `src/agents/graph.py`

**Step 1: Add memory node to graph**

Changes to `build_graph()`:

```python
from src.nodes.memory import memory_node, route_after_memory

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # ── Register nodes ──
    graph.add_node("memory", memory_node)  # ← NEW: first node
    graph.add_node("query_relevancy", query_relevancy_node)
    # ... rest unchanged

    # ── Entry → memory → query_relevancy or answer_generation ──
    graph.add_edge(START, "memory")
    graph.add_conditional_edges(
        "memory",
        route_after_memory,
        {
            "query_relevancy": "query_relevancy",
            "answer_generation": "answer_generation",
        },
    )

    # ── After relevancy: proceed or end ── (unchanged)
    graph.add_conditional_edges(
        "query_relevancy",
        route_after_relevancy,
        {
            "query_understanding": "query_understanding",
            "end": END,
        },
    )
    # ... rest unchanged
```

**Step 2: Verify**
Run: `python -c "from src.agents.graph import build_graph; g = build_graph(); print('graph built, nodes:', list(g.nodes.keys()))"`
Expected: `graph built, nodes: ['memory', 'query_relevancy', ...]`

---

### Phase 4: Update Existing Nodes to Use Conversation Context

#### Task 4: Update query_relevancy to include conversation context
**Objective:** The gatekeeper node should see prior conversation so it can understand follow-up queries.

**Files:**
- Modify: `src/nodes/query_relevancy.py`
- Modify: `src/prompts/query_relevancy.yaml`

**Step 1: Update prompt**

Add to `query_relevancy.yaml` system_prompt (at the end, before the JSON instruction):

```yaml
  When the user's query is a follow-up to prior conversation, use the conversation
  context to understand what they're asking about. Even brief queries like "tell me
  more" or "what about a 3BR instead?" are relevant if the conversation is about
  Dubai real estate.
```

And update `user_prompt_template`:

```yaml
user_prompt_template: |
  Conversation history:
  {conversation_context}
  
  Classify this query: {query}
```

**Step 2: Update node function**

In `query_relevancy_node`, change the messages construction:

```python
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_USER_PROMPT_TEMPLATE.format(
            query=state.query,
            conversation_context=state.conversation_context,
        )),
    ]
```

**Step 3: Verify**
Run existing tests: `uv run pytest tests/nodes/test_query_relevancy.py -v`
These will likely FAIL because tests seed state without `conversation_context`. Update test fixtures.

#### Task 5: Update answer_generation to append history
**Objective:** After generating the final answer, append the user query + assistant answer to `conversation_history`.

**Files:**
- Modify: `src/nodes/answer_generation.py`

**Step 1: Update node return value**

In `answer_generation_node`, after computing `final_answer`, append to history:

```python
def answer_generation_node(state: AgentState) -> dict:
    # ... existing LLM call and streaming unchanged ...
    
    final_answer = "".join(chunks)
    
    # Append this turn to conversation history
    new_entry = [
        {"role": "user", "content": state.query},
        {"role": "assistant", "content": final_answer},
    ]
    updated_history = state.conversation_history + new_entry
    
    logger.info("answer_generation: response complete (%d chars, %d total turns)",
                len(final_answer), len(updated_history) // 2)
    
    return {
        "final_answer": final_answer,
        "conversation_history": updated_history,
    }
```

**Step 2: Include conversation_context in prompts**

In `_build_messages`, include conversation context for all paths. Add context to the system prompt or as a separate message. Simplest: prepend to the system prompt:

```python
def _build_messages(state: AgentState) -> list:
    # Build a system prompt that includes conversation context
    system_with_context = _SYSTEM_PROMPT
    if state.conversation_context and state.conversation_context != "(No prior conversation — this is the first message.)":
        system_with_context += f"\n\nPrior conversation for context:\n{state.conversation_context}"
    
    # ... rest of function uses system_with_context instead of _SYSTEM_PROMPT ...
```

For the meta-question path (`route == "memory_direct"` and no property data available), handle specially:

```python
    # ── Meta-question / memory direct path ──
    if state.route == "memory_direct":
        logger.info("answer_generation: memory direct path (meta-question)")
        user_content = (
            f"User query: {state.query}\n\n"
            f"Here is the conversation history. Answer based on what you find in it. "
            f"If you cannot answer from the history, say so honestly.\n\n"
            f"{state.conversation_context}"
        )
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]
```

**Step 3: Verify**
Run: `python -c "from src.nodes.answer_generation import answer_generation_node; print('import ok')"`
Expected: `import ok`

#### Task 6: Update other LLM-calling nodes to include conversation context
**Objective:** `query_understanding`, `comparison_engine`, and `reflection` nodes should see conversation context for better follow-up understanding.

**Files:**
- Modify: `src/nodes/query_understanding.py` + `src/prompts/query_understanding.yaml`
- Modify: `src/nodes/comparison_engine.py` + `src/prompts/comparison_engine.yaml`

**Step 1: query_understanding**

In `query_understanding_node`, add `conversation_context` to the user prompt:

```python
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_USER_PROMPT_TEMPLATE.format(
            query=state.query,
            conversation_context=state.conversation_context,
        )),
    ]
```

Update `query_understanding.yaml` user_prompt_template:

```yaml
user_prompt_template: |
  Conversation history:
  {conversation_context}
  
  Parse and route this query: {query}
```

**Step 2: comparison_engine**

In `comparison_engine_node`, add context to the user message:

```python
    user_message = _USER_PROMPT_TEMPLATE.format(
        parsed_query=json.dumps(state.parsed_query, ensure_ascii=False, indent=2),
        retrieved_properties=json.dumps(properties, ensure_ascii=False, indent=2),
        conversation_context=state.conversation_context,
    )
```

Update `comparison_engine.yaml` user_prompt_template to include `{conversation_context}` at the top.

**Step 3: Verify**
Run: `python -c "from src.nodes.query_understanding import query_understanding_node; from src.nodes.comparison_engine import comparison_engine_node; print('imports ok')"`
Expected: `imports ok`

---

### Phase 5: Streamlit UI — Thread ID Management

#### Task 7: Generate and use thread_id in main.py
**Objective:** Each chat gets a UUID thread_id. Pass it to `graph.invoke()`. Persist chat metadata to JSON.

**Files:**
- Modify: `main.py`

**Step 1: Add imports and constants**

```python
import json
import uuid
from pathlib import Path

_CHAT_META_FILE = Path(__file__).parent / "chat_metadata.json"
```

**Step 2: Load/save chat metadata**

```python
def _load_chat_metadata() -> list[dict]:
    """Load persisted chat metadata (survives Streamlit restarts)."""
    if _CHAT_META_FILE.exists():
        try:
            return json.loads(_CHAT_META_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []

def _save_chat_metadata(chats: list[dict]) -> None:
    """Persist chat metadata to JSON file."""
    _CHAT_META_FILE.write_text(json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8")
```

**Step 3: Modify session state initialization**

Replace the current session state init:

```python
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = _load_chat_metadata()

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
```

Each chat entry in `chat_history` now has shape:
```python
{
    "thread_id": str,       # UUID
    "title": str,
    "messages": list[dict],  # {role, content, thinking}
    "created_at": str,       # ISO timestamp
}
```

**Step 4: Update `_start_new_chat`**

```python
def _start_new_chat():
    """Save current messages to history and start a fresh chat."""
    if st.session_state.messages:
        title = _make_title(st.session_state.messages)
        # Use existing thread_id if continuing an existing chat
        thread_id = st.session_state.current_thread_id or str(uuid.uuid4())
        
        # Update the existing entry if it's the current chat
        if st.session_state.current_chat_index is not None:
            idx = st.session_state.current_chat_index
            if idx < len(st.session_state.chat_history):
                st.session_state.chat_history[idx]["messages"] = list(st.session_state.messages)
                st.session_state.chat_history[idx]["title"] = title
        
    st.session_state.messages = []
    st.session_state.current_chat_index = None
    st.session_state.current_thread_id = str(uuid.uuid4())
    _save_chat_metadata(st.session_state.chat_history)
```

**Step 5: Update sidebar chat creation**

When user clicks "New Chat", create a new chat entry immediately:

```python
with st.sidebar:
    st.markdown("### Chat History")
    
    def _on_new_chat():
        if st.session_state.messages:
            title = _make_title(st.session_state.messages)
            thread_id = st.session_state.current_thread_id
            if thread_id:
                # Update existing or append new
                if st.session_state.current_chat_index is not None:
                    idx = st.session_state.current_chat_index
                    if idx < len(st.session_state.chat_history):
                        st.session_state.chat_history[idx] = {
                            "thread_id": thread_id,
                            "title": title,
                            "messages": list(st.session_state.messages),
                            "created_at": st.session_state.chat_history[idx].get("created_at", ""),
                        }
                else:
                    st.session_state.chat_history.append({
                        "thread_id": thread_id,
                        "title": title,
                        "messages": list(st.session_state.messages),
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    })
        st.session_state.messages = []
        st.session_state.current_chat_index = None
        st.session_state.current_thread_id = str(uuid.uuid4())
        _save_chat_metadata(st.session_state.chat_history)
    
    st.button("＋ New Chat", use_container_width=True, on_click=_on_new_chat)
```

**Step 6: Update sidebar chat list**

```python
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        idx = len(st.session_state.chat_history) - 1 - i
        label = chat["title"]
        if st.button(label, key=f"hist_{idx}", use_container_width=True):
            st.session_state.messages = list(chat["messages"])
            st.session_state.current_chat_index = idx
            st.session_state.current_thread_id = chat["thread_id"]
            st.rerun()
```

**Step 7: Pass thread_id to graph.invoke**

Replace the `agent_graph.invoke()` / `agent_graph.astream_events()` call:

```python
        # Inside the chat input handler:
        config = {"configurable": {"thread_id": st.session_state.current_thread_id}}
        
        async def _stream():
            first_token = True
            async for event in agent_graph.astream_events(
                {"query": prompt}, config=config, version="v2"
            ):
                # ... rest unchanged
```

**Step 8: Save chat on new messages**

After saving to session state (around line 300 in main.py), also save metadata:

```python
        # Save to session
        st.session_state.messages.append(
            {"role": "assistant", "content": full_answer, "thinking": thinking_text}
        )

        # Update chat metadata
        if st.session_state.current_chat_index is not None:
            idx = st.session_state.current_chat_index
            if idx < len(st.session_state.chat_history):
                st.session_state.chat_history[idx]["messages"] = list(
                    st.session_state.messages
                )
        else:
            # First message in a brand new chat — add to history
            title = _make_title(st.session_state.messages)
            st.session_state.chat_history.append({
                "thread_id": st.session_state.current_thread_id,
                "title": title,
                "messages": list(st.session_state.messages),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            st.session_state.current_chat_index = len(st.session_state.chat_history) - 1
        
        _save_chat_metadata(st.session_state.chat_history)
```

**Step 9: Verify**
Run: `python main.py` — Streamlit should start. Click New Chat, send a message, refresh the page. The sidebar should show the previous chat.

---

### Phase 6: CLI Update

#### Task 8: Support multiple threads in CLI
**Objective:** The CLI script should allow specifying a thread name (or generate one) for conversation isolation.

**Files:**
- Modify: `scripts/run_cli.py`

**Step 1: Replace hardcoded thread_id**

```python
import uuid

def main() -> None:
    print("Agentic Property — Dubai real estate assistant")
    print("Type your question, or 'quit' / 'exit' to stop.")
    print("Type 'new' to start a new conversation thread.\n")
    
    thread_id = str(uuid.uuid4())
    print(f"[Thread: {thread_id[:8]}...]\n")
    
    while True:
        try:
            query = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit"):
            print("Bye!")
            break
        if query.lower() == "new":
            thread_id = str(uuid.uuid4())
            print(f"\n[New thread: {thread_id[:8]}...]\n")
            continue

        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"\n{_DIVIDER}")
        result = agent_graph.invoke({"query": query}, config=config)
        # ... rest unchanged
```

**Step 2: Verify**
Run: `uv run python scripts/run_cli.py`
Ask: "show me apartments in Dubai Marina"
Then: "what was my last question?"
Expected: agent responds with the previous question.

---

### Phase 7: Tests

#### Task 9: Update existing graph test for new node
**Objective:** The graph now starts with `memory` node. Tests mock LLM calls — need to mock the memory node's LLM call too.

**Files:**
- Modify: `tests/agents/test_graph.py`

**Step 1: Add `src.nodes.memory.get_llm` to mock patches**

Each test that patches nodes needs an extra `@patch("src.nodes.memory.get_llm")`:

```python
@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
@patch("src.nodes.query_routing._call_cached_tool")
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
@patch("src.nodes.memory.get_llm")                         # ← NEW
def test_recommendation_path(
    mock_mem_llm, mock_rel_llm, mock_und_llm,              # ← params shift
    mock_cached_tool, mock_comp_llm, mock_refl_llm, mock_ans_llm
):
    # Memory node: not a meta question (empty history on first turn = no LLM call)
    mock_mem_llm.return_value = None  # won't be called with empty history
    # ... rest unchanged
```

Wait — actually the memory node only calls the LLM when `state.conversation_history` is non-empty. In tests, history starts empty, so the LLM won't be called. But the mock still needs to exist as a patch target. Set it to return `None` — it won't be called.

**Step 2: Verify tests pass**
Run: `uv run pytest tests/agents/test_graph.py -v`

#### Task 10: Create memory node unit test
**Objective:** Test the memory node with empty history, with history, and with meta-questions.

**Files:**
- Create: `tests/nodes/test_memory.py`

**Step 1: Test cases**

```python
"""Unit tests for memory node."""

import json
from unittest.mock import MagicMock, patch

from src.agents.state import AgentState
from src.nodes.memory import memory_node, route_after_memory


def test_empty_history_no_llm_call():
    """With empty history, no LLM is called, context shows first message."""
    state = AgentState(query="apartments in Dubai Marina", conversation_history=[])
    result = memory_node(state)
    assert "first message" in result["conversation_context"]
    assert result.get("route") != "memory_direct"


def test_with_history_builds_context():
    """With history, context is built and previous queries appear."""
    state = AgentState(
        query="what about a 3BR instead?",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert "Dubai Marina" in result["conversation_context"]
    assert "Marina Crest" in result["conversation_context"]


@patch("src.nodes.memory.get_llm")
def test_meta_question_detected(mock_llm):
    """Meta-question about conversation is detected and short-circuits."""
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"is_meta": True, "reason": "asks about prior question"})
    mock_llm.return_value.invoke.return_value = mock_resp

    state = AgentState(
        query="what was my last question?",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert result["route"] == "memory_direct"


@patch("src.nodes.memory.get_llm")
def test_normal_followup_not_meta(mock_llm):
    """Follow-up property query with history is NOT classified as meta."""
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"is_meta": False, "reason": "property follow-up"})
    mock_llm.return_value.invoke.return_value = mock_resp

    state = AgentState(
        query="show me villas instead",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert result.get("route") != "memory_direct"


def test_route_after_memory():
    """Router returns correct target based on state."""
    state = AgentState(route="memory_direct")
    assert route_after_memory(state) == "answer_generation"

    state = AgentState(route=None)
    assert route_after_memory(state) == "query_relevancy"
```

**Step 2: Verify**
Run: `uv run pytest tests/nodes/test_memory.py -v`
Expected: all pass.

---

### Phase 8: Integration Verification

#### Task 11: End-to-end thread isolation test
**Objective:** Verify that two different thread_ids produce independent conversation histories.

**Files:**
- Create: `tests/agents/test_thread_isolation.py`

```python
"""Integration test: thread isolation."""

import json
from unittest.mock import MagicMock, patch

from src.agents.graph import build_graph
from src.agents.state import AgentState

COMPARISON_RESULT = {
    "properties": [{
        "id": "prop-001", "title": "Marina Crest 2BR",
        "fit_score": 0.9, "matched_criteria": ["location"],
        "unmatched_criteria": [], "price_assessment": "below_market",
    }]
}
REFLECTION_OK = {"ok": True, "issues": [], "confidence": 0.9}


def _make_invoke_mock(content: str):
    resp = MagicMock()
    resp.content = content
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


def _make_stream_mock(tokens: list[str]):
    chunks = [MagicMock(content=t) for t in tokens]
    llm = MagicMock()
    llm.stream.return_value = iter(chunks)
    return llm


@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
@patch("src.nodes.query_routing.search_active_sync")
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
@patch("src.nodes.memory.get_llm")
def test_thread_isolation(
    mock_mem_llm, mock_rel_llm, mock_und_llm,
    mock_search, mock_comp_llm, mock_refl_llm, mock_ans_llm,
):
    """Two different thread_ids produce independent conversation histories."""
    # Memory node: no meta detection (empty history)
    mock_mem_llm.return_value = _make_invoke_mock(json.dumps({"is_meta": False}))
    # Relevancy
    mock_rel_llm.return_value = _make_invoke_mock(
        json.dumps({"relevant": True, "failed_rule": None, "reason": "valid"})
    )
    # Understanding
    mock_und_llm.return_value = _make_invoke_mock(json.dumps({
        "parsed_query": {"area_name": "Dubai Marina"},
        "route": "query_routing",
        "route_reason": "property search",
    }))
    # Search
    mock_search.return_value = [
        {"id": "prop-001", "title": "Marina Crest 2BR", "price": 1_750_000,
         "area_sqm": 110, "location": "Dubai Marina", "bedrooms": 2}
    ]
    mock_comp_llm.return_value = _make_invoke_mock(json.dumps(COMPARISON_RESULT))
    mock_refl_llm.return_value = _make_invoke_mock(json.dumps(REFLECTION_OK))
    mock_ans_llm.return_value = _make_stream_mock(["Marina ", "Crest ", "recommended."])

    graph = build_graph()

    thread_a = "thread-aaa"
    thread_b = "thread-bbb"

    # Turn 1 — Thread A
    result_a1 = graph.invoke(
        {"query": "2BR in Dubai Marina"},
        {"configurable": {"thread_id": thread_a}},
    )
    assert "Marina Crest" in result_a1["final_answer"]
    assert len(result_a1["conversation_history"]) == 2  # user + assistant

    # Turn 1 — Thread B (independent)
    result_b1 = graph.invoke(
        {"query": "villas in Palm Jumeirah"},
        {"configurable": {"thread_id": thread_b}},
    )
    assert len(result_b1["conversation_history"]) == 2  # independent history

    # Turn 2 — Thread A (accumulates)
    mock_ans_llm.return_value = _make_stream_mock(["Second ", "answer."])
    # Memory node for turn 2: LLM needs to not detect meta
    mock_mem_llm.return_value = _make_invoke_mock(json.dumps({"is_meta": False}))
    
    result_a2 = graph.invoke(
        {"query": "what about 3BR?"},
        {"configurable": {"thread_id": thread_a}},
    )
    assert len(result_a2["conversation_history"]) == 4  # 2 prior + 2 new

    # Verify Thread B is still independent
    assert len(result_b1["conversation_history"]) == 2  # unchanged
```

**Step 2: Run test**
Run: `uv run pytest tests/agents/test_thread_isolation.py -v`
Expected: pass.

---

## Summary of All Changes

| File | Action | Purpose |
|------|--------|---------|
| `src/agents/state.py` | Modify | Add `conversation_history` and `conversation_context` fields |
| `src/nodes/memory.py` | **Create** | New memory node — context builder + meta-question detector |
| `src/prompts/memory.yaml` | **Create** | Prompt for meta-question detection |
| `src/agents/graph.py` | Modify | Add memory node to graph, wire conditional edges |
| `src/nodes/query_relevancy.py` | Modify | Include conversation_context in prompts |
| `src/prompts/query_relevancy.yaml` | Modify | Add conversation context to user prompt template |
| `src/nodes/answer_generation.py` | Modify | Append to conversation_history, handle meta-questions |
| `src/nodes/query_understanding.py` | Modify | Include conversation_context in prompts |
| `src/prompts/query_understanding.yaml` | Modify | Add conversation context to user prompt template |
| `src/nodes/comparison_engine.py` | Modify | Include conversation_context in prompts |
| `src/prompts/comparison_engine.yaml` | Modify | Add conversation context to user prompt template |
| `main.py` | Modify | UUID thread_id per chat, persist chat metadata to JSON |
| `scripts/run_cli.py` | Modify | UUID thread_id, `new` command to switch threads |
| `tests/nodes/test_memory.py` | **Create** | Unit tests for memory node |
| `tests/agents/test_graph.py` | Modify | Add memory LLM mock to test patches |
| `tests/agents/test_thread_isolation.py` | **Create** | Integration test for thread isolation |

## Risks & Tradeoffs

1. **Extra LLM call on every turn** — The memory node calls the LLM to detect meta-questions whenever there's prior history. This adds latency (~1-2s with a local 4B model). Mitigation: the call is skipped on the very first turn (empty history). For production, the meta-detection could be done with a faster keyword/cache-based approach instead of LLM.

2. **Conversation_context can grow large** — Mitigated by `_MAX_HISTORY_TURNS = 10` capping the last 20 messages. For 4B-class models this is manageable.

3. **Prompt updates may break existing tests** — The `conversation_context` is injected into prompt templates. Tests that mock LLM calls and inspect prompt content may need updating.

4. **`chat_metadata.json` is not atomic** — If Streamlit crashes mid-write, the file may corrupt. For O(100) chats this is acceptable. For production, consider SQLite or atomic write (write to temp file, then rename).

5. **Graph topology change** — Adding the memory node shifts the START edge. All graph-plotting and existing integration tests need updating.

## Open Questions

- **Should `chat_metadata.json` store full messages or just metadata?** The plan stores full messages in JSON. For long conversations this could grow large. Alternative: store only `{thread_id, title, created_at, message_count}` and rely on `SqliteSaver` for message content. But this makes the sidebar slower (would need to query LangGraph's internal DB). Current approach is simpler.

- **Should the `memory` node be a subgraph?** Currently it's a single node. If meta-detection logic grows (e.g., conversation summarization for very long histories), it could become a subgraph. Leave as single node for now — YAGNI.

- **Should we compress old conversation history?** When history exceeds ~50 turns, the context window gets squeezed. The plan caps at 10 turns. For very long sessions, consider adding a summarization step. Out of scope for now.
