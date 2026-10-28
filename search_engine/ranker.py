import math
from typing import Dict, List, Tuple
from .inverted_index import InvertedIndex

class Ranker:
    """
    Ranks documents for search queries using TF-IDF or BM25 algorithms.
    """

    def __init__(self, index: InvertedIndex):
        self.index = index

    def compute_idf(self, term: str) -> float:
        """
        Computes smooth Inverse Document Frequency (IDF).
        IDF(t) = log((N + 1) / (DF(t) + 1)) + 1
        """
        N = self.index.total_documents
        df = self.index.get_document_frequency(term)
        return math.log((N + 1.0) / (df + 1.0)) + 1.0

    def rank_tfidf(self, query_tokens: List[str]) -> List[Tuple[str, float, Dict[str, float]]]:
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
        return [(doc_id, round(score, 4), doc_term_breakdown[doc_id]) for doc_id, score in sorted_docs]

    def rank_bm25(self, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> List[Tuple[str, float, Dict[str, float]]]:
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
        return [(doc_id, round(score, 4), doc_term_breakdown[doc_id]) for doc_id, score in sorted_docs]
