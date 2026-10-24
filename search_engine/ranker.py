import math
from typing import Dict, List, Optional, Tuple

from .inverted_index import InvertedIndex


class Ranker:
    """
    Ranks documents for search queries using TF-IDF, BM25,
    Field-Aware BM25, or Hybrid (BM25 + Semantic) ranking algorithms.
    """

    # Field-aware boost weights: title matches are scored higher than content.
    FIELD_WEIGHTS = {"title": 3.0, "content": 1.0}

    def __init__(self, index: InvertedIndex):
        self.index = index

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def compute_idf(self, term: str) -> float:
        """
        Computes smooth Inverse Document Frequency (IDF).
        IDF(t) = log((N + 1) / (DF(t) + 1)) + 1
        """
        N = self.index.total_documents
        df = self.index.get_document_frequency(term)
        return math.log((N + 1.0) / (df + 1.0)) + 1.0

    # ------------------------------------------------------------------
    # TF-IDF
    # ------------------------------------------------------------------

    def rank_tfidf(
        self, query_tokens: List[str]
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Ranks matching documents using TF-IDF Cosine Similarity algorithm.
        Returns list of (doc_id, total_score, term_scores_breakdown).
        """
        if not query_tokens or self.index.total_documents == 0:
            return []

        doc_scores: Dict[str, float] = {}
        doc_term_breakdown: Dict[str, Dict[str, float]] = {}

        # Count term frequencies in query
        query_tf: Dict[str, int] = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0) + 1

        for term, q_count in query_tf.items():
            postings = self.index.get_postings(term)
            if not postings:
                continue

            idf = self.compute_idf(term)
            q_tfidf = (1.0 + math.log(q_count)) * idf

            for doc_id, data in postings.items():
                raw_tf = data["tf"]
                doc_len = self.index.doc_lengths.get(doc_id, 1)

                # Normalized Term Frequency by Document Length
                norm_tf = raw_tf / float(doc_len if doc_len > 0 else 1)
                term_score = norm_tf * idf * q_tfidf

                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + term_score

                if doc_id not in doc_term_breakdown:
                    doc_term_breakdown[doc_id] = {}
                doc_term_breakdown[doc_id][term] = round(term_score, 4)

        # Sort documents by score descending
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            (doc_id, round(score, 4), doc_term_breakdown[doc_id])
            for doc_id, score in sorted_docs
        ]

    # ------------------------------------------------------------------
    # BM25
    # ------------------------------------------------------------------

    def rank_bm25(
        self,
        query_tokens: List[str],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Ranks matching documents using Okapi BM25 relevance scoring.
        Returns list of (doc_id, total_score, term_scores_breakdown).
        """
        if not query_tokens or self.index.total_documents == 0:
            return []

        N = self.index.total_documents
        avgdl = self.index.avg_doc_length or 1.0

        doc_scores: Dict[str, float] = {}
        doc_term_breakdown: Dict[str, Dict[str, float]] = {}

        unique_query_tokens = set(query_tokens)

        for term in unique_query_tokens:
            postings = self.index.get_postings(term)
            if not postings:
                continue

            df = len(postings)
            # BM25 IDF variant
            bm25_idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

            for doc_id, data in postings.items():
                f = data["tf"]
                doc_len = self.index.doc_lengths.get(doc_id, 1)

                # BM25 TF component with document length normalization
                numerator = f * (k1 + 1.0)
                denominator = f + k1 * (1.0 - b + b * (doc_len / avgdl))

                term_score = bm25_idf * (numerator / denominator)

                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + term_score

                if doc_id not in doc_term_breakdown:
                    doc_term_breakdown[doc_id] = {}
                doc_term_breakdown[doc_id][term] = round(term_score, 4)

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            (doc_id, round(score, 4), doc_term_breakdown[doc_id])
            for doc_id, score in sorted_docs
        ]

    # ------------------------------------------------------------------
    # Field-Aware BM25
    # ------------------------------------------------------------------

    def rank_field_aware(
        self,
        query_tokens: List[str],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Field-Aware BM25: independently scores title and content fields and
        combines them using pre-defined field weights (title boosted 3x).

        BM25_field(d, q) = w_title * BM25_title(d, q)
                         + w_content * BM25_content(d, q)

        Title matches carry much stronger signal because a term in a paper's
        title almost always means the paper is centrally about that topic.
        """
        if not query_tokens or self.index.total_documents == 0:
            return []

        N = self.index.total_documents
        avgdl = self.index.avg_doc_length or 1.0

        doc_scores: Dict[str, float] = {}
        doc_term_breakdown: Dict[str, Dict[str, float]] = {}

        unique_tokens = set(query_tokens)

        for term in unique_tokens:
            postings = self.index.get_postings(term)
            if not postings:
                continue

            df = len(postings)
            bm25_idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

            field_postings = self.index.get_field_postings(term)

            for doc_id, data in postings.items():
                doc_len = self.index.doc_lengths.get(doc_id, 1)

                # Field-level TFs (fall back to proportional estimate if missing)
                fp = field_postings.get(doc_id, {})
                title_tf = fp.get("title", 0)
                content_tf = fp.get("content", data["tf"] - title_tf)

                def bm25_tf(f: float) -> float:
                    num = f * (k1 + 1.0)
                    den = f + k1 * (1.0 - b + b * (doc_len / avgdl))
                    return num / den if den > 0 else 0.0

                title_score = self.FIELD_WEIGHTS["title"] * bm25_idf * bm25_tf(title_tf)
                content_score = self.FIELD_WEIGHTS["content"] * bm25_idf * bm25_tf(content_tf)
                term_score = title_score + content_score

                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + term_score

                if doc_id not in doc_term_breakdown:
                    doc_term_breakdown[doc_id] = {}
                doc_term_breakdown[doc_id][term] = round(term_score, 4)

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            (doc_id, round(score, 4), doc_term_breakdown[doc_id])
            for doc_id, score in sorted_docs
        ]

    # ------------------------------------------------------------------
    # Hybrid Ranking (BM25 + Semantic via Reciprocal Rank Fusion)
    # ------------------------------------------------------------------

    def rank_hybrid(
        self,
        bm25_results: List[Tuple[str, float, Dict]],
        semantic_results: List[Tuple[str, float, Dict]],
        k: int = 60,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Hybrid ranking using Reciprocal Rank Fusion (RRF).

        RRF score(d) = w_bm25 * 1/(k + rank_bm25(d))
                     + w_sem  * 1/(k + rank_sem(d))

        RRF is rank-order based, so it is insensitive to the raw score scales
        of the two systems (TF/IDF vs. cosine similarity), which would make a
        naive linear combination unreliable.

        Parameters
        ----------
        bm25_results     : ranked list from rank_bm25 / rank_field_aware
        semantic_results : ranked list from SemanticSearcher.search
        k                : smoothing constant (default 60, standard in literature)
        bm25_weight      : relative importance of the BM25 ranking
        semantic_weight  : relative importance of the semantic ranking
        """
        rrf_scores: Dict[str, float] = {}
        combined_breakdown: Dict[str, Dict] = {}

        # Accumulate RRF score from BM25 ranking.
        for rank, (doc_id, bm25_score, breakdown) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + bm25_weight / (k + rank)
            combined_breakdown[doc_id] = {
                "bm25": round(bm25_score, 4),
                "semantic": 0.0,
                **{f"bm25_{t}": s for t, s in breakdown.items()},
            }

        # Accumulate RRF score from semantic ranking.
        for rank, (doc_id, sem_score, _) in enumerate(semantic_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + semantic_weight / (k + rank)
            if doc_id not in combined_breakdown:
                combined_breakdown[doc_id] = {"bm25": 0.0, "semantic": round(sem_score, 4)}
            else:
                combined_breakdown[doc_id]["semantic"] = round(sem_score, 4)

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            (doc_id, round(score, 6), combined_breakdown.get(doc_id, {}))
            for doc_id, score in sorted_docs
        ]
