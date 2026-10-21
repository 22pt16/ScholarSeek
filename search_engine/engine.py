import json
from pathlib import Path
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
    """Load research papers from JSONL, falling back to sample data."""
    corpus_path = Path(__file__).with_name("scholarseek_corpus.jsonl")

    if corpus_path.exists():
        print(f"Loading research corpus from {corpus_path}...")

        with corpus_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                paper = json.loads(line)

                self.index_document(
                    doc_id=paper["id"],
                    title=paper["title"],
                    content=paper["abstract"],
                    category=paper.get("category", "General"),
                    url=paper.get("url", "#"),
                    metadata=paper,
                )

        print(f"Loaded {self.index.total_documents:,} research papers.")

    else:
        print("Research corpus not found. Loading sample corpus.")

        for doc in SAMPLE_CORPUS:
            self.index_document(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                category=doc.get("category", "General"),
                url=doc.get("url", "#"),
            )


    
def index_document(
    self,
    doc_id: str,
    title: str,
    content: str,
    category: str = "General",
    url: str = "#",
    metadata: Optional[Dict[str, Any]] = None,
):
    """Tokenize and index a document while preserving its metadata."""
    full_text = f"{title} {content}"
    tokens_with_pos = self.tokenizer.tokenize_with_positions(full_text)

    self.index.add_document(
        doc_id, title, content, category, url, tokens_with_pos
    )

    # Preserve research-paper fields for display and future retrieval.
    if metadata:
        self.index.documents[doc_id].update(metadata)

    # Keep the spell checker synchronized with the index vocabulary.
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
                "term_scores": term_scores,
                "authors": doc_meta.get("authors", ""),
                "year": doc_meta.get("year"),
                "abstract": doc_meta.get("abstract", doc_meta["content"]),
                "keywords": doc_meta.get("keywords", []),
                "doi": doc_meta.get("doi"),
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
