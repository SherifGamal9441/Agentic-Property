"""
Agentic Property — interactive CLI.

Run the agent pipeline and get answers in real time.

Each session has a UUID thread_id for conversation isolation.
Type 'new' to start a fresh conversation thread.

Usage:
    uv run python scripts/run_cli.py
"""

import logging
import sys
import uuid
from pathlib import Path

# Add project root to sys.path so 'src' can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.graph import agent_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

_DIVIDER = "=" * 60


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

        print(f"\n{_DIVIDER}")
        print("Assistant >")
        print(result.get("final_answer") or "(no answer)")

        route = result.get("route", "n/a (rejected before routing)")
        source = result.get("data_source", "n/a")
        intent = result.get("data_intent", "n/a")
        currency = result.get("currency", "AED")
        turns = len(result.get("conversation_history", [])) // 2
        print(f"\n[route={route} | source={source} | intent={intent} | currency={currency} | turns={turns}]")
        print()


if __name__ == "__main__":
    main()
