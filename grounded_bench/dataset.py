"""Dataset load / validate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED = ("id", "domain", "question", "context")
DOMAINS = frozenset({"finance", "medical", "legal", "technical", "hr"})


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{i}: invalid JSON: {e}") from e
    return cases


def load_predictions(path: Path) -> dict[str, str]:
    """Map case id → answer text. Accepts `answer` or `candidate_answer`."""
    rows = load_jsonl(path)
    out: dict[str, str] = {}
    for i, row in enumerate(rows):
        cid = row.get("id")
        if not isinstance(cid, str) or not cid:
            raise SystemExit(f"{path}:{i}: prediction missing id")
        answer = row.get("answer")
        if answer is None:
            answer = row.get("candidate_answer")
        if not isinstance(answer, str):
            raise SystemExit(f"{path}:{i}: prediction `{cid}` missing answer")
        if cid in out:
            raise SystemExit(f"{path}: duplicate prediction id `{cid}`")
        out[cid] = answer
    return out


def validate_case(case: dict[str, Any], *, index: int) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in case:
            errors.append(f"case[{index}]: missing `{key}`")
    if "id" in case and not isinstance(case["id"], str):
        errors.append(f"case[{index}]: id must be str")
    domain = case.get("domain")
    if domain is not None and domain not in DOMAINS:
        errors.append(f"case[{index}] {case.get('id')}: unknown domain `{domain}`")
    if "citations" in case and not isinstance(case["citations"], list):
        errors.append(f"case[{index}]: citations must be list")
    for c in case.get("citations") or []:
        if not isinstance(c, dict) or "id" not in c:
            errors.append(f"case[{index}]: citation missing id")
            break
    if "numeric_values" in case and not isinstance(case["numeric_values"], list):
        errors.append(f"case[{index}]: numeric_values must be list")
    if "expect_refusal" in case and not isinstance(case["expect_refusal"], bool):
        errors.append(f"case[{index}]: expect_refusal must be bool")
    return errors


def validate_dataset(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for i, case in enumerate(cases):
        errors.extend(validate_case(case, index=i))
        cid = case.get("id")
        if isinstance(cid, str):
            if cid in seen:
                errors.append(f"duplicate id: {cid}")
            seen.add(cid)
    return errors


def attach_predictions(cases: list[dict[str, Any]], predictions: dict[str, str]) -> list[dict[str, Any]]:
    missing = [c["id"] for c in cases if c["id"] not in predictions]
    if missing:
        preview = ", ".join(missing[:10])
        raise SystemExit(f"predictions missing {len(missing)} case ids (e.g. {preview})")
    out: list[dict[str, Any]] = []
    for case in cases:
        merged = dict(case)
        merged["candidate_answer"] = predictions[case["id"]]
        out.append(merged)
    return out
