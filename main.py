"""
Agentic Property — Streamlit chat interface.

Warm gray + terracotta palette (ChatGPT-style with warm colors).
Sidebar: chat history. Main: messages + collapsible "thinking" dropdown.
Agent answer streams token-by-token via LangGraph astream_events.

Each chat in the sidebar is an isolated thread with its own UUID thread_id.
LangGraph's SqliteSaver persists conversation state per thread, so clicking
a chat resumes the conversation from where it left off.

Usage:
    uv run streamlit run main.py
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import streamlit as st

from src.agents.graph import build_graph
from src.memory.long_term_memory import create_async_checkpointer
from src.logging_setup import setup_file_logging

# ── Persisted chat metadata ────────────────────────────────────────────────────

_CHAT_META_FILE = Path(__file__).parent / "chat_metadata.json"


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
    _CHAT_META_FILE.write_text(
        json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Agentic Property", page_icon="🏠", layout="wide")

# ── Warm gray + terracotta CSS ─────────────────────────────────────────────────

st.markdown(
    """
<style>
    /* Override Streamlit's default cool-gray palette */
    .stApp {
        background: #f5f3f0;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #2b2520;
    }
    [data-testid="stSidebar"] * {
        color: #c4b8a8 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #e8d9c8 !important;
    }
    /* Chat messages — user bubble */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: #ebe7e2;
        border-radius: 16px;
        padding: 4px 8px;
    }
    /* Chat input */
    [data-testid="stChatInput"] textarea {
        border: 1px solid #d4cec7 !important;
        border-radius: 12px !important;
    }
    /* Thinking expander */
    [data-testid="stExpander"] details {
        background: #faf8f6;
        border: 1px solid #e8d0c0;
        border-radius: 8px;
    }
    /* Accent color for route/source labels */
    .accent {
        color: #c2653a;
        font-weight: 600;
    }
    /* Thinking log lines */
    .log-line {
        font-family: 'Consolas', 'JetBrains Mono', monospace;
        font-size: 12px;
        color: #6b5c4e;
        display: block;
        margin: 1px 0;
        white-space: pre-wrap;
        word-break: break-word;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── Node names that appear in graph events ─────────────────────────────────────

_NODE_NAMES = {
    "memory",
    "query_relevancy",
    "query_understanding",
    "query_routing",
    "web_search",
    "comparison_engine",
    "reflection",
    "answer_generation",
}

# ── Logging to stderr (keeps Streamlit stdout clean) ──────────────────────────

logging.basicConfig(
    level=logging.INFO, format="%(name)s: %(message)s", stream=sys.stderr
)

# Timestamped log file — one per Streamlit session
_log_path = setup_file_logging()


class _LogCapture(logging.Handler):
    """Capture log records into a list during agent invocation."""
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

# ── Session state ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {role, content, thinking}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = _load_chat_metadata()

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = str(uuid.uuid4())


def _make_title(messages: list) -> str:
    """Derive a short title from the first user message."""
    for m in messages:
        if m["role"] == "user":
            text = m["content"]
            return text[:50] + ("…" if len(text) > 50 else "")
    return "Empty chat"


def _start_new_chat():
    """Save current chat to history and start a fresh one with a new thread_id."""
    if st.session_state.messages:
        title = _make_title(st.session_state.messages)
        thread_id = st.session_state.current_thread_id

        if st.session_state.current_chat_index is not None:
            # Update existing entry in-place
            idx = st.session_state.current_chat_index
            if idx < len(st.session_state.chat_history):
                st.session_state.chat_history[idx] = {
                    "thread_id": thread_id,
                    "title": title,
                    "messages": list(st.session_state.messages),
                    "created_at": st.session_state.chat_history[idx].get(
                        "created_at", time.strftime("%Y-%m-%dT%H:%M:%S")
                    ),
                }
        else:
            # Append new chat entry
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


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Chat History")
    st.button("＋ New Chat", use_container_width=True, on_click=_start_new_chat)

    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        idx = len(st.session_state.chat_history) - 1 - i
        label = chat.get("title", "Untitled")
        if st.button(label, key=f"hist_{idx}", use_container_width=True):
            st.session_state.messages = list(chat["messages"])
            st.session_state.current_chat_index = idx
            st.session_state.current_thread_id = chat["thread_id"]
            st.rerun()

# ── Main chat area ─────────────────────────────────────────────────────────────

st.markdown(
    "<h1 style='color:#1a1a1a;font-size:24px;margin-bottom:0'>🏠 Agentic Property</h1>"
    "<p style='color:#8b7a6a;margin-top:4px'>Dubai real estate assistant</p>",
    unsafe_allow_html=True,
)

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("thinking"):
            with st.expander("Thinking"):
                st.markdown(msg["thinking"], unsafe_allow_html=True)

# ── Chat input ─────────────────────────────────────────────────────────────────

if prompt := st.chat_input("Ask about Dubai property…"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream agent response
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        answer_placeholder = st.empty()

        thinking_lines: list[str] = []
        answer_tokens: list[str] = []
        final_state: list[dict] = [{}]  # mutable container for inner function
        timings: list[float] = [0, 0]  # [t_first_token, t_total]

        t_start = time.time()

        # ── Capture agent logs ────────────────────────────────────────────────
        capture = _LogCapture()
        capture.setLevel(logging.INFO)
        capture.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        src_logger = logging.getLogger("src")
        src_logger.addHandler(capture)

        config = {"configurable": {"thread_id": st.session_state.current_thread_id}}

        async def _stream():
            # Build graph with async checkpointer (requires running event loop)
            async_cp = await create_async_checkpointer()
            async_graph = build_graph(checkpointer=async_cp)

            try:
                first_token = True
                async for event in async_graph.astream_events(
                    {"query": prompt}, config=config, version="v2"
                ):
                    kind = event["event"]
                    name = event.get("name", "")

                    # ── Node start ──
                    if kind == "on_chain_start" and name in _NODE_NAMES:
                        thinking_lines.append(f'<span class="log-line">→ {name} …</span>')
                        thinking_placeholder.markdown(
                            "\n".join(thinking_lines), unsafe_allow_html=True
                        )

                    # ── Token stream ──
                    elif kind == "on_chat_model_stream":
                        token = event["data"]["chunk"].content
                        if token:
                            if first_token:
                                timings[0] = time.time() - t_start
                                first_token = False
                            answer_tokens.append(token)
                            answer_placeholder.markdown("".join(answer_tokens))

                    # ── Node end ──
                    elif kind == "on_chain_end" and name in _NODE_NAMES:
                        if thinking_lines:
                            thinking_lines[-1] = thinking_lines[-1].replace("…", "✓")
                            thinking_placeholder.markdown(
                                "\n".join(thinking_lines), unsafe_allow_html=True
                            )

                    # ── Root chain end → final state ──
                    elif kind == "on_chain_end" and name == "LangGraph":
                        output = event["data"].get("output", {})
                        if isinstance(output, dict):
                            final_state[0] = output
            finally:
                # Close aiosqlite connection to prevent "Event loop is closed" errors
                if hasattr(async_cp, 'conn') and async_cp.conn is not None:
                    await async_cp.conn.close()

        asyncio.run(_stream())

        # ── Detach log capture ─────────────────────────────────────────────────
        src_logger.removeHandler(capture)

        # Format captured logs chronologically
        agent_logs: list[str] = []
        for r in capture.records:
            node_short = r.name.split(".")[-1] if "." in r.name else r.name
            agent_logs.append(
                f'<span class="log-line">{node_short}: {r.getMessage()}</span>'
            )
        if agent_logs:
            thinking_lines.append(
                '<div style="margin-top:6px;font-size:12px;color:#8b7a6a">'
                "─ Agent log ─</div>"
            )
            thinking_lines.extend(agent_logs)

        timings[1] = time.time() - t_start

        # Build full answer
        full_answer = "".join(answer_tokens)

        # If streaming didn't produce tokens (fallback), show final_answer from state
        if not full_answer:
            full_answer = final_state[0].get("final_answer", "(no answer)")

        # Build thinking summary with route/source info
        route = final_state[0].get("route", "—")
        source = final_state[0].get("data_source", "—")
        intent = final_state[0].get("data_intent", "—")
        currency = final_state[0].get("currency", "AED")
        retry = final_state[0].get("retry_count", 0)

        summary = (
            f'route=<span class="accent">{route}</span> &nbsp;|&nbsp; '
            f'source=<span class="accent">{source}</span> &nbsp;|&nbsp; '
            f'intent=<span class="accent">{intent}</span> &nbsp;|&nbsp; '
            f"currency={currency} &nbsp;|&nbsp; "
            f"retries={retry}"
        )
        ttft_str = f"{timings[0]:.1f}s" if timings[0] else "—"
        total_str = f"{timings[1]:.1f}s"
        timing_summary = (
            f'<span style="color:#8b7a6a;font-size:13px">'
            f"TTFT: {ttft_str} &nbsp;|&nbsp; Total: {total_str}"
            f"</span>"
        )
        thinking_lines.append(
            f'<div style="margin-top:8px;font-size:13px">{summary}</div>'
        )
        thinking_lines.append(f'<div style="margin-top:2px">{timing_summary}</div>')
        thinking_text = "\n".join(thinking_lines)

        # Show final answer and thinking (clear inline thinking, move to expander)
        answer_placeholder.markdown(full_answer)
        thinking_placeholder.empty()  # clear the inline node log
        with st.expander("Thinking"):
            st.markdown(thinking_text, unsafe_allow_html=True)

        # Save to session
        st.session_state.messages.append(
            {"role": "assistant", "content": full_answer, "thinking": thinking_text}
        )

        # Update or create chat entry in persisted history
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
