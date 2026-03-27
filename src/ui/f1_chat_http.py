"""Sync HTTP helpers for the F1 Assistant async chat API via httpx.

Uses a 30s timeout on the client (see httpx.Timeout(30.0)).
"""

from __future__ import annotations

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(30.0)


def start_chat_http(
    client: httpx.Client,
    base_url: str,
    access_code: str,
    question: str,
) -> str:
    base = base_url.rstrip("/")
    response = client.post(
        f"{base}/start_chat",
        json={"access_code": access_code, "question": question},
    )
    response.raise_for_status()
    data = response.json()
    return str(data["session_id"])


def get_message_status(client: httpx.Client, base_url: str, session_id: str) -> dict:
    base = base_url.rstrip("/")
    response = client.get(
        f"{base}/message_status",
        headers={"X-Session-Id": session_id},
    )
    response.raise_for_status()
    return response.json()


def post_next_message(client: httpx.Client, base_url: str, session_id: str) -> dict:
    base = base_url.rstrip("/")
    response = client.post(
        f"{base}/next_message",
        headers={"X-Session-Id": session_id},
        json={},
    )
    response.raise_for_status()
    return response.json()
