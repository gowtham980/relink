from __future__ import annotations

from typing import Any

from ..http_client import get_http_client
from .config import Settings


async def chat_ollama(
    messages: list[dict[str, str]],
    *,
    settings: Settings,
    role: str = "coach",
    temperature: float = 0.6,
    max_tokens: int = 2048,
) -> str:
    if not settings.api_key:
        raise RuntimeError("OLLAMA_API_KEY not set")
    model = settings.model_for(role)
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = f"{settings.api_base}/chat/completions"
    client = get_http_client()
    r = await client.post(url, headers=headers, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"ollama status={r.status_code} body={r.text[:300]}")
    data = r.json()
    msg = data["choices"][0]["message"]
    content = (msg.get("content") or "").strip()
    if content:
        return content
    reasoning = (msg.get("reasoning") or "").strip()
    if reasoning:
        raise RuntimeError("empty ollama content (reasoning-only; increase max_tokens)")
    raise RuntimeError("empty ollama content")
