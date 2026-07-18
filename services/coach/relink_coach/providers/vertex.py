from __future__ import annotations

import asyncio
from typing import Any

from .config import Settings


async def chat_vertex(
    messages: list[dict[str, str]],
    *,
    settings: Settings,
    temperature: float = 0.6,
    max_tokens: int = 2048,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise RuntimeError("google-genai not installed") from e

    client_kwargs: dict[str, Any] = {}
    if settings.gcp_project:
        client_kwargs = {
            "vertexai": True,
            "project": settings.gcp_project,
            "location": settings.gcp_location,
        }
    client = genai.Client(**client_kwargs)

    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    contents: list[Any] = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    if not contents:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text="Hello")])]

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction="\n".join(system_parts) if system_parts else None,
    )

    def _run() -> str:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=config,
        )
        text = getattr(resp, "text", None) or ""
        if not text and getattr(resp, "candidates", None):
            try:
                text = resp.candidates[0].content.parts[0].text  # type: ignore[index,union-attr]
            except Exception:
                text = str(resp)
        if not text:
            raise RuntimeError("empty gemini response")
        return text

    return await asyncio.to_thread(_run)
