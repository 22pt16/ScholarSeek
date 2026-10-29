"""
Mini Search Engine Package
Information Retrieval Engine implementing Tokenization, Inverted Indexing, TF-IDF / BM25 Ranking, and Spell Correction.
"""
from .engine import SearchEngine
from . import metrics

__all__ = ["SearchEngine", "metrics"]
