"""Streamlit operator UI for the F1 Assistant API (local HTTP client)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.f1_chat_http import DEFAULT_TIMEOUT, get_message_status, post_next_message, start_chat_http
from src.ui.provenance_display import (
    fetch_subsection_md,
    rag_section_md,
    synthesis_section_md,
    use_unified_provenance_expander,
    web_section_md,
)

POLL_SECONDS = 0.75
STATUS_TIMEOUT_SECONDS = 60.0


def _base_url() -> str:
    return os.environ.get("F1_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _http_error_message(exc: httpx.HTTPStatusError) -> str:
    resp = exc.response
    try:
        data = resp.json()
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
    except Exception:
        pass
    return resp.text[:500] or f"HTTP {resp.status_code}"


def _render_assistant_block(content: str, details: dict) -> None:
    st.markdown(content)

    if use_unified_provenance_expander(details):
        prov = details.get("provenance")
        if not isinstance(prov, dict):
            prov = {}
        with st.expander("Происхождение ответа", expanded=False):
            rag = prov.get("rag")
            if isinstance(rag, dict):
                rmd = rag_section_md(rag)
                if rmd.strip():
                    st.markdown("### Контекст (RAG)")
                    st.markdown(rmd)
            if "web" in prov:
                webp = prov.get("web")
                if isinstance(webp, dict):
                    wmd = web_section_md(webp)
                    fetch = webp.get("fetch")
                    has_fetch = isinstance(fetch, dict)
                    if wmd.strip() or has_fetch:
                        st.markdown("### Веб-поиск")
                        if wmd.strip():
                            st.markdown(wmd)
                        if has_fetch:
                            st.markdown("### Загрузка страницы")
                            st.markdown(fetch_subsection_md(fetch))
            synth = prov.get("synthesis")
            if isinstance(synth, dict):
                smd = synthesis_section_md(synth)
                if smd.strip():
                    st.markdown("### Синтез")
                    st.markdown(smd)
    else:
        structured = details.get("structured_answer")
        sources = None
        if isinstance(structured, dict):
            sources = structured.get("sources_block_ru")
        if sources:
            st.markdown("**Источники**")
            st.markdown(f"```\n{sources}\n```")

        web = details.get("web")
        if isinstance(web, dict):
            with st.expander("Веб-поиск", expanded=False):
                st.json(web)

        synth = details.get("synthesis")
        if isinstance(synth, dict):
            with st.expander("Синтез", expanded=False):
                route = synth.get("route", "")
                err_cls = synth.get("gigachat_error_class")
                parts = [f"route: `{route}`"]
                if err_cls:
                    parts.append(f"gigachat_error_class: `{err_cls}`")
                st.markdown(" · ".join(parts))

    live = details.get("live")
    if isinstance(live, dict):
        with st.expander("Актуальные данные (live)", expanded=False):
            st.json(live)


def main() -> None:
    st.set_page_config(page_title="F1 Assistant", layout="wide")
    st.title("F1 Assistant")
    base = _base_url()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    with st.sidebar:
        st.caption("API")
        st.code(base, language="text")

    if not st.session_state.messages:
        st.info("Введите код и вопрос, затем нажмите «Отправить вопрос».")

    with st.container(height=520, border=True):
        for msg in st.session_state.messages:
            role = msg["role"]
            with st.chat_message(role):
                if role == "assistant" and msg.get("details"):
                    _render_assistant_block(msg["content"], msg["details"])
                else:
                    st.markdown(msg["content"])

    st.divider()

    ac = st.text_input("Код доступа", placeholder="Введите персональный код", key="access_code")
    q = st.text_input(
        "Вопрос",
        placeholder="Например: кто выиграл Гран-при Монако в 1996?",
        key="question",
    )

    c1, c2 = st.columns(2)
    with c1:
        send = st.button("Отправить вопрос", type="primary")
    with c2:
        new_chat = st.button("Новый чат")

    if new_chat:
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    if send:
        if not (ac or "").strip() or not (q or "").strip():
            st.warning("Нужны непустой код доступа и вопрос.")
        else:
            try:
                with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                    try:
                        sid = start_chat_http(client, base, ac.strip(), q.strip())
                    except httpx.HTTPStatusError as exc:
                        st.error(f"Ошибка: {_http_error_message(exc)}")
                        return

                    st.session_state.session_id = sid

                    deadline = time.monotonic() + STATUS_TIMEOUT_SECONDS
                    with st.spinner("Ожидаем ответ…"):
                        while time.monotonic() < deadline:
                            try:
                                st_payload = get_message_status(client, base, sid)
                            except httpx.HTTPStatusError as exc:
                                st.error(f"Ошибка: {_http_error_message(exc)}")
                                return
                            last_status = st_payload.get("status", "")
                            if last_status in ("ready", "failed"):
                                break
                            time.sleep(POLL_SECONDS)
                        else:
                            st.error(
                                f"Превышено время ожидания ответа (60 с). Проверьте, что API запущен на {base}."
                            )
                            return

                    try:
                        nxt = post_next_message(client, base, sid)
                    except httpx.HTTPStatusError as exc:
                        st.error(f"Ошибка: {_http_error_message(exc)}")
                        return

                    assistant_text = nxt.get("message", "") or ""
                    details = nxt.get("details") if isinstance(nxt.get("details"), dict) else {}
                    st.session_state.messages.append({"role": "user", "content": q.strip()})
                    st.session_state.messages.append(
                        {"role": "assistant", "content": assistant_text, "details": details},
                    )
            except httpx.RequestError as exc:
                st.error(f"Ошибка сети: {exc}")

            st.rerun()


if __name__ == "__main__":
    main()
