"""Chroma embedding backend (production: ru-en-RoSBERTa; tests may override via env)."""

from __future__ import annotations

import os


def get_embedding_function():
    """Return a Chroma EmbeddingFunction. Same instance semantics as Chroma expects per process."""
    from chromadb.utils import embedding_functions

    if os.environ.get("F1_CHROMA_DEFAULT_EMBEDDINGS", "").strip() in ("1", "true", "yes"):
        return embedding_functions.DefaultEmbeddingFunction()

    model = os.environ.get("F1_EMBEDDING_MODEL", "ai-forever/ru-en-RoSBERTa").strip()
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
