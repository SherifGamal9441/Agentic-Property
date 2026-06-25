"""
Agentic Property — interactive CLI.

Run the agent pipeline and get answers in real time.

Usage:
    uv run python main.py
"""

import logging
import sys

from src.agents.graph import agent_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

_DIVIDER = "=" * 60


def main() -> None:
    print("Agentic Property — Dubai real estate assistant")
    print("Type your question, or 'quit' / 'exit' to stop.\n")

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

        print(f"\n{_DIVIDER}")
        result = agent_graph.invoke({"query": query})

        print(f"\n{_DIVIDER}")
        print("Assistant >")
        print(result.get("final_answer") or "(no answer)")

        route = result.get("route", "n/a (rejected before routing)")
        source = result.get("data_source", "n/a")
        intent = result.get("data_intent", "n/a")
        currency = result.get("currency", "AED")
        print(f"\n[route={route} | source={source} | intent={intent} | currency={currency}]")
        print()


if __name__ == "__main__":
    main()
