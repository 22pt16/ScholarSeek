"""
Query Expansion using corpus co-occurrence statistics.

The expander looks at the indexed vocabulary and finds terms that
frequently appear together with query terms at the document level,
then appends the top co-occurring terms to widen the recall of the
original query.

This is a lightweight, fully offline approach (no external APIs or
word-vector models needed) that fits naturally on top of the existing
InvertedIndex and Tokenizer infrastructure.
"""

from typing import Dict, List, Set

from .inverted_index import InvertedIndex


class QueryExpander:
    """
    Pseudo-Relevance-Free corpus-level query expansion.

    Strategy
    --------
    1. For each query term, retrieve the set of documents that contain it
       (its posting list).
    2. For every other vocabulary term, count how many of those documents
       also contain it (document-level co-occurrence).
    3. Rank co-occurring terms by frequency; pick the top-N.
    4. Exclude original query tokens and very high-frequency stop terms
       (terms that appear in > 80 % of the corpus are uninformative).

    The result is a list of expansion terms that can be appended to the
    tokenized query before ranking, broadening the retrieved set without
    requiring any external resource.
    """

    #: Terms appearing in more than this fraction of the corpus are ignored.
    MAX_DF_RATIO: float = 0.8

    def __init__(self, index: InvertedIndex):
        self.index = index

    def expand(
        self,
        query_tokens: List[str],
        top_n: int = 5,
    ) -> List[str]:
        """
        Return up to ``top_n`` expansion terms for the given query tokens.

        Parameters
        ----------
        query_tokens : tokenized query (already stemmed / lowercased)
        top_n        : maximum number of expansion terms to return

        Returns
        -------
        List of expansion term strings (may be empty if corpus is tiny).
        """
        if not query_tokens or self.index.total_documents == 0:
            return []

        N = self.index.total_documents
        max_df = int(N * self.MAX_DF_RATIO)

        import math
        query_token_set: Set[str] = set(query_tokens)

        # 1. Score candidate documents using query term matching
        candidate_doc_scores: Dict[str, float] = {}
        for token in query_token_set:
            postings = self.index.get_postings(token)
            if not postings:
                continue
            df = len(postings)
            idf = math.log((N + 1.0) / (df + 1.0)) + 1.0
            for doc_id, data in postings.items():
                candidate_doc_scores[doc_id] = candidate_doc_scores.get(doc_id, 0.0) + data["tf"] * idf

        if not candidate_doc_scores:
            return []

        # Select top-15 pseudo-relevant feedback documents (PRF)
        sorted_candidates = sorted(candidate_doc_scores.items(), key=lambda x: x[1], reverse=True)
        top_feedback_docs = [doc_id for doc_id, _ in sorted_candidates[:15]]

        # 2. Score candidate expansion terms using Rocchio PRF: sum(TF * IDF) across feedback docs
        term_scores: Dict[str, float] = {}
        for term, postings in self.index.index.items():
            if term in query_token_set or len(term) <= 2:
                continue

            df = len(postings)
            if df > max_df or df < 2:
                continue

            # Fast O(1) lookup in postings for the top feedback docs
            feedback_tf = sum(postings[doc_id]["tf"] for doc_id in top_feedback_docs if doc_id in postings)
            if feedback_tf > 0:
                idf = math.log((N + 1.0) / (df + 1.0)) + 1.0
                term_scores[term] = feedback_tf * idf

        if not term_scores:
            return []

        # 3. Rank terms by Rocchio score descending
        ranked = sorted(term_scores.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in ranked[:top_n]]

    def expand_query_string(
        self,
        query_tokens: List[str],
        top_n: int = 5,
    ) -> List[str]:
        """
        Convenience wrapper: returns original tokens + expansion tokens.

        The expanded tokens are appended (not prepended) so that the
        original terms always take priority in score accumulation.
        """
        expansion = self.expand(query_tokens, top_n=top_n)
        return query_tokens + expansion
