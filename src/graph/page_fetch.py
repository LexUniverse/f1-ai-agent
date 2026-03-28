"""Single-page HTTP fetch for web deepening (Phase 12 SRCH-04)."""

from __future__ import annotations

from html.parser import HTMLParser

import httpx

_USER_AGENT = "F1Assistant/1.4 (+local)"


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        t = data.strip()
        if t:
            self._chunks.append(t)

    def text(self) -> str:
        return "\n".join(self._chunks)


def fetch_url_text_plain(url: str, *, timeout_s: float = 15.0, max_bytes: int = 500_000) -> str:
    """GET url and return rough plain text; empty string on failure or oversize."""
    if not (url or "").strip():
        return ""
    try:
        with httpx.Client(
            timeout=timeout_s,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            resp = client.get(url)
    except (httpx.HTTPError, OSError, ValueError):
        return ""
    if resp.status_code != 200:
        return ""
    body = resp.content
    if len(body) > max_bytes:
        return ""
    try:
        html = body.decode(resp.encoding or "utf-8", errors="replace")
    except Exception:
        return ""
    parser = _TextCollector()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return ""
    return " ".join(parser.text().split())
