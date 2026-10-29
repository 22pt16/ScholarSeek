
import json
import time
from pathlib import Path
from bisect import bisect_left
from typing import Dict, List, Any, Optional

from .tokenizer import Tokenizer
from .inverted_index import InvertedIndex
from .ranker import Ranker
from .spell_check import SpellChecker
from .corpus import SAMPLE_CORPUS


class SearchEngine:
    """
    Main SearchEngine coordinating the tokenizer, inverted index,
    ranker, spell checker, and research-paper corpus.
    """

    def __init__(self, load_sample_corpus: bool = True):
        self.tokenizer = Tokenizer()
        self.index = InvertedIndex()
        self.ranker = Ranker(self.index)
        self.surface_vocabulary = set()
        self.spell_checker = SpellChecker(self.surface_vocabulary)
        self._semantic_searcher = None
        self._autocomplete_cache = []
        self._autocomplete_cache_size = -1

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
                        rebuild_norms=False,
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
                    rebuild_norms=False,
                )

        # Build expensive derived structures once after bulk indexing.
        self.ranker.rebuild_document_norms()
        self.spell_checker.prepare()

    def _get_semantic_searcher(self):
        if self._semantic_searcher is None:
            # Keep transformer dependencies out of the classical-search startup path.
            from .semantic_search import SemanticSearcher
            self._semantic_searcher = SemanticSearcher(self.index.documents)

        return self._semantic_searcher

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str = "General",
        url: str = "#",
        metadata: Optional[Dict[str, Any]] = None,
        rebuild_norms: bool = True,
    ):
        """
        Tokenize and index a document while preserving its metadata.
        """
        full_text = f"{title} {content}"
        tokens_with_pos = self.tokenizer.tokenize_with_positions(full_text)
        self.surface_vocabulary.update(self.tokenizer.tokenize_surface(full_text))

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

        # Spell suggestions use surface forms; ranking uses normalized index terms.
        self.spell_checker.vocabulary = self.surface_vocabulary
        if rebuild_norms:
            self.ranker.rebuild_document_norms()

        if self._semantic_searcher is not None:
            self._semantic_searcher.add_document(doc_id, self.index.documents[doc_id])

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
        top_k: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute a query and return ranked results and timing metrics.
        """
        start_time = time.perf_counter()

        # Slicing configuration: top_k takes precedence when provided (for CLI, benchmarks, tests)
        if top_k is not None:
            effective_page = 1
            effective_per_page = max(1, int(top_k))
            start = 0
            end = effective_per_page
        else:
            effective_page = max(1, int(page))
            effective_per_page = max(1, min(100, int(per_page)))
            start = (effective_page - 1) * effective_per_page
            end = start + effective_per_page

        if not query or not query.strip():
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "page": effective_page,
                "per_page": effective_per_page,
                "total_pages": 0,
                "execution_time_ms": 0.0,
                "suggestion": None,
                "algorithm": algorithm.upper(),
            }

        query_tokens = self.tokenizer.tokenize(query)

        if not query_tokens:
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "page": effective_page,
                "per_page": effective_per_page,
                "total_pages": 0,
                "execution_time_ms": round(
                    (time.perf_counter() - start_time) * 1000, 2
                ),
                "suggestion": None,
                "algorithm": algorithm.upper(),
            }

        corrected_query, has_correction = self.spell_checker.suggest_query(
            query,
            tokenizer=self.tokenizer,
            indexed_vocabulary=self.index.vocabulary,
        )
        suggestion = corrected_query if has_correction else None

        # Select the ranking algorithm.
        algorithm_name = algorithm.lower()

        if algorithm_name == "tfidf":
            ranked = self.ranker.rank_tfidf(query_tokens)

        elif algorithm_name == "bm25":
            ranked = self.ranker.rank_bm25(query_tokens)

        elif algorithm_name == "semantic":
            # Retrieve enough top candidates to support requested page/top_k
            candidate_pool = max(end, 200)
            ranked = self._get_semantic_searcher().search(
                query,
                top_k=candidate_pool,
            )

        else:
            raise ValueError(
                f"Unknown search algorithm: {algorithm}. Supported: tfidf, bm25, semantic"
            )

        results = []

        for doc_id, score, term_scores in ranked[start:end]:
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

        total_pages = (
            (len(ranked) + effective_per_page - 1) // effective_per_page
            if effective_per_page > 0
            else 1
        )

        return {
            "query": query,
            "results": results,
            "total_results": len(ranked),
            "page": effective_page,
            "per_page": effective_per_page,
            "total_pages": total_pages,
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

        if len(self.index.vocabulary) != self._autocomplete_cache_size:
            self._autocomplete_cache = sorted(self.index.vocabulary)
            self._autocomplete_cache_size = len(self.index.vocabulary)

        start = bisect_left(self._autocomplete_cache, prefix_clean)
        matches = []
        for term in self._autocomplete_cache[start:]:
            if not term.startswith(prefix_clean):
                break
            matches.append(term)
            if len(matches) >= limit:
                break
        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics."""
        return self.index.get_stats()
