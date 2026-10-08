import math
from collections import defaultdict
from typing import Dict, List, Any

class InvertedIndex:
    def __init__(self):
        # index: term -> { doc_id -> {"tf": term_frequency, "positions": [pos1, pos2]} }
        self.index: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        # documents metadata: doc_id -> {"id": ..., "title": ..., "content": ..., "category": ...}
        self.documents: Dict[str, Dict[str, Any]] = {}
        # doc_lengths: doc_id -> total_term_count
        self.doc_lengths: Dict[str, int] = {}
        # Total unique terms
        self.vocabulary: set = set()

    def add_document(self, doc_id: str, title: str, content: str, category: str = "General", url: str = "#", tokens_with_pos: List = None):
        """
        Indexes a document into the inverted index structure.
        """
        self.documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "url": url
        }

        total_tokens = len(tokens_with_pos)
        self.doc_lengths[doc_id] = total_tokens

        # Process each token and update inverted index posting list
        for token, pos, start_char, end_char in tokens_with_pos:
            self.vocabulary.add(token)

            if doc_id not in self.index[token]:
                self.index[token][doc_id] = {
                    "tf": 0,
                    "positions": []
                }

            self.index[token][doc_id]["tf"] += 1
            self.index[token][doc_id]["positions"].append(pos)

    def get_document_frequency(self, term: str) -> int:
        """
        Returns number of documents containing the term (DF).
        """
        return len(self.index.get(term, {}))

    def get_postings(self, term: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns the postings dict for a term: { doc_id -> {"tf": ..., "positions": [...]} }.
        """
        return self.index.get(term, {})

    @property
    def total_documents(self) -> int:
        return len(self.documents)

    @property
    def avg_doc_length(self) -> float:
        if not self.doc_lengths:
            return 0.0
        return sum(self.doc_lengths.values()) / float(len(self.doc_lengths))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "vocabulary_size": len(self.vocabulary),
            "avg_doc_length": round(self.avg_doc_length, 2),
            "total_terms_indexed": sum(self.doc_lengths.values())
        }
