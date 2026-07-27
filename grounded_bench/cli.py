"""CLI entrypoint: validate | run | publish."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from grounded_bench import SEED_DEFAULT, __version__
from grounded_bench.dataset import load_jsonl, validate_dataset
from grounded_bench.runner import publish_leaderboard, run_offline, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="grounded-bench",
        description="Public benchmark for verifiable / grounded generation",
    )
    parser.add_argument("--version", action="version", version=f"grounded-bench {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate JSONL dataset schema")
    p_val.add_argument("--dataset", type=Path, required=True)

    p_run = sub.add_parser("run", help="Score predictions against dataset (NVR/CP/HR/RR)")
    p_run.add_argument("--dataset", type=Path, required=True)
    p_run.add_argument("--predictions", type=Path, required=True, help="JSONL: {id, answer}")
    p_run.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--system", default="oracle")
    p_run.add_argument("--write", type=Path, default=Path("results/latest.json"))

    p_pub = sub.add_parser("publish", help="Write static leaderboard from results JSON")
    p_pub.add_argument("--results", type=Path, required=True)
    p_pub.add_argument("--out", type=Path, default=Path("leaderboard"))

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        cases = load_jsonl(args.dataset)
        errors = validate_dataset(cases)
        if errors:
            print(f"INVALID ({len(errors)} errors)", file=sys.stderr)
            for e in errors[:50]:
                print(f"  - {e}", file=sys.stderr)
            return 1
        domains: dict[str, int] = {}
        refusals = 0
        for c in cases:
            domains[c["domain"]] = domains.get(c["domain"], 0) + 1
            if c.get("expect_refusal"):
                refusals += 1
        print(f"OK {len(cases)} cases · refusals={refusals} · domains={domains}")
        return 0

    if args.cmd == "run":
        payload = run_offline(
            args.dataset,
            predictions_path=args.predictions,
            seed=args.seed,
            limit=args.limit,
            system_name=args.system,
        )
        write_json(args.write, payload)
        m = payload["metrics"]
        print(f"Wrote {args.write}")
        print(
            "NVR={nvr} CP={cp} HR={hr} RR={rr} cases={cases}".format(
                nvr=_pct(m.get("nvr")),
                cp=_pct(m.get("citation_precision")),
                hr=_pct(m.get("hallucination_rate")),
                rr=_pct(m.get("refusal_rate")),
                cases=m.get("cases"),
            )
        )
        return 0

    if args.cmd == "publish":
        html = publish_leaderboard(args.results, args.out)
        print(f"Published {html}")
        return 0

    return 2


def _pct(v: float | None) -> str:
    if v is None:
        return "n/a"
    return f"{100.0 * v:.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
