import httpx
import pytest

from src.graph.page_fetch import fetch_url_text_plain


def test_fetch_url_text_plain_strips_html(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><body><p>Hello <b>world</b></p><script>bad()</script></body></html>"
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, content=html))

    class MC(httpx.Client):
        def __init__(self, *a, **kw):
            kw = {**kw, "transport": transport}
            super().__init__(*a, **kw)

    monkeypatch.setattr("src.graph.page_fetch.httpx.Client", MC)
    text = fetch_url_text_plain("https://example.test/page")
    assert "Hello" in text
    assert "world" in text
    assert "<p>" not in text
