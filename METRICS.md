# Metrics — grounded-bench v0

Offline track scores a **predictions JSONL** against the dataset context. No LLM call is required for reproducibility.

| Metric | Direction | Definition |
|--------|-----------|------------|
| **NVR** (Numeric Verify Rate) | ↑ | Among numbers extracted from non-refusal answers, fraction that appear in `context` within **±0.01** (Grounded Spec tolerance). Supports RU `млн` / `млрд` and EN `million` / `billion`. Cases with zero answer numbers are excluded from the denominator. |
| **CP** (Citation Precision) | ↑ | Among `[cite:ID]` markers in the answer, fraction whose `ID` exists in the case `citations` list. Answers with no citations are excluded. |
| **HR** (Hallucination Rate) | ↓ | Fraction of cases that are **hallucinated**: unsupported number and/or invalid citation; or an OOS case (`expect_refusal=true`) that does not refuse and still makes claims. |
| **RR** (Refusal Rate) | ↑ | Among cases with `expect_refusal=true`, fraction whose answer matches refusal markers (`no information`, `insufficient context`, …). |

## Citation syntax

```text
[cite:document_id]
```

## Reproducibility

```bash
python -m grounded_bench run \
  --dataset dataset/grounded-bench-v0.jsonl \
  --predictions predictions/oracle.jsonl \
  --seed 42
```

Results JSON includes `seed`, `hardware`, `benchmark_version`, prediction path, and per-case diagnostics.

## What v0 does *not* claim

- Live RAG/LLM quality of a deployed stack (use [grounded-llm eval](https://github.com/kantik001/grounded-llm/tree/main/eval) for retrieval gates).
- Semantic entailment beyond numeric + citation checks.
- Distributed multi-worker eval (deferred).
