"""Offline runner + leaderboard publish."""

from __future__ import annotations

import json
import platform
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grounded_bench import SEED_DEFAULT, __version__
from grounded_bench.dataset import attach_predictions, load_jsonl, load_predictions, validate_dataset
from grounded_bench.metrics import aggregate, score_case


def run_offline(
    dataset_path: Path,
    *,
    predictions_path: Path,
    seed: int = SEED_DEFAULT,
    limit: int | None = None,
    system_name: str = "oracle",
) -> dict[str, Any]:
    cases = load_jsonl(dataset_path)
    errors = validate_dataset(cases)
    if errors:
        raise SystemExit("dataset invalid:\n- " + "\n- ".join(errors[:20]))
    cases = attach_predictions(cases, load_predictions(predictions_path))

    rng = random.Random(seed)
    order = list(range(len(cases)))
    rng.shuffle(order)
    if limit is not None:
        order = order[:limit]

    selected = [cases[i] for i in order]
    scores = [score_case(c) for c in selected]
    metrics = aggregate(scores)

    by_domain: dict[str, list] = {}
    for s in scores:
        by_domain.setdefault(s.domain, []).append(s)
    domain_metrics = {
        domain: aggregate(items).as_dict() for domain, items in sorted(by_domain.items())
    }

    return {
        "benchmark": "grounded-bench",
        "benchmark_version": __version__,
        "track": "offline",
        "system": system_name,
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hardware": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "dataset": {
            "path": str(dataset_path).replace("\\", "/"),
            "predictions": str(predictions_path).replace("\\", "/"),
            "cases_total": len(cases),
            "cases_scored": len(selected),
        },
        "metrics": metrics.as_dict(),
        "by_domain": domain_metrics,
        "cases": [
            {
                "id": s.id,
                "domain": s.domain,
                "hallucinated": s.hallucinated,
                "nvr": s.nvr_case,
                "cp": s.cp_case,
                "refusal_correct": s.refusal_correct,
                "unsupported_numbers": s.unsupported_numbers,
                "invalid_citations": s.invalid_citations,
                "notes": s.notes,
            }
            for s in scores
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publish_leaderboard(results_path: Path, out_dir: Path) -> Path:
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "results.json"
    write_json(dest, payload)

    m = payload.get("metrics") or {}
    rows = [
        {
            "system": payload.get("system", "unknown"),
            "nvr": m.get("nvr"),
            "cp": m.get("citation_precision"),
            "hr": m.get("hallucination_rate"),
            "rr": m.get("refusal_rate"),
            "cases": m.get("cases"),
            "date": (payload.get("timestamp") or "")[:10],
            "seed": payload.get("seed"),
            "version": payload.get("benchmark_version"),
        }
    ]
    # Keep historical rows if present
    hist_path = out_dir / "history.json"
    history: list[dict[str, Any]] = []
    if hist_path.exists():
        try:
            history = json.loads(hist_path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []
    key = (rows[0]["system"], rows[0]["seed"], rows[0]["version"], rows[0]["cases"])
    history = [h for h in history if (h.get("system"), h.get("seed"), h.get("version"), h.get("cases")) != key]
    history.insert(0, rows[0])
    history.sort(
        key=lambda r: (
            -(r.get("nvr") if isinstance(r.get("nvr"), (int, float)) else -1.0),
            r.get("system") or "",
        )
    )
    write_json(hist_path, history)

    html = render_leaderboard_html(history, payload)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return out_dir / "index.html"


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{100.0 * v:.1f}%"


def render_leaderboard_html(history: list[dict[str, Any]], latest: dict[str, Any]) -> str:
    rows_html = []
    for r in history:
        rows_html.append(
            "<tr>"
            f"<td>{_esc(r.get('system'))}</td>"
            f"<td>{_fmt_pct(r.get('nvr'))}</td>"
            f"<td>{_fmt_pct(r.get('cp'))}</td>"
            f"<td>{_fmt_pct(r.get('hr'))}</td>"
            f"<td>{_fmt_pct(r.get('rr'))}</td>"
            f"<td>{r.get('cases') or '—'}</td>"
            f"<td>{_esc(r.get('date'))}</td>"
            f"<td>seed={r.get('seed')} · v{_esc(r.get('version'))}</td>"
            "</tr>"
        )
    hw = latest.get("hardware") or {}
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>grounded-bench leaderboard</title>
  <style>
    :root {{
      --bg: #0f1419;
      --panel: #1a222c;
      --text: #e7ecf1;
      --muted: #9aa7b5;
      --accent: #3d9cfd;
      --line: #2a3542;
    }}
    body {{
      margin: 0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1c2a3a, var(--bg));
      color: var(--text); line-height: 1.45;
    }}
    main {{ max-width: 960px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
    h1 {{ font-size: 1.75rem; margin: 0 0 0.35rem; letter-spacing: -0.02em; }}
    .sub {{ color: var(--muted); margin-bottom: 1.75rem; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); }}
    th, td {{ padding: 0.7rem 0.75rem; text-align: left; border-bottom: 1px solid var(--line); font-size: 0.95rem; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    tr:last-child td {{ border-bottom: none; }}
    code {{ color: var(--accent); }}
    .meta {{ margin-top: 1.5rem; color: var(--muted); font-size: 0.9rem; }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <h1>grounded-bench</h1>
    <p class="sub">Offline verifiable-generation leaderboard — NVR · Citation Precision · Hallucination Rate · Refusal Rate</p>
    <table>
      <thead>
        <tr>
          <th>System</th><th>NVR ↑</th><th>CP ↑</th><th>HR ↓</th><th>RR ↑</th>
          <th>Cases</th><th>Date</th><th>Repro</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows_html)}
      </tbody>
    </table>
    <p class="meta">
      Latest hardware: <code>{_esc(hw.get("platform"))}</code> · Python <code>{_esc(hw.get("python"))}</code><br/>
      Definitions: <a href="../METRICS.md">METRICS.md</a> · Dataset seed reproducible via <code>grounded-bench run --seed</code>
    </p>
  </main>
</body>
</html>
"""


def _esc(value: Any) -> str:
    s = "" if value is None else str(value)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
