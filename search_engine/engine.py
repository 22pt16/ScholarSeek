
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .tokenizer import Tokenizer
from .inverted_index import InvertedIndex
from .ranker import Ranker
from .spell_check import SpellChecker
from .corpus import SAMPLE_CORPUS
from .semantic_search import SemanticSearcher


class SearchEngine:
    """
    Main SearchEngine coordinating the tokenizer, inverted index,
    ranker, spell checker, and research-paper corpus.
    """

    def __init__(self, load_sample_corpus: bool = True):
        self.tokenizer = Tokenizer()
        self.index = InvertedIndex()
        self.ranker = Ranker(self.index)
        self.spell_checker = SpellChecker(self.index.vocabulary)
        self._semantic_searcher = None

        if load_sample_corpus:
            self._load_corpus()

    def _load_corpus(self):
        """
        Load research papers from JSONL.
        Fall back to the sample corpus if the JSONL file is absent.
        """
        corpus_path = Path(__file__).with_name(
            "scholarseek_corpus.jsonl"
        )

        if corpus_path.exists():
            print(f"Loading research corpus from {corpus_path}...")

            loaded = 0

            with corpus_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue

                    try:
                        paper = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"Invalid JSON at line {line_number} "
                            f"in {corpus_path}"
                        ) from exc

                    paper_id = paper.get("id")
                    title = paper.get("title", "")
                    abstract = paper.get("abstract") or paper.get(
                        "content", ""
                    )

                    if not paper_id or not title or not abstract:
                        continue

                    self.index_document(
                        doc_id=str(paper_id),
                        title=title,
                        content=abstract,
                        category=paper.get("category", "General"),
                        url=paper.get("url", "#"),
                        metadata=paper,
                    )

                    loaded += 1

            print(f"Loaded {loaded:,} research papers.")

        else:
            print(
                "Research corpus not found. "
                "Loading sample corpus instead."
            )

            for doc in SAMPLE_CORPUS:
                self.index_document(
                    doc_id=doc["id"],
                    title=doc["title"],
                    content=doc["content"],
                    category=doc.get("category", "General"),
                    url=doc.get("url", "#"),
                )

        # Ensure spell correction uses the completed vocabulary.
        self.spell_checker.vocabulary = self.index.vocabulary

    def _get_semantic_searcher(self):
        if self._semantic_searcher is None:
            self._semantic_searcher = SemanticSearcher(
                self.index.documents
            )

        return self._semantic_searcher

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str = "General",
        url: str = "#",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Tokenize and index a document while preserving its metadata.
        """
        full_text = f"{title} {content}"
        tokens_with_pos = self.tokenizer.tokenize_with_positions(
            full_text
        )

        self.index.add_document(
            doc_id,
            title,
            content,
            category,
            url,
            tokens_with_pos,
        )

        # Store research-paper metadata for result display and future use.
        if metadata:
            self.index.documents[doc_id].update(metadata)

        # Keep the spell checker's vocabulary synchronized.
        self.spell_checker.vocabulary = self.index.vocabulary

    def extract_snippet(
        self,
        content: str,
        query_terms: List[str],
        max_len: int = 180,
    ) -> str:
        """
        Extract a short snippet around the first matching query term.
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
            return (
                content[:max_len] + "..."
                if len(content) > max_len
                else content
            )

        start = max(0, first_pos - 40)
        end = min(len(content), start + max_len)

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet

        if end < len(content):
            snippet += "..."

        return snippet

    def search(
        self,
        query: str,
        algorithm: str = "tfidf",
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute a query and return ranked results and timing metrics.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "execution_time_ms": 0.0,
                "suggestion": None,
                "algorithm": algorithm.upper(),
            }

        # Check for a possible spelling correction.
        corrected_query, has_correction = (
            self.spell_checker.suggest_query(query)
        )
        suggestion = corrected_query if has_correction else None

        query_tokens = self.tokenizer.tokenize(query)

        if not query_tokens:
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "execution_time_ms": round(
                    (time.perf_counter() - start_time) * 1000, 2
                ),
                "suggestion": suggestion,
                "algorithm": algorithm.upper(),
            }

        # Select the ranking algorithm.
        algorithm_name = algorithm.lower()

        if algorithm_name == "tfidf":
            ranked = self.ranker.rank_tfidf(query_tokens)

        elif algorithm_name == "bm25":
            ranked = self.ranker.rank_bm25(query_tokens)

        elif algorithm_name == "semantic":
            ranked = self._get_semantic_searcher().search(
                query,
                top_k=max(top_k, 100),
            )

        else:
            raise ValueError(
                f"Unknown search algorithm: {algorithm}"
            )

        results = []

        for doc_id, score, term_scores in ranked[:max(0, top_k)]:
            doc_meta = self.index.documents[doc_id]
            content = doc_meta.get(
                "abstract",
                doc_meta.get("content", ""),
            )

            snippet = self.extract_snippet(content, query_tokens)

            results.append({
                "id": doc_id,
                "title": doc_meta.get("title", ""),
                "content": doc_meta.get("content", content),
                "snippet": snippet,
                "category": doc_meta.get("category", "General"),
                "url": doc_meta.get("url", "#"),
                "score": score,
                "term_scores": term_scores,
                "authors": doc_meta.get("authors", ""),
                "year": doc_meta.get("year"),
                "abstract": doc_meta.get("abstract", content),
                "keywords": doc_meta.get("keywords", []),
                "doi": doc_meta.get("doi"),
            })

        execution_time = (
            time.perf_counter() - start_time
        ) * 1000.0

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "execution_time_ms": round(execution_time, 2),
            "suggestion": suggestion,
            "algorithm": algorithm.upper(),
        }

    def autocomplete(
        self,
        prefix: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Return matching terms from the indexed vocabulary.
        """
        if not prefix or not prefix.strip():
            return []

        prefix_clean = prefix.lower().strip()

        matches = [
            term
            for term in self.index.vocabulary
            if term.startswith(prefix_clean)
        ]

        return sorted(matches)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics."""
        return self.index.get_stats()
