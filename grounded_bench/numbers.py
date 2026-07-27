"""Numeric extract / verify aligned with Grounded Spec (±0.01)."""

from __future__ import annotations

import re

from grounded_bench import NUMERIC_TOLERANCE

# Plain decimals + European comma decimals. Optional RU "млн" / "млрд" multipliers.
_NUM_RE = re.compile(
    r"(?P<num>\d+(?:[.,]\d+)?)\s*(?P<unit>млн\.?|млрд\.?|million|billion)?",
    re.IGNORECASE,
)

_UNIT_MULT = {
    "млн": 1_000_000.0,
    "млн.": 1_000_000.0,
    "million": 1_000_000.0,
    "млрд": 1_000_000_000.0,
    "млрд.": 1_000_000_000.0,
    "billion": 1_000_000_000.0,
}


def extract_numbers(text: str) -> list[float]:
    """Extract canonical floats from text (Spec-compatible + RU млн/млрд)."""
    if not text:
        return []
    out: list[float] = []
    for m in _NUM_RE.finditer(text):
        raw = m.group("num").replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            continue
        unit = (m.group("unit") or "").lower()
        if unit:
            value *= _UNIT_MULT.get(unit, 1.0)
        out.append(value)
    return out


def number_in_context(n: float, context_numbers: list[float], tol: float = NUMERIC_TOLERANCE) -> bool:
    return any(abs(n - c) <= tol for c in context_numbers)


def unsupported_numbers(
    answer: str,
    context: str,
    *,
    tol: float = NUMERIC_TOLERANCE,
) -> list[float]:
    ctx_nums = extract_numbers(context)
    missing: list[float] = []
    for n in extract_numbers(answer):
        if not number_in_context(n, ctx_nums, tol=tol):
            missing.append(n)
    return missing
