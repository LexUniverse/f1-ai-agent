from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from pydantic import BaseModel, ValidationError

from src.answer.russian_qna import build_sources_block_ru_from_evidence
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer

GIGACHAT_SUCCESS_ROUTE = "gigachat_rag"
GIGACHAT_FALLBACK_ROUTE = "template_fallback"
GIGACHAT_WEB_ROUTE = "gigachat_web"
GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU = "Ответ подготовлен по шаблону: нейросеть GigaChat сейчас недоступна."

# src/answer/gigachat_rag.py → parents[2] = репозиторий (для относительных путей к certs/).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CA_FILES = (
    _REPO_ROOT / "certs" / "russiantrustedca2024.pem",
    _REPO_ROOT / "certs" / "russiantrustedca.pem",
)

_SYSTEM_HISTORICAL = """Ты помощник по Формуле 1. Отвечай на русском, опираясь только на фрагменты контекста [1]..[n].
Верни один JSON-объект без markdown и без текста вокруг. Ключи: message (короткая строка для пользователя), sections (массив объектов с heading и body).

Требования к ответу:
- Дай прямой ответ на исходный вопрос пользователя по смыслу; не ограничивайся перефразированием вопроса.
- Не выдавай только текст поискового запроса или список источников без содержательного предложения с фактом.
- Не повторяй только формулировку вопроса без новой информации из контекста."""

_SYSTEM_WEB = """Ты помощник по Формуле 1. Ниже даны выдержки из веб-поиска с URL. Отвечай на русском строго по этим выдержкам; не выдумывай факты вне них.
Верни один JSON-объект без markdown и без текста вокруг. Ключи: message (короткая строка для пользователя), sections (массив объектов с heading и body).

Требования к ответу:
- Дай прямой ответ на исходный вопрос пользователя по смыслу; не ограничивайся перефразированием вопроса.
- Не выдавай только строку запроса или перечень URL без фактического ответа на вопрос.
- Не используй только список источников без хотя бы одного предложения с фактом из выдержек."""

_SYSTEM_TAVILY_QUERY = (
    "Сформулируй одну короткую поисковую строку (на английском или русском) для веб-поиска по Формуле 1. "
    "Ответ — только эта строка, без кавычек, без пояснений, без JSON."
)

_SYSTEM_JUDGE = """Тебе дан вопрос пользователя и фрагменты контекста из исторической базы.
Оцени, достаточно ли контекста, чтобы дать содержательный ответ на вопрос (не обязательно идеальный, но лучше, чем «данных нет»).
Верни один JSON-объект без markdown: {"sufficient": true} или {"sufficient": false}."""

_SYSTEM_SUPERVISOR_ACCEPT = """Тебе дан вопрос пользователя и предлагаемый ответ ассистента на русском.
Реши, отвечает ли предлагаемый текст на вопрос по существу (допустимы краткие ответы, если вопрос узкий).

Требования:
- Ответ должен содержать содержательную информацию, а не только повтор вопроса, только поисковый запрос или только список ссылок без фактов.
- Если текст явно не отвечает на вопрос или является пустой отпиской, считай ответ неприемлемым.

Верни один JSON-объект без markdown: {"accept": true} или {"accept": false}."""


@dataclass
class GigachatRUSynthesisResult:
    message: str
    structured_answer: StructuredRUAnswer


def append_fallback_disclosure_ru(message: str) -> str:
    if GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU not in message:
        return f"{message} — {GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU}"
    return message


def _resolved_ca_bundle_file() -> str | None:
    """Путь к CA для verify: из GIGACHAT_CA_BUNDLE_FILE или встроенные certs/*.pem в репозитории."""
    raw = os.environ.get("GIGACHAT_CA_BUNDLE_FILE", "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        return str(path.resolve())
    for candidate in _DEFAULT_CA_FILES:
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def _client_kwargs() -> dict:
    kwargs: dict = {
        "timeout": float(os.environ.get("GIGACHAT_TIMEOUT", "30")),
        "max_retries": int(os.environ.get("GIGACHAT_MAX_RETRIES", "2")),
        "verify_ssl_certs": os.environ.get("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true",
    }
    ca = _resolved_ca_bundle_file()
    if ca:
        kwargs["ca_bundle_file"] = ca
    return kwargs


def _model_name() -> str:
    return os.environ.get("GIGACHAT_MODEL", "GigaChat")


class _LLMJsonPayload(BaseModel):
    message: str
    sections: list[AnswerSection]


class _SufficiencyJudgePayload(BaseModel):
    sufficient: bool


class _SupervisorAcceptPayload(BaseModel):
    accept: bool


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


def _chat_completion_plain_line(*, system: str, user: str) -> str:
    model = _model_name()
    with GigaChat(**_client_kwargs()) as client:
        messages: list[Messages] = [
            Messages(role=MessagesRole.SYSTEM, content=system),
            Messages(role=MessagesRole.USER, content=user),
        ]
        resp = client.chat(Chat(model=model, messages=messages))
        line = (resp.choices[0].message.content or "").strip().split("\n")[0].strip()
        return line[:500]


def gigachat_author_tavily_query(*, user_question: str) -> str:
    try:
        q = _chat_completion_plain_line(system=_SYSTEM_TAVILY_QUERY, user=f"Вопрос: {user_question}")
        return q if q else user_question[:200]
    except Exception:
        return user_question[:200].strip()


def _web_sources_block_ru(web_results: list[dict]) -> tuple[str, int]:
    lines: list[str] = ["Источники:"]
    for n, row in enumerate(web_results, start=1):
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        excerpt = content[:80] + ("…" if len(content) > 80 else "")
        lines.append(f"[{n}] {url} — {excerpt}")
    return "\n".join(lines), len(web_results)


def gigachat_synthesize_from_web_results(
    *, user_question: str, web_results: list[dict]
) -> GigachatRUSynthesisResult:
    lines = []
    for i, row in enumerate(web_results, start=1):
        url = row.get("url", "")
        title = row.get("title", "")
        body = str(row.get("content", ""))[:1200]
        head = f"{title} — {url}" if title else str(url)
        lines.append(f"[{i}] URL: {head}\nВыдержка: {body}")
    user = f"Вопрос пользователя: {user_question}\n\nРезультаты поиска:\n" + "\n\n".join(lines)
    msg, sections = _chat_completion_json(system=_SYSTEM_WEB, user=user)
    sources_block_ru, citation_count = _web_sources_block_ru(web_results)
    structured = StructuredRUAnswer(
        sections=sections,
        sources_block_ru=sources_block_ru,
        citation_count=citation_count,
    )
    return GigachatRUSynthesisResult(message=msg, structured_answer=structured)


def gigachat_judge_rag_sufficient(*, user_question: str, evidence: list[EvidenceItem]) -> bool:
    lines = [f"[{i}] {item.source_id}: {item.snippet}" for i, item in enumerate(evidence, start=1)]
    user = f"Вопрос: {user_question}\n\nКонтекст:\n" + "\n".join(lines)
    try:
        model = _model_name()
        with GigaChat(**_client_kwargs()) as client:
            messages: list[Messages] = [
                Messages(role=MessagesRole.SYSTEM, content=_SYSTEM_JUDGE),
                Messages(role=MessagesRole.USER, content=user),
            ]
            resp = client.chat(Chat(model=model, messages=messages))
            content = resp.choices[0].message.content
            data = json.loads(_strip_json_fence(content))
            parsed = _SufficiencyJudgePayload.model_validate(data)
            return bool(parsed.sufficient)
    except Exception:
        return False


def gigachat_supervisor_accept_answer(*, user_question: str, candidate_answer: str) -> bool:
    user = f"Вопрос пользователя:\n{user_question}\n\nПредлагаемый ответ ассистента:\n{candidate_answer}"
    try:
        model = _model_name()
        with GigaChat(**_client_kwargs()) as client:
            messages: list[Messages] = [
                Messages(role=MessagesRole.SYSTEM, content=_SYSTEM_SUPERVISOR_ACCEPT),
                Messages(role=MessagesRole.USER, content=user),
            ]
            resp = client.chat(Chat(model=model, messages=messages))
            content = resp.choices[0].message.content
            data = json.loads(_strip_json_fence(content))
            parsed = _SupervisorAcceptPayload.model_validate(data)
            return bool(parsed.accept)
    except Exception:
        return False


def gigachat_synthesize_historical(*, evidence: list[EvidenceItem], user_question: str) -> GigachatRUSynthesisResult:
    lines = [f"[{i}] {item.source_id}: {item.snippet}" for i, item in enumerate(evidence, start=1)]
    user = f"Вопрос пользователя: {user_question}\n\nКонтекст:\n" + "\n".join(lines)
    msg, sections = _chat_completion_json(system=_SYSTEM_HISTORICAL, user=user)
    sources_block_ru, citation_count = build_sources_block_ru_from_evidence(evidence)
    structured = StructuredRUAnswer(
        sections=sections,
        sources_block_ru=sources_block_ru,
        citation_count=citation_count,
    )
    return GigachatRUSynthesisResult(message=msg, structured_answer=structured)
