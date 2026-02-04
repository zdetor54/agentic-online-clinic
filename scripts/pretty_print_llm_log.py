"""Script to pretty-print llm_requests.jsonl to a human-readable JSON file."""

import json
from pathlib import Path

INPUT_FILE = Path("logs/llm_requests.jsonl")
OUTPUT_FILE = Path("logs/llm_requests_pretty.json")


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return
    with INPUT_FILE.open("r", encoding="utf-8") as infile:
        lines = [json.loads(line) for line in infile if line.strip()]
    with OUTPUT_FILE.open("w", encoding="utf-8") as outfile:
        json.dump(lines, outfile, indent=2, ensure_ascii=False)
    print(f"Wrote pretty-printed log to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
