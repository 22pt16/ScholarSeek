import time
import re
from typing import Dict, List, Any, Optional
from .tokenizer import Tokenizer
from .inverted_index import InvertedIndex
from .ranker import Ranker
from .spell_check import SpellChecker
from .corpus import SAMPLE_CORPUS

class SearchEngine:
    """
    Main SearchEngine Façade coordinating Tokenizer, InvertedIndex, Ranker, and SpellChecker.
    """

    def __init__(self, load_sample_corpus: bool = True):
        self.tokenizer = Tokenizer()
        self.index = InvertedIndex()
        self.ranker = Ranker(self.index)
        self.spell_checker = SpellChecker(self.index.vocabulary)

        if load_sample_corpus:
            self._load_corpus()

    def _load_corpus(self):
        """Indexes initial sample corpus."""
        for doc in SAMPLE_CORPUS:
            self.index_document(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                category=doc.get("category", "General"),
                url=doc.get("url", "#")
            )

    def index_document(self, doc_id: str, title: str, content: str, category: str = "General", url: str = "#"):
        """
        Tokenizes and indexes a document.
        """
        full_text = f"{title} {content}"
        tokens_with_pos = self.tokenizer.tokenize_with_positions(full_text)
        self.index.add_document(doc_id, title, content, category, url, tokens_with_pos)
        # Update spell checker vocabulary reference
        self.spell_checker.vocabulary = self.index.vocabulary

    def extract_snippet(self, content: str, query_terms: List[str], max_len: int = 180) -> str:
        """
        Extracts the most relevant snippet window around matching query terms.
        """
        if not content:
            return ""

        lower_content = content.lower()
        first_pos = -1

        for term in query_terms:
            pos = lower_content.find(term.lower())
            if pos != -1:
                first_pos = pos
                break

        if first_pos == -1:
            return content[:max_len] + "..." if len(content) > max_len else content

        start = max(0, first_pos - 40)
        end = min(len(content), start + max_len)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def search(self, query: str, algorithm: str = "tfidf", top_k: int = 10) -> Dict[str, Any]:
        """
        Executes search query and returns ranked results with execution time metrics.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "execution_time_ms": 0.0,
                "suggestion": None,
                "algorithm": algorithm
            }

        # Check spell suggestion
        corrected_query, has_correction = self.spell_checker.suggest_query(query)
        suggestion = corrected_query if has_correction else None

        query_tokens = self.tokenizer.tokenize(query)

        if algorithm.lower() == "bm25":
            ranked = self.ranker.rank_bm25(query_tokens)
        else:
            ranked = self.ranker.rank_tfidf(query_tokens)

        results = []
        for doc_id, score, term_scores in ranked[:top_k]:
            doc_meta = self.index.documents[doc_id]
            snippet = self.extract_snippet(doc_meta["content"], query_tokens)

            results.append({
                "id": doc_id,
                "title": doc_meta["title"],
                "content": doc_meta["content"],
                "snippet": snippet,
                "category": doc_meta["category"],
                "url": doc_meta["url"],
                "score": score,
                "term_scores": term_scores
            })

        execution_time = (time.perf_counter() - start_time) * 1000.0

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "execution_time_ms": round(execution_time, 2),
            "suggestion": suggestion,
            "algorithm": algorithm.upper()
        }

    def autocomplete(self, prefix: str, limit: int = 5) -> List[str]:
        """
        Returns matching prefix terms from the index vocabulary.
        """
        if not prefix or len(prefix.strip()) < 1:
            return []

        prefix_clean = prefix.lower().strip()
        matches = [term for term in self.index.vocabulary if term.startswith(prefix_clean)]
        return sorted(matches)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        return self.index.get_stats()
