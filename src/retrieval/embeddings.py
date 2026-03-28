"""Chroma embedding backend: `F1_EMBEDDING_MODEL` (sentence-transformers).

По умолчанию: каталог `embedding_model/` в корне репозитория (рядом с `src/`), если он
уже заполнен; иначе — идентификатор Hub `ai-forever/ru-en-RoSBERTa`.
"""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_MODEL_DIR = _REPO_ROOT / "embedding_model"
_HUB_MODEL_ID = "ai-forever/ru-en-RoSBERTa"


def _is_sentence_transformer_dir(d: Path) -> bool:
    return d.is_dir() and (d / "config_sentence_transformers.json").is_file()


def get_embedding_model_name() -> str:
    raw = (os.environ.get("F1_EMBEDDING_MODEL") or "").strip()
    if raw:
        candidates: list[Path] = []
        p = Path(raw)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.append(_REPO_ROOT / raw)
            candidates.append(p)
        for c in candidates:
            if _is_sentence_transformer_dir(c):
                return str(c.resolve())
        return raw
    if _is_sentence_transformer_dir(_LOCAL_MODEL_DIR):
        return str(_LOCAL_MODEL_DIR.resolve())
    return _HUB_MODEL_ID


def get_embedding_function():
    """Return a Chroma EmbeddingFunction. Same instance semantics as Chroma expects per process."""
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=get_embedding_model_name())
