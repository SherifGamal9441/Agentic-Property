"""
Upload eval JSON files to LangSmith as datasets.

Creates two datasets:
  - agentic-property-structural  (50 objective state-assertion tests)
  - agentic-property-quality     (50 LLM-as-judge quality tests)

Usage:
    python scripts/upload_eval_datasets.py                   # upload both
    python scripts/upload_eval_datasets.py --type structural # upload one
    python scripts/upload_eval_datasets.py --force           # skip confirmation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

EVAL_DIR = Path(__file__).parent.parent / "data" / "eval"

DATASETS = {
    "structural": {
        "name": "agentic-property-structural",
        "file": EVAL_DIR / "structural_tests.json",
    },
    "quality": {
        "name": "agentic-property-quality",
        "file": EVAL_DIR / "quality_tests.json",
    },
}


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_structural_examples(tests: list[dict]) -> list[dict]:
    examples = []
    for t in tests:
        examples.append(
            {
                "inputs": {
                    "query": t["query"],
                    "id": t["id"],
                    "tags": t.get("tags", []),
                },
                "outputs": {
                    "expected": t["expected"],
                },
            }
        )
    return examples


def _build_quality_examples(tests: list[dict]) -> list[dict]:
    examples = []
    for t in tests:
        examples.append(
            {
                "inputs": {
                    "query": t["query"],
                    "id": t["id"],
                    "tags": t.get("tags", []),
                },
                "outputs": {
                    "criteria": t["criteria"],
                    "min_score": t["min_score"],
                },
            }
        )
    return examples


def upload_dataset(
    client: Client,
    dataset_type: str,
    force: bool = False,
) -> None:
    info = DATASETS[dataset_type]
    name = info["name"]
    tests = _load_json(info["file"])

    existing = None
    try:
        existing = client.read_dataset(dataset_name=name)
    except Exception:
        pass

    if existing is not None:
        if not force:
            answer = input(
                f"Dataset '{name}' already exists ({len(tests)} examples). "
                f"Delete and recreate? [y/N] "
            )
            if answer.strip().lower() not in ("y", "yes"):
                print(f"  Skipped '{name}' — keeping existing dataset.")
                return
        client.delete_dataset(dataset_name=name)
        print(f"  Deleted existing '{name}'")

    dataset = client.create_dataset(dataset_name=name)

    if dataset_type == "structural":
        examples = _build_structural_examples(tests)
    else:
        examples = _build_quality_examples(tests)

    client.create_examples(dataset_id=dataset.id, examples=examples)

    print(f"  Created '{name}' with {len(examples)} examples")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload eval JSON files to LangSmith as datasets.",
    )
    parser.add_argument(
        "--type",
        choices=["structural", "quality", "both"],
        default="both",
        help="Which dataset to upload (default: both)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing datasets without asking",
    )
    args = parser.parse_args()

    client = Client()

    types_to_upload = ["structural", "quality"] if args.type == "both" else [args.type]

    print(
        f"Uploading datasets to LangSmith (project: {client._get_default_project_name() if hasattr(client, '_get_default_project_name') else 'default'})"
    )

    for dt in types_to_upload:
        print(f"\n[{dt}]")
        upload_dataset(client, dt, force=args.force)

    print("\nDone! View datasets at https://smith.langchain.com/datasets")


if __name__ == "__main__":
    main()
