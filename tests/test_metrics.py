from grounded_bench.metrics import aggregate, score_case
from grounded_bench.numbers import extract_numbers, unsupported_numbers


def test_extract_plain_and_million():
    assert 28.0 in extract_numbers("Employees get 28 days")
    assert 14_000_000.0 in extract_numbers("выручка 14 млн")


def test_unsupported_numbers():
    missing = unsupported_numbers("99 days", "28 vacation days")
    assert 99.0 in missing
    assert unsupported_numbers("28 days", "28 vacation days") == []


def test_grounded_case_scores_clean():
    case = {
        "id": "t1",
        "domain": "hr",
        "context": "Leave Policy: 28 paid vacation days.",
        "citations": [{"id": "leave", "title": "Leave"}],
        "candidate_answer": "Employees get 28 days. [cite:leave]",
        "expect_refusal": False,
    }
    s = score_case(case)
    assert s.hallucinated is False
    assert s.nvr_case == 1.0
    assert s.cp_case == 1.0


def test_hallucination_and_refusal():
    bad = score_case(
        {
            "id": "t2",
            "domain": "hr",
            "context": "28 days",
            "citations": [{"id": "leave"}],
            "candidate_answer": "99 days [cite:leave]",
            "expect_refusal": False,
        }
    )
    assert bad.hallucinated is True

    refusal = score_case(
        {
            "id": "t3",
            "domain": "hr",
            "context": "",
            "citations": [],
            "candidate_answer": "No information found in the knowledge base.",
            "expect_refusal": True,
        }
    )
    assert refusal.refusal_correct is True
    assert refusal.hallucinated is False


def test_citation_ids_do_not_pollute_nvr():
    case = {
        "id": "t4",
        "domain": "finance",
        "context": "Revenue figure is 42.",
        "citations": [{"id": "finance-doc-99"}],
        "candidate_answer": "Revenue is 42. [cite:finance-doc-99]",
        "expect_refusal": False,
    }
    s = score_case(case)
    assert s.hallucinated is False
    assert s.nvr_case == 1.0
    assert s.answer_numbers == 1


def test_aggregate_shape():
    scores = [
        score_case(
            {
                "id": "a",
                "domain": "hr",
                "context": "28",
                "citations": [{"id": "x"}],
                "candidate_answer": "28 [cite:x]",
                "expect_refusal": False,
            }
        ),
        score_case(
            {
                "id": "b",
                "domain": "hr",
                "context": "",
                "citations": [],
                "candidate_answer": "No information found in the knowledge base.",
                "expect_refusal": True,
            }
        ),
    ]
    m = aggregate(scores)
    assert m.cases == 2
    assert m.nvr == 1.0
    assert m.refusal_rate == 1.0
