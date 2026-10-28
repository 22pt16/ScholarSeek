import math
from typing import Dict, List, Tuple
from .inverted_index import InvertedIndex


class Ranker:
    """Rank documents using TF-IDF cosine similarity or Okapi BM25."""

    def __init__(self, index: InvertedIndex):
        self.index = index
        self.document_norms: Dict[str, float] = {}

    def compute_idf(self, term: str) -> float:
        n_docs = self.index.total_documents
        df = self.index.get_document_frequency(term)
        return math.log((n_docs + 1.0) / (df + 1.0)) + 1.0

    def rebuild_document_norms(self) -> None:
        """Precompute TF-IDF vector norms once after bulk indexing."""
        squared_norms = {doc_id: 0.0 for doc_id in self.index.documents}
        for term, postings in self.index.index.items():
            idf = self.compute_idf(term)
            for doc_id, data in postings.items():
                doc_len = self.index.doc_lengths.get(doc_id, 1) or 1
                weight = (data["tf"] / float(doc_len)) * idf
                squared_norms[doc_id] += weight * weight
        self.document_norms = {
            doc_id: math.sqrt(value) for doc_id, value in squared_norms.items()
        }

    def rank_tfidf(self, query_tokens: List[str]) -> List[Tuple[str, float, Dict[str, float]]]:
        """Rank matching documents by cosine similarity of TF-IDF vectors."""
        if not query_tokens or self.index.total_documents == 0:
            return []

        query_tf: Dict[str, int] = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0) + 1

        query_weights = {}
        for term, count in query_tf.items():
            if self.index.get_postings(term):
                query_weights[term] = (1.0 + math.log(count)) * self.compute_idf(term)
        if not query_weights:
            return []

        query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values())) or 1.0
        doc_dots: Dict[str, float] = {}
        doc_contributions: Dict[str, Dict[str, float]] = {}

        for term, query_weight in query_weights.items():
            idf = self.compute_idf(term)
            for doc_id, data in self.index.get_postings(term).items():
                doc_len = self.index.doc_lengths.get(doc_id, 1) or 1
                doc_weight = (data["tf"] / float(doc_len)) * idf
                contribution = doc_weight * query_weight
                doc_dots[doc_id] = doc_dots.get(doc_id, 0.0) + contribution
                doc_contributions.setdefault(doc_id, {})[term] = contribution

        scored = []
        for doc_id, dot_product in doc_dots.items():
            doc_norm = self.document_norms.get(doc_id, 0.0)
            if doc_norm <= 0:
                continue
            denominator = doc_norm * query_norm
            score = dot_product / denominator if denominator else 0.0
            breakdown = {
                term: round(value / denominator, 6)
                for term, value in doc_contributions[doc_id].items()
            }
            scored.append((doc_id, round(score, 6), breakdown))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def rank_bm25(self, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> List[Tuple[str, float, Dict[str, float]]]:
        """Rank matching documents using Okapi BM25 relevance scoring."""
        if not query_tokens or self.index.total_documents == 0:
            return []

        n_docs = self.index.total_documents
        avgdl = self.index.avg_doc_length or 1.0
        doc_scores: Dict[str, float] = {}
        doc_term_breakdown: Dict[str, Dict[str, float]] = {}

        for term in set(query_tokens):
            postings = self.index.get_postings(term)
            if not postings:
                continue
            df = len(postings)
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
            for doc_id, data in postings.items():
                tf = data["tf"]
                doc_len = self.index.doc_lengths.get(doc_id, 1) or 1
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / avgdl))
                contribution = idf * (numerator / denominator)
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + contribution
                doc_term_breakdown.setdefault(doc_id, {})[term] = round(contribution, 6)

        ranked = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)
        return [(doc_id, round(score, 6), doc_term_breakdown[doc_id]) for doc_id, score in ranked]
