"""Evaluate TF-IDF and BM25 using manually judged relevance labels.

Create evaluation/qrels.json using the format documented in evaluation/README.md,
then run this script from the project root:
    python evaluate_ir.py
"""
import json
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from search_engine import SearchEngine

QRELS_PATH = Path("evaluation/qrels.json")
K = 5


def precision_at_k(ranked_ids, relevant, k=K):
    return sum(doc_id in relevant for doc_id in ranked_ids[:k]) / k


def recall_at_k(ranked_ids, relevant, k=K):
    if not relevant:
        return None
    return sum(doc_id in relevant for doc_id in ranked_ids[:k]) / len(relevant)


def ndcg_at_k(ranked_ids, grades, k=K):
    def dcg(values):
        return sum((2 ** rel - 1) / __import__("math").log2(i + 2)
                   for i, rel in enumerate(values[:k]))

    actual = [grades.get(doc_id, 0) for doc_id in ranked_ids[:k]]
    ideal = sorted(grades.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    return dcg(actual) / ideal_dcg if ideal_dcg else None


def main():
    if not QRELS_PATH.exists():
        raise SystemExit(
            f"Missing {QRELS_PATH}. Follow evaluation/README.md to create "
            "manual relevance judgments first; don't report metrics from guessed labels."
        )

    qrels = json.loads(QRELS_PATH.read_text(encoding="utf-8"))
    if not qrels or not any(isinstance(v, dict) and v for v in qrels.values()):
        raise SystemExit("qrels.json has no relevance judgments yet. Add judged document IDs and grades.")

    engine = SearchEngine(load_sample_corpus=True)
    for algorithm in ("tfidf", "bm25", "semantic"):
        precisions, recalls, ndcgs, latencies = [], [], [], []
        for query, raw_grades in qrels.items():
            grades = {str(doc_id): int(grade) for doc_id, grade in raw_grades.items()}
            relevant = {doc_id for doc_id, grade in grades.items() if grade > 0}
            start = perf_counter()
            result = engine.search(query, algorithm=algorithm, top_k=K)
            latencies.append((perf_counter() - start) * 1000)
            ranked_ids = [str(item["id"]) for item in result["results"]]
            precisions.append(precision_at_k(ranked_ids, relevant, K))
            recall = recall_at_k(ranked_ids, relevant, K)
            ndcg = ndcg_at_k(ranked_ids, grades, K)
            if recall is not None:
                recalls.append(recall)
            if ndcg is not None:
                ndcgs.append(ndcg)

        print(f"\n{algorithm.upper()} — {len(qrels)} queries")
        print(f"P@{K}:       {mean(precisions):.4f}")
        print(f"Recall@{K}:  {mean(recalls):.4f}" if recalls else f"Recall@{K}:  n/a")
        print(f"nDCG@{K}:     {mean(ndcgs):.4f}" if ndcgs else f"nDCG@{K}:     n/a")
        print(f"Median latency: {median(latencies):.2f} ms")


if __name__ == "__main__":
    main()
