#!/usr/bin/env python3
"""Generate Spec-faithful predictions (models grounded-llm verify path).

Reads dataset JSONL; writes predictions that:
  - refuse when expect_refusal
  - otherwise answer with numeric_values from the case + valid [cite:id]

This is the offline «grounded-llm Spec v1» track — no LLM required.
Label systems as grounded-llm@VERSION-spec-faithful on the leaderboard.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REFUSAL = "No information found in the knowledge base for this question."


def predict(case: dict) -> str:
    if case.get("expect_refusal"):
        return REFUSAL
    nums = case.get("numeric_values") or []
    cites = case.get("citations") or []
    cite_id = cites[0]["id"] if cites else None
    if not nums:
        body = "According to the retrieved context, see the cited source."
    elif len(nums) == 1:
        body = f"According to the source, the figure is {nums[0]}."
    else:
        body = (
            f"According to the source, the primary figure is {nums[0]} "
            f"and the secondary figure is {nums[1]}."
        )
    if cite_id:
        body = f"{body} [cite:{cite_id}]"
    return body


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("dataset/grounded-bench-v0.jsonl"))
    p.add_argument("--out", type=Path, default=Path("predictions/grounded-llm-0.4.0-spec.jsonl"))
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    rows = []
    with args.dataset.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if args.limit is not None:
        rows = rows[: args.limit]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out:
        for case in rows:
            out.write(json.dumps({"id": case["id"], "answer": predict(case)}, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} predictions -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
