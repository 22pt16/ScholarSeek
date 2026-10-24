
import hashlib
from pathlib import Path
from typing import Optional

import numpy as np


class SemanticSearcher:
    """
    Semantic search over research-paper titles and abstracts.

    Paper embeddings are cached on disk so they do not need to be
    regenerated every time the application starts.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, documents, cache_path=None):
        self.documents = documents
        self.doc_ids = list(documents.keys())

        self.texts = [
            self._document_text(documents[doc_id])
            for doc_id in self.doc_ids
        ]

        self.cache_path = (
            Path(cache_path)
            if cache_path
            else Path(__file__).resolve().parent
            / "cache"
            / "semantic_embeddings.npz"
        )

        self.model = None
        self.embeddings = None
        self.fingerprint: Optional[str] = None

        self._load_or_create_embeddings()

    @staticmethod
    def _document_text(document):
        title = document.get("title", "")

        abstract = (
            document.get("abstract")
            or document.get("content")
            or ""
        )

        return f"{title}. {abstract}".strip()

    def _make_fingerprint(self):
        """
        Identify the current corpus so stale embeddings are not reused.
        """
        digest = hashlib.sha256()
        digest.update(self.MODEL_NAME.encode("utf-8"))

        for doc_id, text in zip(self.doc_ids, self.texts):
            digest.update(doc_id.encode("utf-8"))
            digest.update(b"\0")
            digest.update(text.encode("utf-8"))
            digest.update(b"\n")

        return digest.hexdigest()

    def _get_model(self):
        if self.model is None:
            print(f"Loading semantic model: {self.MODEL_NAME}")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.MODEL_NAME)

        return self.model

    def _load_or_create_embeddings(self):
        if self.cache_path.exists():
            try:
                with np.load(
                    self.cache_path,
                    allow_pickle=False,
                ) as cache:
                    cached_ids = cache["doc_ids"].tolist()

                    if cached_ids == self.doc_ids:
                        self.embeddings = cache["embeddings"]
                        if "fingerprint" in cache:
                            self.fingerprint = str(cache["fingerprint"].item())
                        print(
                            "Loaded cached embeddings:",
                            self.embeddings.shape,
                        )
                        return

            except (ValueError, KeyError, OSError) as exc:
                print("Could not load embedding cache:", exc)

        print(
            f"Generating embeddings for "
            f"{len(self.texts):,} research papers..."
        )

        self.fingerprint = self._make_fingerprint()
        model = self._get_model()

        self.embeddings = model.encode(
            self.texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        np.savez_compressed(
            self.cache_path,
            doc_ids=np.asarray(self.doc_ids, dtype=str),
            embeddings=self.embeddings,
            fingerprint=np.asarray(self.fingerprint),
        )

        print(
            "Embeddings saved to:",
            self.cache_path,
        )

    def search(self, query, top_k=10):
        """
        Rank documents using cosine similarity.

        Because document and query vectors are normalized, their
        dot product equals cosine similarity.
        """
        if not query or not query.strip():
            return []

        model = self._get_model()

        query_vector = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        similarities = self.embeddings @ query_vector

        top_k = max(0, min(top_k, len(self.doc_ids)))

        if top_k == 0:
            return []

        # Partial sorting is faster than sorting the entire corpus.
        candidate_ids = np.argpartition(
            similarities,
            len(similarities) - top_k,
        )[-top_k:]

        candidate_ids = candidate_ids[
            np.argsort(similarities[candidate_ids])[::-1]
        ]

        results = []

        for position in candidate_ids:
            doc_id = self.doc_ids[int(position)]
            score = float(similarities[position])

            results.append(
                (
                    doc_id,
                    score,
                    {"semantic": score},
                )
            )

        return results
