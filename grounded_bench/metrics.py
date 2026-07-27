"""Case-level and aggregate metrics: NVR, CP, HR, RR."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from grounded_bench.numbers import extract_numbers, unsupported_numbers

CITE_RE = re.compile(r"\[cite:([a-zA-Z0-9_.:-]+)\]")

REFUSAL_MARKERS = (
    "cannot find",
    "can't find",
    "no information",
    "not found in",
    "out of scope",
    "insufficient context",
    "i don't know",
    "do not know",
    "unable to verify",
    "not in the knowledge base",
    "нет информации",
    "не найдено",
    "вне области",
    "недостаточно данных",
)


@dataclass
class CaseScore:
    id: str
    domain: str
    expect_refusal: bool
    is_refusal: bool
    answer_numbers: int
    verified_numbers: int
    unsupported_numbers: list[float] = field(default_factory=list)
    citations_claimed: int = 0
    citations_valid: int = 0
    invalid_citations: list[str] = field(default_factory=list)
    hallucinated: bool = False
    refusal_correct: bool | None = None  # only for expect_refusal cases
    notes: str = ""

    @property
    def nvr_case(self) -> float | None:
        if self.expect_refusal or self.answer_numbers == 0:
            return None
        return self.verified_numbers / self.answer_numbers

    @property
    def cp_case(self) -> float | None:
        if self.expect_refusal or self.citations_claimed == 0:
            return None
        return self.citations_valid / self.citations_claimed


@dataclass
class AggregateMetrics:
    cases: int
    nvr: float | None
    citation_precision: float | None
    hallucination_rate: float
    refusal_rate: float
    nvr_denominator: int
    cp_denominator: int
    refusal_denominator: int
    hallucinated_cases: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def looks_like_refusal(answer: str) -> bool:
    text = (answer or "").lower()
    return any(m in text for m in REFUSAL_MARKERS)


def extract_citation_ids(answer: str) -> list[str]:
    return CITE_RE.findall(answer or "")


def strip_citations(text: str) -> str:
    return CITE_RE.sub(" ", text or "")


def score_case(case: dict[str, Any]) -> CaseScore:
    answer = case.get("candidate_answer") or ""
    context = case.get("context") or ""
    expect_refusal = bool(case.get("expect_refusal"))
    allowed = {c["id"] for c in (case.get("citations") or []) if c.get("id")}

    is_refusal = looks_like_refusal(answer)
    answer_for_numbers = strip_citations(answer)
    missing = unsupported_numbers(answer_for_numbers, context) if not is_refusal else []
    ans_nums = extract_numbers(answer_for_numbers) if not is_refusal else []
    verified = len(ans_nums) - len(missing)

    claimed = extract_citation_ids(answer)
    invalid = [cid for cid in claimed if cid not in allowed]
    valid = len(claimed) - len(invalid)

    hallucinated = False
    refusal_correct: bool | None = None
    notes = ""

    if expect_refusal:
        refusal_correct = is_refusal
        # Claiming unsupported facts on an OOS case counts as hallucination.
        hallucinated = (not is_refusal) and (bool(missing) or bool(invalid) or bool(ans_nums))
        if not is_refusal and not hallucinated and answer.strip():
            # Non-refusal prose without numbers/cites on OOS: soft hallucination
            hallucinated = True
            notes = "expected refusal but answer made claims"
    else:
        hallucinated = bool(missing) or bool(invalid)

    return CaseScore(
        id=case["id"],
        domain=case.get("domain") or "unknown",
        expect_refusal=expect_refusal,
        is_refusal=is_refusal,
        answer_numbers=len(ans_nums),
        verified_numbers=max(0, verified),
        unsupported_numbers=missing,
        citations_claimed=len(claimed),
        citations_valid=max(0, valid),
        invalid_citations=invalid,
        hallucinated=hallucinated,
        refusal_correct=refusal_correct,
        notes=notes,
    )


def aggregate(scores: list[CaseScore]) -> AggregateMetrics:
    nvr_num = nvr_den = 0
    cp_num = cp_den = 0
    for s in scores:
        if s.nvr_case is not None:
            nvr_num += s.verified_numbers
            nvr_den += s.answer_numbers
        if s.cp_case is not None:
            cp_num += s.citations_valid
            cp_den += s.citations_claimed

    refusal_cases = [s for s in scores if s.expect_refusal]
    refusal_ok = sum(1 for s in refusal_cases if s.refusal_correct)
    hallucinated = sum(1 for s in scores if s.hallucinated)

    return AggregateMetrics(
        cases=len(scores),
        nvr=(nvr_num / nvr_den) if nvr_den else None,
        citation_precision=(cp_num / cp_den) if cp_den else None,
        hallucination_rate=(hallucinated / len(scores)) if scores else 0.0,
        refusal_rate=(refusal_ok / len(refusal_cases)) if refusal_cases else 0.0,
        nvr_denominator=nvr_den,
        cp_denominator=cp_den,
        refusal_denominator=len(refusal_cases),
        hallucinated_cases=hallucinated,
    )
