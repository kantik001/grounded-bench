#!/usr/bin/env python3
"""Run Spec-faithful + no-verify tracks and publish leaderboard rows.

Usage (from grounded-bench root, after pip install -e .):

  python scripts/run_spec_track.py
  python scripts/run_spec_track.py --limit 200
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="dataset/grounded-bench-v0.jsonl")
    p.add_argument("--limit", type=int, default=None, help="Optional subset for smoke")
    p.add_argument("--system-spec", default="grounded-llm@0.4.0-spec-faithful")
    p.add_argument("--system-naive", default="no-verify-naive")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    spec_pred = "predictions/grounded-llm-0.4.0-spec.jsonl"
    naive_pred = "predictions/no-verify-naive.jsonl"
    gen_limit = []
    if args.limit is not None:
        gen_limit = ["--limit", str(args.limit)]

    run([sys.executable, "scripts/predict_spec_faithful.py", "--dataset", args.dataset, "--out", spec_pred, *gen_limit])
    run([sys.executable, "scripts/predict_no_verify.py", "--dataset", args.dataset, "--out", naive_pred, *gen_limit])

    run_limit = []
    if args.limit is not None:
        run_limit = ["--limit", str(args.limit)]

    run(
        [
            sys.executable,
            "-m",
            "grounded_bench",
            "run",
            "--dataset",
            args.dataset,
            "--predictions",
            spec_pred,
            "--system",
            args.system_spec,
            "--seed",
            str(args.seed),
            "--write",
            "results/grounded-llm-0.4.0-spec.json",
            *run_limit,
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "grounded_bench",
            "run",
            "--dataset",
            args.dataset,
            "--predictions",
            naive_pred,
            "--system",
            args.system_naive,
            "--seed",
            str(args.seed),
            "--write",
            "results/no-verify-naive.json",
            *run_limit,
        ]
    )
    run([sys.executable, "-m", "grounded_bench", "publish", "--results", "results/grounded-llm-0.4.0-spec.json", "--out", "leaderboard/"])
    run([sys.executable, "-m", "grounded_bench", "publish", "--results", "results/no-verify-naive.json", "--out", "leaderboard/"])
    # Keep oracle/weak rows visible
    if (ROOT / "results/oracle.json").exists():
        run([sys.executable, "-m", "grounded_bench", "publish", "--results", "results/oracle.json", "--out", "leaderboard/"])
    if (ROOT / "results/weak.json").exists():
        run([sys.executable, "-m", "grounded_bench", "publish", "--results", "results/weak.json", "--out", "leaderboard/"])

    print("Done. Open leaderboard/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
