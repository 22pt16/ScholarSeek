
import hashlib
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticSearcher:
    """
    Semantic search over research-paper titles and abstracts.

    Paper embeddings are cached on disk so they do not need to be
    regenerated every time the application starts.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, documents, cache_path=None):
        self.documents = dict(documents)
        self.doc_ids = list(documents.keys())
        self._custom_cache = cache_path is not None

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

        if self.texts:
            self.fingerprint = self._make_fingerprint()
            self._load_or_create_embeddings()
        else:
            self.fingerprint = ""
            self.embeddings = np.empty((0, 384), dtype=np.float32)

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
            self.model = SentenceTransformer(self.MODEL_NAME)

        return self.model

    def _load_or_create_embeddings(self):
        if self.cache_path.exists():
            try:
                with np.load(
                    self.cache_path,
                    allow_pickle=False,
                ) as cache:
                    cached_fingerprint = str(
                        cache["fingerprint"].item()
                    )

                    cached_ids = cache["doc_ids"].tolist()

                    if (
                        cached_fingerprint == self.fingerprint
                        and cached_ids == self.doc_ids
                    ):
                        self.embeddings = cache["embeddings"]

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

        model = self._get_model()

        self.embeddings = model.encode(
            self.texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        # Only overwrite cache if explicitly configured or full corpus (prevent wiping 20k cache on small test sets)
        if self._custom_cache or len(self.texts) >= 1000:
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

    def add_document(self, doc_id, document):
        """Dynamically index or update a document and its embedding vector."""
        self.documents[doc_id] = document
        text = self._document_text(document)
        model = self._get_model()
        new_vec = model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        if doc_id in self.doc_ids:
            idx = self.doc_ids.index(doc_id)
            self.texts[idx] = text
            if self.embeddings is not None and len(self.embeddings) > idx:
                self.embeddings[idx] = new_vec[0]
        else:
            self.doc_ids.append(doc_id)
            self.texts.append(text)
            if self.embeddings is not None and len(self.embeddings) > 0:
                self.embeddings = np.vstack([self.embeddings, new_vec])
            else:
                self.embeddings = new_vec

    def search(self, query, top_k=10):
        """
        Rank documents using cosine similarity.

        Because document and query vectors are normalized, their
        dot product equals cosine similarity.
        """
        if not query or not query.strip():
            return []

        if not self.doc_ids or self.embeddings is None or len(self.embeddings) == 0:
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
                    {"semantic": round(score, 4)},
                )
            )

        return results
