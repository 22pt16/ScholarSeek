"""
Evaluation module for ScholarSeek.

Implements standard Information Retrieval evaluation metrics:
  - Precision@K  : fraction of top-K results that are relevant
  - Recall@K     : fraction of all relevant docs retrieved in top-K
  - F1@K         : harmonic mean of Precision@K and Recall@K
  - NDCG@K       : Normalized Discounted Cumulative Gain (graded relevance)
  - MRR          : Mean Reciprocal Rank (rank of the first relevant result)
  - MAP@K        : Mean Average Precision

All metrics accept a list of retrieved document IDs (ranked) and a set of
ground-truth relevant document IDs.
"""

import math
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Individual metric functions
# ---------------------------------------------------------------------------

def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Precision@K = |{relevant} ∩ {retrieved[:K]}| / K
    """
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant)
    return hits / k


def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Recall@K = |{relevant} ∩ {retrieved[:K]}| / |relevant|
    """
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant)
    return hits / len(relevant)


def f1_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    F1@K = 2 * P@K * R@K / (P@K + R@K)
    """
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)
    if p + r == 0.0:
        return 0.0
    return 2 * p * r / (p + r)


def dcg_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    DCG@K using binary relevance:
    DCG@K = sum_{i=1}^{K} rel_i / log2(i + 1)
    """
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k], start=1):
        if doc_id in relevant:
            dcg += 1.0 / math.log2(i + 1)
    return dcg


def ndcg_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    NDCG@K = DCG@K / IDCG@K

    IDCG is the ideal DCG (all relevant docs ranked first).
    """
    actual_dcg = dcg_at_k(retrieved, relevant, k)
    # Ideal: min(|relevant|, k) hits at top positions
    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> float:
    """
    Reciprocal Rank = 1 / rank_of_first_relevant_doc
    Returns 0.0 if no relevant doc is found.
    """
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def average_precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Average Precision@K = (1/|relevant|) * sum_k P@k * rel_k
    """
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for i, doc_id in enumerate(retrieved[:k], start=1):
        if doc_id in relevant:
            hits += 1
            precision_sum += hits / i
    return precision_sum / len(relevant)


# ---------------------------------------------------------------------------
# Convenience: evaluate a single ranked list
# ---------------------------------------------------------------------------

def evaluate(
    retrieved: List[str],
    relevant: Set[str],
    k: int = 10,
) -> Dict[str, float]:
    """
    Compute all standard IR metrics for one query result.

    Parameters
    ----------
    retrieved : ordered list of retrieved document IDs (highest-ranked first)
    relevant  : set of ground-truth relevant document IDs
    k         : cut-off rank (default 10)

    Returns
    -------
    Dict with keys: precision, recall, f1, ndcg, mrr, map
    """
    return {
        f"precision@{k}": round(precision_at_k(retrieved, relevant, k), 4),
        f"recall@{k}":    round(recall_at_k(retrieved, relevant, k), 4),
        f"f1@{k}":        round(f1_at_k(retrieved, relevant, k), 4),
        f"ndcg@{k}":      round(ndcg_at_k(retrieved, relevant, k), 4),
        "mrr":            round(reciprocal_rank(retrieved, relevant), 4),
        f"map@{k}":       round(average_precision_at_k(retrieved, relevant, k), 4),
        "hits":           sum(1 for d in retrieved[:k] if d in relevant),
        "total_relevant": len(relevant),
        "k":              k,
    }


# ---------------------------------------------------------------------------
# Convenience: compare two systems on the same query
# ---------------------------------------------------------------------------

def compare_systems(
    system_a_results: List[str],
    system_b_results: List[str],
    relevant: Set[str],
    k: int = 10,
    label_a: str = "System A",
    label_b: str = "System B",
) -> Dict:
    """
    Evaluate two ranked lists against the same ground truth and return
    a side-by-side comparison dict.
    """
    eval_a = evaluate(system_a_results, relevant, k)
    eval_b = evaluate(system_b_results, relevant, k)
    return {
        label_a: eval_a,
        label_b: eval_b,
        "winner": _pick_winner(eval_a, eval_b, k, label_a, label_b),
    }


def _pick_winner(
    eval_a: Dict,
    eval_b: Dict,
    k: int,
    label_a: str,
    label_b: str,
) -> str:
    """Return the label of whichever system has a higher NDCG@K."""
    ndcg_key = f"ndcg@{k}"
    if eval_a.get(ndcg_key, 0) >= eval_b.get(ndcg_key, 0):
        return label_a
    return label_b
