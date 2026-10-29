# ScholarSeek IR Evaluation Report

Evaluated 8 test queries across **TF-IDF**, **Okapi BM25**, and **Semantic Search** on the 20,000 research paper corpus.

## Summary Table

| Algorithm | P@5 | P@10 | Recall@10 | MRR | MAP@10 | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TFIDF** | 0.2500 | 0.1750 | 0.4146 | 0.5451 | 0.2534 | 0.3327 | 0.3743 |
| **BM25** | 0.5750 | 0.3250 | 0.7750 | 0.8750 | 0.6023 | 0.6920 | 0.7293 |
| **SEMANTIC** | 0.5750 | 0.3125 | 0.7625 | 0.9375 | 0.7035 | 0.7143 | 0.7388 |

## Latency and Zero-Result Statistics

| Algorithm | Median latency (ms) | P95 latency (ms) | Zero results | Zero-result rate |
| :--- | ---: | ---: | ---: | ---: |
| **TFIDF** | 11.55 | 48.72 | 0 | 0.00% |
| **BM25** | 9.70 | 40.76 | 0 | 0.00% |
| **SEMANTIC** | 33.60 | 43.64 | 0 | 0.00% |

    ## Key Findings

    - **Ranking Quality**: Compare the relevance metrics above to understand the strengths of lexical and semantic retrieval.
    - **Latency**: The table reports measured query latency in milliseconds. Results include the effects of the current runtime, caching, and model initialization strategy; interpret them in that context.
    - **Zero-result rate**: This is the proportion of benchmark queries that returned no results.
