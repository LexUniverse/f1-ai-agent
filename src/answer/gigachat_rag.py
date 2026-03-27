from __future__ import annotations

import json
import os
from dataclasses import dataclass

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from pydantic import BaseModel, ValidationError

from src.answer.russian_qna import (
    build_live_structured_ru_answer,
    build_sources_block_ru_from_evidence,
    live_qna_confidence,
    qna_confidence_from_evidence,
)
from src.models.api_contracts import AnswerSection, EvidenceItem, QnAConfidence, StructuredRUAnswer

GIGACHAT_SUCCESS_ROUTE = "gigachat_rag"
GIGACHAT_FALLBACK_ROUTE = "template_fallback"
GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU = "Ответ подготовлен по шаблону: нейросеть GigaChat сейчас недоступна."

_SYSTEM_HISTORICAL = """Ты помощник по Формуле 1. Отвечай на русском, опираясь только на фрагменты контекста [1]..[n].
Верни один JSON-объект без markdown и без текста вокруг. Ключи: message (короткая строка для пользователя), sections (массив объектов с heading и body)."""

_SYSTEM_LIVE = """Ты помощник по Формуле 1. В контексте даны актуальные данные (не из исторической базы). Ответь на русском.
Верни один JSON-объект без markdown и без текста вокруг. Ключи: message (короткая строка для пользователя), sections (массив объектов с heading и body)."""


@dataclass
class GigachatRUSynthesisResult:
    message: str
    structured_answer: StructuredRUAnswer
    confidence: QnAConfidence


def append_fallback_disclosure_ru(message: str) -> str:
    if GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU not in message:
        return f"{message} — {GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU}"
    return message


def _client_kwargs() -> dict:
    # Credentials и прочее подхватываются из GIGACHAT_* через gigachat.Settings, если не передать явно.
    return {
        "timeout": float(os.environ.get("GIGACHAT_TIMEOUT", "30")),
        "max_retries": int(os.environ.get("GIGACHAT_MAX_RETRIES", "2")),
        "verify_ssl_certs": os.environ.get("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true",
    }


def _model_name() -> str:
    return os.environ.get("GIGACHAT_MODEL", "GigaChat")


class _LLMJsonPayload(BaseModel):
    message: str
    sections: list[AnswerSection]


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _parse_and_validate_payload(content: str) -> tuple[str, list[AnswerSection]]:
    data = json.loads(_strip_json_fence(content))
    env = _LLMJsonPayload.model_validate(data)
    return env.message, env.sections


def _chat_completion_json(
    *,
    system: str,
    user: str,
) -> tuple[str, list[AnswerSection]]:
    model = _model_name()
    last_exc: Exception | None = None
    with GigaChat(**_client_kwargs()) as client:
        messages: list[Messages] = [
            Messages(role=MessagesRole.SYSTEM, content=system),
            Messages(role=MessagesRole.USER, content=user),
        ]
        resp = client.chat(Chat(model=model, messages=messages))
        content = resp.choices[0].message.content
        try:
            return _parse_and_validate_payload(content)
        except (json.JSONDecodeError, ValidationError) as e:
            last_exc = e
            messages.append(Messages(role=MessagesRole.ASSISTANT, content=content))
            messages.append(
                Messages(
                    role=MessagesRole.USER,
                    content=f"Неверный формат ответа: {e}. Верни только валидный JSON с ключами message и sections.",
                )
            )
            resp2 = client.chat(Chat(model=model, messages=messages))
            content2 = resp2.choices[0].message.content
            try:
                return _parse_and_validate_payload(content2)
            except (json.JSONDecodeError, ValidationError) as e2:
                raise e2 from last_exc


def gigachat_synthesize_historical(*, evidence: list[EvidenceItem], user_question: str) -> GigachatRUSynthesisResult:
    lines = [f"[{i}] {item.source_id}: {item.snippet}" for i, item in enumerate(evidence, start=1)]
    user = f"Вопрос пользователя: {user_question}\n\nКонтекст:\n" + "\n".join(lines)
    msg, sections = _chat_completion_json(system=_SYSTEM_HISTORICAL, user=user)
    sources_block_ru, citation_count = build_sources_block_ru_from_evidence(evidence)
    conf = qna_confidence_from_evidence(evidence)
    structured = StructuredRUAnswer(
        sections=sections,
        sources_block_ru=sources_block_ru,
        citation_count=citation_count,
    )
    return GigachatRUSynthesisResult(message=msg, structured_answer=structured, confidence=conf)


def gigachat_synthesize_live(*, summary_ru: str, user_question: str, as_of_utc_z: str) -> GigachatRUSynthesisResult:
    user = (
        f"Вопрос пользователя: {user_question}\n\n"
        f"Актуальные данные (не из исторической базы):\n{summary_ru}\n(на момент {as_of_utc_z})"
    )
    msg, sections = _chat_completion_json(system=_SYSTEM_LIVE, user=user)
    base = build_live_structured_ru_answer(summary_ru=summary_ru)
    conf = live_qna_confidence()
    structured = StructuredRUAnswer(
        sections=sections,
        sources_block_ru=base.sources_block_ru,
        citation_count=base.citation_count,
    )
    return GigachatRUSynthesisResult(message=msg, structured_answer=structured, confidence=conf)
