"""Shared async HTTP client — connection reuse across coach requests."""

from __future__ import annotations

import os

import httpx

_client: httpx.AsyncClient | None = None

OLLAMA_TIMEOUT = float(os.getenv("RELINK_OLLAMA_TIMEOUT", "45"))


def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def startup_http() -> None:
    get_http_client()


async def shutdown_http() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
