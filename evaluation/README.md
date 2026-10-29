# ScholarSeek IR Evaluation Benchmark

This directory contains the ground-truth relevance judgments and artifacts for evaluating Information Retrieval models in ScholarSeek.

## Relevance Scale
- **`2` (Highly Relevant)**: The paper directly solves, investigates, or implements the specific core topic of the query.
- **`1` (Partially Relevant)**: The paper discusses the topic as a sub-component, application, or closely related technique.
- **`0` (Irrelevant / Negative)**: The paper matches surface keywords but addresses an entirely distinct topic.

## Running the Benchmark
Run the evaluator from the repository root:
```bash
python evaluate_ir.py
```

This will run all evaluated algorithms (**TF-IDF**, **Okapi BM25**, and **Semantic Search**) against the benchmark query set, print a detailed metrics table to stdout, and export `evaluation/evaluation_report.md` and `evaluation/evaluation_report.json`.
