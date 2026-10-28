"""Measure corpus loading and warm search latency for ScholarSeek.

Run from the project root with the project's virtual environment active:
    python benchmark_search.py
"""
from statistics import median
from time import perf_counter

from search_engine import SearchEngine

QUERIES = [
    "machine learning",
    "phishing detection",
    "neural networks for image classification",
    "database indexing",
    "quantum computing",
    "machien learning",
    "zzzxqv nonsense",
]
REPEATS = 5
TOP_K = 10


def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = round((len(ordered) - 1) * p)
    return ordered[index]


def main():
    start = perf_counter()
    engine = SearchEngine(load_sample_corpus=True)
    load_seconds = perf_counter() - start

    stats = engine.get_stats()
    print("\nScholarSeek benchmark")
    print(f"Corpus load + index: {load_seconds:.3f} s")
    print(f"Documents: {stats['total_documents']:,}")
    print(f"Vocabulary: {stats['vocabulary_size']:,}")
    print(f"Indexed tokens: {stats['total_terms_indexed']:,}")
    print(f"Average document length: {stats['avg_doc_length']}")

    for algorithm in ("tfidf", "bm25"):
        print(f"\n{algorithm.upper()} (top_k={TOP_K}, {REPEATS} timed runs)")
        print(f"{'Query':43} {'Median ms':>10} {'P95 ms':>9} {'Matches':>9}  Top result")
        for query in QUERIES:
            engine.search(query, algorithm=algorithm, top_k=TOP_K)  # warm-up
            samples = []
            result = None
            for _ in range(REPEATS):
                start = perf_counter()
                result = engine.search(query, algorithm=algorithm, top_k=TOP_K)
                samples.append((perf_counter() - start) * 1000)
            title = result["results"][0]["title"] if result["results"] else "-"
            print(f"{query[:43]:43} {median(samples):10.2f} {percentile(samples, .95):9.2f} "
                  f"{result['total_results']:9d}  {title[:65]}")


if __name__ == "__main__":
    main()
