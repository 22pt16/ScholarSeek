"""
Standard Information Retrieval (IR) Evaluation Metrics.

Implements mathematical formulations for Precision@K, Recall@K,
Mean Reciprocal Rank (MRR), Average Precision (MAP),
Normalized Discounted Cumulative Gain (nDCG@K), and Jaccard Rank Overlap.
"""
import math
from typing import Dict, List, Optional, Set


def precision_at_k(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int = 10,
) -> float:
    """
    Compute Precision at rank K: (relevant items in top-K) / K.
    """
    if k <= 0:
        return 0.0

    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0

    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / float(k)


def recall_at_k(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int = 10,
) -> Optional[float]:
    """
    Compute Recall at rank K: (relevant items in top-K) / (total relevant items).
    Returns None if there are no relevant items in the ground truth.
    """
    if not relevant_ids:
        return None

    if k <= 0:
        return 0.0

    top_k = ranked_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / float(len(relevant_ids))


def reciprocal_rank(
    ranked_ids: List[str],
    relevant_ids: Set[str],
) -> float:
    """
    Compute Reciprocal Rank (RR): 1 / rank of the first relevant document.
    Returns 0.0 if no relevant document is retrieved.
    """
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def average_precision(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int = 10,
) -> float:
    """
    Compute Average Precision (AP) at rank K.
    Evaluates ranking quality across all relevant recall points up to rank K.
    """
    if not relevant_ids or k <= 0:
        return 0.0

    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0

    cumulative_hits = 0
    precision_sum = 0.0

    for rank, doc_id in enumerate(top_k, start=1):
        if doc_id in relevant_ids:
            cumulative_hits += 1
            precision_sum += cumulative_hits / float(rank)

    # Normalized by the total number of relevant documents (or k if smaller)
    num_relevant = len(relevant_ids)
    return precision_sum / float(num_relevant) if num_relevant > 0 else 0.0


def dcg_at_k(
    ranked_ids: List[str],
    grades: Dict[str, int],
    k: int = 10,
) -> float:
    """
    Compute Discounted Cumulative Gain (DCG) at rank K using logarithmic discounting:
    DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log_2(i + 1)
    """
    dcg = 0.0
    for i, doc_id in enumerate(ranked_ids[:k]):
        grade = grades.get(doc_id, 0)
        if grade > 0:
            dcg += (2.0 ** grade - 1.0) / math.log2(i + 2)

    return dcg


def ndcg_at_k(
    ranked_ids: List[str],
    grades: Dict[str, int],
    k: int = 10,
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain (nDCG) at rank K:
    nDCG@K = DCG@K / IDCG@K
    """
    if k <= 0:
        return 0.0

    actual_dcg = dcg_at_k(ranked_ids, grades, k)

    # Ideal ranking is sorted descending by relevance grade
    ideal_grades = sorted(grades.values(), reverse=True)[:k]
    ideal_dcg = sum(
        (2.0 ** grade - 1.0) / math.log2(i + 2)
        for i, grade in enumerate(ideal_grades)
        if grade > 0
    )

    if ideal_dcg == 0.0:
        return 0.0

    return actual_dcg / ideal_dcg


def jaccard_overlap(
    list_a: List[str],
    list_b: List[str],
    k: int = 10,
) -> float:
    r"""
    Compute Jaccard similarity between the top-K results of two algorithms:
    |A \cap B| / |A \cup B|
    """
    set_a = set(list_a[:k])
    set_b = set(list_b[:k])

    union = set_a.union(set_b)
    if not union:
        return 0.0

    intersection = set_a.intersection(set_b)
    return len(intersection) / float(len(union))
