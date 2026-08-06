#!/usr/bin/env python3
"""Generate a no-verify naive baseline (invented numbers, bad cites, no refusal).

Contrast system for the leaderboard vs Spec-faithful / oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def predict(case: dict) -> str:
    # Always answer confidently — even on OOS — with wrong numbers / fake cite.
    nums = case.get("numeric_values") or [99.0]
    wrong = [float(n) + 1.0 for n in nums[:2]]
    if len(wrong) == 1:
        return f"Definitely {wrong[0]}. [cite:fake-doc]"
    return f"Definitely {wrong[0]} and {wrong[1]}. [cite:fake-doc]"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("dataset/grounded-bench-v0.jsonl"))
    p.add_argument("--out", type=Path, default=Path("predictions/no-verify-naive.jsonl"))
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
