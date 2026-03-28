"""Normalize user text for retrieval (no entity alias dictionary)."""

from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("ё", "е")
    normalized = re.sub(r"[-_/]", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_retrieval_query(query: str) -> tuple[str, list[str], list[str]]:
    """
    Returns (normalized_query, canonical_entity_ids, entity_tags).

    canonical_entity_ids and entity_tags are always empty — retrieval is fully vector-driven.
    """
    nq = _normalize(query)
    return nq, [], []
