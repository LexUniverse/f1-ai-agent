"""Chroma embedding backend: `F1_EMBEDDING_MODEL` (sentence-transformers), default ru-en-RoSBERTa."""

from __future__ import annotations

import os

_DEFAULT_MODEL = "ai-forever/ru-en-RoSBERTa"


def get_embedding_model_name() -> str:
    name = (os.environ.get("F1_EMBEDDING_MODEL") or _DEFAULT_MODEL).strip()
    return name or _DEFAULT_MODEL


def get_embedding_function():
    """Return a Chroma EmbeddingFunction. Same instance semantics as Chroma expects per process."""
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=get_embedding_model_name())
