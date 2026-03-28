"""Единый лимит длины текста одного RAG-чанка для LLM (символы как грубый прокси токенов)."""

from __future__ import annotations

import os

# Порог по умолчанию: хватает на обзор сезона / полную гонку без раздувания промпта (top_k × лимит ≈ бюджет).
_DEFAULT_MAX_CHARS = 8_000
_MIN = 500
_MAX = 50_000


def max_chars_per_rag_chunk() -> int:
    """
    Сколько символов максимум отдаём в LLM с одного попавшего чанка.

    Задаётся **F1_RAG_MAX_CHARS_PER_CHUNK** (целое). Иначе — дефолт 8000 символов.
    Оценка бюджета: ``top_k * max_chars_per_rag_chunk()`` плюс системные/вопрос сообщения;
    точный токенайзер GigaChat здесь не используем (для RU часто грубо ~3–4 симв. ≈ 1 токен).
    """
    raw = os.environ.get("F1_RAG_MAX_CHARS_PER_CHUNK", "").strip()
    if raw:
        try:
            v = int(raw)
            return max(_MIN, min(v, _MAX))
        except ValueError:
            pass
    return _DEFAULT_MAX_CHARS
