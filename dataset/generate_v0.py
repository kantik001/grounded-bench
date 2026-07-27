#!/usr/bin/env python3
"""Generate grounded-bench v0 dataset + oracle / weak prediction files."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DOMAINS = ("finance", "medical", "legal", "technical", "hr")

TEMPLATES = {
    "finance": {
        "docs": (
            ("q3_report", "Q3 Revenue Report", "Q3 revenue figure is {n}. Operating margin {m}%."),
            ("tax_note", "Tax Schedule", "VAT rate is {n}%. Filing deadline is day {m} of the month."),
        ),
        "q": (
            "What was Q3 revenue?",
            "What is the VAT rate?",
            "What operating margin is reported?",
        ),
    },
    "medical": {
        "docs": (
            ("dose_card", "Dosing Card", "Adult dose is {n} mg twice daily. Max daily dose {m} mg."),
            ("contra", "Contraindications", "Do not exceed {n} mg/day. Hold if heart rate below {m}."),
        ),
        "q": (
            "What is the adult dose?",
            "What is the maximum daily dose?",
            "Below which heart rate should treatment be held?",
        ),
    },
    "legal": {
        "docs": (
            ("statute", "Statute Excerpt", "Fine for late filing is {n} EUR. Appeal window is {m} days."),
            ("contract", "MSA Clause", "Liability cap equals {n} times fees. Notice period {m} days."),
        ),
        "q": (
            "What is the late-filing fine?",
            "How many days is the appeal window?",
            "What is the liability cap multiplier?",
        ),
    },
    "technical": {
        "docs": (
            ("spec", "Hardware Spec", "Tolerance is {n} mm. Rated voltage {m} V."),
            ("slo", "SLO Sheet", "Availability target {n}%. Error budget {m}% per quarter."),
        ),
        "q": (
            "What is the dimensional tolerance?",
            "What is the rated voltage?",
            "What availability target is published?",
        ),
    },
    "hr": {
        "docs": (
            ("policy", "Leave Policy", "Employees receive {n} paid vacation days. Carry-over limit is {m} days."),
            ("oncall", "On-call Policy", "On-call stipend is {n} USD per week. Response SLA {m} minutes."),
        ),
        "q": (
            "How many paid vacation days do employees get?",
            "What is the vacation carry-over limit?",
            "What is the on-call response SLA?",
        ),
    },
}


def _base(
    *,
    cid: str,
    domain: str,
    question: str,
    context: str,
    citations: list[dict],
    numeric_values: list[float],
    expect_refusal: bool,
    tags: list[str],
    seed: int,
) -> dict:
    return {
        "id": cid,
        "domain": domain,
        "track": "offline",
        "question": question,
        "context": context,
        "citations": citations,
        "numeric_values": numeric_values,
        "expect_refusal": expect_refusal,
        "tags": tags,
        "seed": seed,
    }


def generate(count: int, seed: int) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """Return (cases, oracle_answers, weak_answers) keyed by id."""
    rng = random.Random(seed)
    cases: list[dict] = []
    oracle: dict[str, str] = {}
    weak: dict[str, str] = {}

    anchors = [
        (
            _base(
                cid="anchor-fin-mln",
                domain="finance",
                question="Какая выручка за квартал?",
                context="Отчёт: выручка 14 млн рублей за квартал.",
                citations=[{"id": "annual", "title": "Annual Report"}],
                numeric_values=[14_000_000.0],
                expect_refusal=False,
                tags=["grounded", "ru_million"],
                seed=seed,
            ),
            "Выручка составила 14 млн рублей. [cite:annual]",
            "Выручка 99 млн. [cite:wrong]",
        ),
        (
            _base(
                cid="anchor-hr-vacation",
                domain="hr",
                question="How many paid vacation days?",
                context="Leave Policy: Employees receive 28 paid vacation days per year. Carry-over limit is 14 days.",
                citations=[{"id": "leave", "title": "Leave Policy"}],
                numeric_values=[28.0, 14.0],
                expect_refusal=False,
                tags=["grounded", "hr_seed"],
                seed=seed,
            ),
            "Employees get 28 paid vacation days. [cite:leave]",
            "Employees get 99 paid vacation days. [cite:leave]",
        ),
        (
            _base(
                cid="anchor-oos-refusal",
                domain="hr",
                question="What is the company stock ticker?",
                context="",
                citations=[],
                numeric_values=[],
                expect_refusal=True,
                tags=["refusal"],
                seed=seed,
            ),
            "No information found in the knowledge base for this question.",
            "The ticker is ACME and market cap is 50 billion.",
        ),
    ]

    for case, good, bad in anchors:
        cases.append(case)
        oracle[case["id"]] = good
        weak[case["id"]] = bad

    i = 0
    while len(cases) < count:
        domain = DOMAINS[i % len(DOMAINS)]
        tmpl = TEMPLATES[domain]
        doc_id, title, body_tmpl = tmpl["docs"][i % len(tmpl["docs"])]
        question = tmpl["q"][i % len(tmpl["q"])]
        n = float(rng.randint(2, 97))
        m = float(rng.randint(2, 60))
        bad_n = float(rng.randint(100, 900))
        while abs(bad_n - n) < 0.01 or abs(bad_n - m) < 0.01:
            bad_n = float(rng.randint(100, 900))

        ni, mi = int(n), int(m)
        context = body_tmpl.format(n=ni, m=mi)
        cite_id = f"{domain}-{doc_id}-{i}"
        citations = [{"id": cite_id, "title": title}]
        kind = i % 4  # 0-2 in-domain, 3 OOS

        if kind != 3:
            cid = f"{domain}-{i:04d}"
            case = _base(
                cid=cid,
                domain=domain,
                question=question,
                context=context,
                citations=citations,
                numeric_values=[n, m],
                expect_refusal=False,
                tags=["grounded"],
                seed=seed,
            )
            cases.append(case)
            oracle[cid] = (
                f"According to the source, the primary figure is {ni} "
                f"and the secondary figure is {mi}. [cite:{cite_id}]"
            )
            # Weak: wrong number OR bad citation alternating
            if i % 2 == 0:
                weak[cid] = f"The answer is {int(bad_n)}. [cite:{cite_id}]"
            else:
                weak[cid] = f"Primary figure is {ni}. [cite:fake-{i}]"
        else:
            cid = f"{domain}-{i:04d}-oos"
            oos_context = "" if i % 2 == 0 else "Weather bulletin: temperature 18 C in the city center."
            case = _base(
                cid=cid,
                domain=domain,
                question=question + " (out of corpus)",
                context=oos_context,
                citations=[],
                numeric_values=[],
                expect_refusal=True,
                tags=["refusal"],
                seed=seed,
            )
            cases.append(case)
            oracle[cid] = "Insufficient context — no information found in the knowledge base."
            weak[cid] = f"Confidently, the value is {int(bad_n)}. [cite:invented]"
        i += 1

    cases.sort(key=lambda c: c["id"])
    cases = cases[:count]
    ids = {c["id"] for c in cases}
    oracle = {k: v for k, v in oracle.items() if k in ids}
    weak = {k: v for k, v in weak.items() if k in ids}
    return cases, oracle, weak


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("dataset/grounded-bench-v0.jsonl"))
    parser.add_argument("--oracle", type=Path, default=Path("predictions/oracle.jsonl"))
    parser.add_argument("--weak", type=Path, default=Path("predictions/weak-baseline.jsonl"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=280)
    args = parser.parse_args()

    cases, oracle, weak = generate(args.count, args.seed)
    _write_jsonl(args.out, cases)
    _write_jsonl(args.oracle, [{"id": k, "answer": oracle[k]} for k in sorted(oracle)])
    _write_jsonl(args.weak, [{"id": k, "answer": weak[k]} for k in sorted(weak)])
    print(f"Wrote {len(cases)} cases -> {args.out}")
    print(f"Wrote oracle predictions -> {args.oracle}")
    print(f"Wrote weak predictions -> {args.weak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
