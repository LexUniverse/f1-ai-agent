"""Single-shot Tavily search via LangChain Community (bounded timeout)."""

from __future__ import annotations

import os
from typing import Any

import requests
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TAVILY_API_URL, TavilySearchAPIWrapper
from pydantic import Field


class TavilyConfigError(RuntimeError):
    """Raised when Tavily is not configured (missing API key)."""


class _TavilySearchAPIWrapperWithTimeout(TavilySearchAPIWrapper):
    """Same as upstream wrapper but honors HTTP timeout (TAVILY_TIMEOUT)."""

    request_timeout: float = Field(default=10.0)

    def raw_results(  # type: ignore[override]
        self,
        query: str,
        max_results: int | None = 5,
        search_depth: str | None = "advanced",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_answer: bool | None = False,
        include_raw_content: bool | None = False,
        include_images: bool | None = False,
    ) -> dict[str, Any]:
        include_domains = include_domains or []
        exclude_domains = exclude_domains or []
        params = {
            "api_key": self.tavily_api_key.get_secret_value(),
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }
        response = requests.post(
            f"{TAVILY_API_URL}/search",
            json=params,
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        return response.json()


def run_tavily_search_once(query: str) -> list[dict[str, Any]]:
    """
    Run one Tavily search. Results are dicts with url, content, and optional title.

    Reads TAVILY_API_KEY from the environment. Uses TavilySearchResults from
    langchain_community; HTTP timeout from TAVILY_TIMEOUT (default 10s).
    """
    if not (os.environ.get("TAVILY_API_KEY") or "").strip():
        raise TavilyConfigError("TAVILY_API_KEY is not set")

    timeout = float(os.environ.get("TAVILY_TIMEOUT", "10"))
    max_results = int(os.environ.get("TAVILY_MAX_RESULTS", "5"))

    tool = TavilySearchResults(
        max_results=max_results,
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
        include_images=False,
        api_wrapper=_TavilySearchAPIWrapperWithTimeout(request_timeout=timeout),
    )
    raw = tool.invoke({"query": query})
    if isinstance(raw, str):
        raise RuntimeError(raw)

    normalized: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        out: dict[str, Any] = {"url": url, "content": content}
        if row.get("title") is not None:
            out["title"] = str(row["title"])
        normalized.append(out)
    return normalized
