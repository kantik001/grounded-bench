# grounded-bench

[![CI](https://github.com/kantik001/grounded-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/kantik001/grounded-bench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](pyproject.toml)

**Public benchmark for verifiable / grounded generation.** Part of the [Grounded](https://github.com/kantik001/grounded-llm) ecosystem.

> Measure whether answers stay faithful to sources — numbers, citations, refusals — with a reproducible seed.

| | |
|---|---|
| **Track (v0)** | Offline scoring (dataset + prediction JSONL, no LLM required) |
| **Metrics** | **NVR** · **CP** · **HR** · **RR** — [METRICS.md](METRICS.md) |
| **Dataset** | `dataset/grounded-bench-v0.jsonl` (**1000** cases, seed `42`) |
| **Leaderboard** | [leaderboard/index.html](leaderboard/index.html) |

## Quick start

```bash
python -m venv .venv
pip install -e ".[dev]"

python -m grounded_bench validate --dataset dataset/grounded-bench-v0.jsonl

python -m grounded_bench run \
  --dataset dataset/grounded-bench-v0.jsonl \
  --predictions predictions/oracle.jsonl \
  --system oracle --seed 42 \
  --write results/oracle.json

python -m grounded_bench publish --results results/oracle.json --out leaderboard/
```

Or: `make ci`

## Reference numbers (v0.1.1, seed 42)

| System | NVR ↑ | CP ↑ | HR ↓ | RR ↑ | Cases |
|--------|------:|-----:|-----:|-----:|------:|
| `oracle` | **100%** | **100%** | **0%** | **100%** | 1000 |
| `grounded-llm@0.4.0-spec-faithful` | **100%** | **100%** | **0%** | **100%** | 1000 |
| `weak-baseline` | 33.2% | 66.7% | 100% | 0% | 1000 |
| `no-verify-naive` | 1.1% | 0% | **100%** | **0%** | 1000 |

Regenerate Spec + naive rows:

```bash
make score-spec
# or: python scripts/run_spec_track.py
```

See [TRACKS.md](TRACKS.md). Exact figures are regenerated into `leaderboard/results.json` / `history.json` on each publish. CI gates oracle to NVR/CP/RR ≥ 99% and HR ≤ 1%.

## Submit your system

1. Produce `predictions.jsonl` with `{"id","answer"}` for every case id.
2. Cite sources as `[cite:ID]` matching dataset citation ids.
3. Run:

```bash
python -m grounded_bench run \
  --dataset dataset/grounded-bench-v0.jsonl \
  --predictions path/to/predictions.jsonl \
  --system your-system-name \
  --seed 42 \
  --write results/yours.json
```

## Why this exists

[grounded-llm](https://github.com/kantik001/grounded-llm) ships a **retrieval** eval gate (99 cases).  
`grounded-bench` scores **verifiable generation** independently of a live RAG stack.

## Dataset

| Domains | finance · medical · legal · technical · hr |
|---------|--------------------------------------------|
| Mix | in-domain grounded + OOS refusal cases |
| Generator | [`dataset/generate_v0.py`](dataset/generate_v0.py) |
| Schema | [`dataset/SCHEMA.md`](dataset/SCHEMA.md) |

## Ecosystem

| Repo | Role |
|------|------|
| [grounded-llm](https://github.com/kantik001/grounded-llm) | Cited RAG + Spec + retrieval eval |
| [grounded-guardrails](https://github.com/kantik001/grounded-guardrails) | Token-level verify gRPC `:50052` |
| [grounded-vllm](https://github.com/kantik001/grounded-vllm) | Serving-path verify proxy for vLLM |
| [mcp-gateway](https://github.com/kantik001/mcp-gateway) | MCP HTTP bridge |
| [grounded-agent](https://github.com/kantik001/grounded-agent) | ReAct orchestrator |
| **grounded-bench** | Public verifiable-generation benchmark |

## Status

Shipped (v0): offline metrics, **1000**-case dataset, oracle/weak predictions, CLI, leaderboard, CI.

Next: `make score-spec` publishes `grounded-llm@0.4.0-spec-faithful` vs `no-verify-naive` · optional live RAG track.

## License

MIT
