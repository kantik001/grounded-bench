# Dataset schema (v0)

One JSON object per line (`dataset/grounded-bench-v0.jsonl`).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Unique |
| `domain` | string | yes | `finance` \| `medical` \| `legal` \| `technical` \| `hr` |
| `track` | string | no | `offline` |
| `question` | string | yes | User question |
| `context` | string | yes | Source text (may be empty for OOS) |
| `citations` | object[] | no | `[{ "id", "title"? }]` |
| `numeric_values` | number[] | no | Ground-truth numbers present in context |
| `expect_refusal` | bool | no | Default `false` |
| `tags` | string[] | no | e.g. `grounded`, `refusal` |
| `seed` | int | no | Generator seed |

## Predictions

Separate JSONL (`predictions/*.jsonl`):

```json
{"id": "hr-0001", "answer": "Employees get 28 days. [cite:leave]"}
```

Bundled:

- `predictions/oracle.jsonl` — faithful answers (ceiling)
- `predictions/weak-baseline.jsonl` — wrong numbers / bad cites / non-refusals

Regenerate:

```bash
python dataset/generate_v0.py --seed 42 --count 1000
```
