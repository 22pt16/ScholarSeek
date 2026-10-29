import pytest
from search_engine.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    average_precision,
    ndcg_at_k,
    jaccard_overlap,
)


def test_precision_at_k():
    ranked = ["d1", "d2", "d3", "d4", "d5"]
    relevant = {"d1", "d3", "d5"}

    assert precision_at_k(ranked, relevant, k=1) == 1.0  # d1 is relevant (1/1)
    assert precision_at_k(ranked, relevant, k=2) == 0.5  # d1 is, d2 not (1/2)
    assert precision_at_k(ranked, relevant, k=3) == pytest.approx(2 / 3)  # d1, d3 (2/3)
    assert precision_at_k(ranked, relevant, k=5) == 0.6  # d1, d3, d5 (3/5)
    assert precision_at_k([], relevant, k=5) == 0.0
    assert precision_at_k(ranked, set(), k=5) == 0.0


def test_recall_at_k():
    ranked = ["d1", "d2", "d3", "d4", "d5"]
    relevant = {"d1", "d3", "d5", "d6"}  # 4 total relevant

    assert recall_at_k(ranked, relevant, k=1) == 0.25  # 1/4
    assert recall_at_k(ranked, relevant, k=3) == 0.5   # 2/4
    assert recall_at_k(ranked, relevant, k=5) == 0.75  # 3/4
    assert recall_at_k(ranked, set(), k=5) is None
    assert recall_at_k([], relevant, k=5) == 0.0


def test_reciprocal_rank():
    # First relevant at rank 1
    assert reciprocal_rank(["d1", "d2", "d3"], {"d1"}) == 1.0
    # First relevant at rank 2
    assert reciprocal_rank(["d0", "d1", "d2"], {"d1"}) == 0.5
    # First relevant at rank 3
    assert reciprocal_rank(["d0", "d9", "d1"], {"d1"}) == pytest.approx(1 / 3)
    # No relevant found
    assert reciprocal_rank(["d0", "d9", "d8"], {"d1"}) == 0.0
    assert reciprocal_rank([], {"d1"}) == 0.0


def test_average_precision():
    # Ranked: [R, N, R, N, R] (positions 1, 3, 5)
    # Precision at pos 1: 1/1 = 1.0
    # Precision at pos 3: 2/3 = 0.6667
    # Precision at pos 5: 3/5 = 0.6000
    # Total relevant in ground truth = 3
    # AP = (1.0 + 2/3 + 0.6) / 3 = 2.2667 / 3 = 0.7555
    ranked = ["d1", "d2", "d3", "d4", "d5"]
    relevant = {"d1", "d3", "d5"}
    expected_ap = (1.0 + (2 / 3) + (3 / 5)) / 3.0
    assert average_precision(ranked, relevant, k=5) == pytest.approx(expected_ap)

    # Empty cases
    assert average_precision([], relevant, k=5) == 0.0
    assert average_precision(ranked, set(), k=5) == 0.0


def test_ndcg_at_k():
    grades = {"d1": 3, "d2": 2, "d3": 1, "d4": 0}
    
    # Perfect ranking: [d1, d2, d3, d4] -> nDCG must be exactly 1.0
    assert ndcg_at_k(["d1", "d2", "d3", "d4"], grades, k=4) == pytest.approx(1.0)

    # Inverted ranking: [d4, d3, d2, d1] -> nDCG must be significantly less than 1.0
    ndcg_inverted = ndcg_at_k(["d4", "d3", "d2", "d1"], grades, k=4)
    assert ndcg_inverted < 0.6
    assert ndcg_inverted > 0.0

    # All zero grades
    assert ndcg_at_k(["d4"], {"d4": 0}, k=1) == 0.0


def test_jaccard_overlap():
    list_a = ["d1", "d2", "d3", "d4"]
    list_b = ["d1", "d2", "d5", "d6"]

    # Overlap at k=2: {"d1", "d2"} vs {"d1", "d2"} -> 1.0
    assert jaccard_overlap(list_a, list_b, k=2) == 1.0

    # Overlap at k=4: intersection 2 ("d1", "d2"), union 6 ("d1","d2","d3","d4","d5","d6") -> 2/6 = 1/3
    assert jaccard_overlap(list_a, list_b, k=4) == pytest.approx(2 / 6)

    # Disjoint lists
    assert jaccard_overlap(["a", "b"], ["c", "d"], k=2) == 0.0
