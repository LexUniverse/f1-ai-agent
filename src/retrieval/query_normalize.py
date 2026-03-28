"""Normalize user text for retrieval (no entity alias dictionary)."""

from __future__ import annotations

import re
import unicodedata

_YEAR_TOKEN = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("ё", "е")
    normalized = re.sub(r"[-_/]", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_year_int_from_query(query: str) -> int | None:
    """
    First plausible F1 season year in the question (1950–2035), for Chroma metadata filter.
    Used to scope retrieval to `year` in chunk metadata when the index is full.
    """
    if not (query or "").strip():
        return None
    for m in _YEAR_TOKEN.finditer(query):
        y = int(m.group(1))
        if 1950 <= y <= 2035:
            return y
    return None


def normalize_retrieval_query(query: str) -> tuple[str, list[str], list[str]]:
    """
    Returns (normalized_query, canonical_entity_ids, entity_tags).

    canonical_entity_ids and entity_tags are always empty — retrieval is fully vector-driven.
    """
    nq = _normalize(query)
    return nq, [], []
