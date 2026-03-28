"""Pure helpers for Streamlit provenance vs legacy branching (no Streamlit imports)."""

from __future__ import annotations

_SNIP_MAX = 400


def _trunc(s: str) -> str:
    if len(s) <= _SNIP_MAX:
        return s
    return s[:_SNIP_MAX] + "…"


def use_unified_provenance_expander(details: dict) -> bool:
    """True when details carry a non-empty provenance snapshot worth a single expander."""
    prov = details.get("provenance")
    if not isinstance(prov, dict):
        return False

    rag = prov.get("rag")
    if isinstance(rag, dict):
        ev = rag.get("evidence")
        if isinstance(ev, list) and len(ev) > 0:
            return True

    web = prov.get("web")
    if isinstance(web, dict):
        queries = web.get("queries")
        results = web.get("results")
        if (isinstance(queries, list) and len(queries) > 0) or (
            isinstance(results, list) and len(results) > 0
        ):
            return True

    synth = prov.get("synthesis")
    if isinstance(synth, dict):
        route = synth.get("route")
        err_cls = synth.get("gigachat_error_class")
        if route or err_cls:
            return True

    return False


def rag_section_md(prov_rag: dict) -> str:
    parts: list[str] = []
    nq = prov_rag.get("normalized_query")
    if nq is not None and str(nq).strip():
        parts.append(f"**Запрос:** {_trunc(str(nq))}")
    evidence = prov_rag.get("evidence") or []
    if isinstance(evidence, list) and evidence:
        lines: list[str] = []
        for i, item in enumerate(evidence[:20], 1):
            if isinstance(item, dict):
                sid = item.get("source_id", "")
                snip = _trunc(str(item.get("snippet", "")))
                lines.append(f"{i}. `{sid}` — {snip}")
            else:
                lines.append(f"{i}. {_trunc(str(item))}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts) if parts else ""


def web_section_md(prov_web: dict) -> str:
    parts: list[str] = []
    queries = prov_web.get("queries") or []
    if isinstance(queries, list) and queries:
        qtxt = ", ".join(_trunc(str(q)) for q in queries[:12])
        parts.append(f"**Запросы:** {qtxt}")
    results = prov_web.get("results") or []
    if isinstance(results, list) and results:
        lines: list[str] = []
        for i, r in enumerate(results[:15], 1):
            if isinstance(r, dict):
                title = _trunc(str(r.get("title") or ""))
                url = str(r.get("url") or "")
                snip = _trunc(str(r.get("content_snippet") or ""))
                lines.append(f"{i}. **{title}** — `{url}`\n   {snip}")
            else:
                lines.append(f"{i}. {_trunc(str(r))}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts) if parts else ""


def fetch_subsection_md(fetch: dict) -> str:
    if not isinstance(fetch, dict):
        return ""
    url = fetch.get("url", "")
    ok = fetch.get("ok")
    err = fetch.get("error")
    exc = fetch.get("excerpt_preview")
    lines = [f"- **URL:** `{url}`", f"- **ok:** `{ok}`"]
    if err is not None and str(err).strip():
        lines.append(f"- **error:** {_trunc(str(err))}")
    if exc is not None and str(exc).strip():
        lines.append(f"- **Фрагмент:** {_trunc(str(exc))}")
    return "\n".join(lines)


def synthesis_section_md(prov_synth: dict) -> str:
    route = prov_synth.get("route")
    err_cls = prov_synth.get("gigachat_error_class")
    if not route and not err_cls:
        return ""
    parts: list[str] = []
    if route is not None:
        parts.append(f"**route:** `{route}`")
    if err_cls:
        parts.append(f"**gigachat_error_class:** `{err_cls}`")
    return " · ".join(parts)
