# Tracks — grounded-bench

## Offline (default, CI)

| System | How | Meaning |
|--------|-----|---------|
| `oracle` | Bundled predictions | Ceiling |
| `weak-baseline` | Bundled | Broken cites / numbers / refusals |
| `grounded-llm@0.4.0-spec-faithful` | `scripts/predict_spec_faithful.py` | Models **Spec verify path**: numbers from context, valid `[cite:id]`, OOS refusal |
| `no-verify-naive` | `scripts/predict_no_verify.py` | Confident answers with **wrong** numbers and fake cites (even on OOS) |

```bash
pip install -e ".[dev]"
python scripts/run_spec_track.py          # full 1000
python scripts/run_spec_track.py --limit 200   # smoke
```

## Live RAG (optional, not CI)

Full retrieve→LLM→verify against a running [grounded-llm](https://github.com/kantik001/grounded-llm) needs the case `context` injected into the KB (or a context-override API). Deferred: use retrieval eval in `grounded-llm/eval/` for live RAG quality; use this repo for **verifiable generation** metrics on fixed context.

## Citation

When publishing results, cite seed `42` and `benchmark_version` from results JSON.
