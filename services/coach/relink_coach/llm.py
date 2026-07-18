"""ModelRouter: Ollama Cloud primary → Vertex Gemini fallback → mock."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any

from .http_client import get_http_client
from .json_util import extract_json
from .mock_replies import mock_reply

logger = logging.getLogger("relink.llm")

PROVIDER = os.getenv("RELINK_LLM_PROVIDER", "mock").lower()
API_BASE = os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1").rstrip("/")
API_KEY = os.getenv("OLLAMA_API_KEY", "")
MODEL_COACH = os.getenv("RELINK_MODEL_COACH", "glm-5.2")
MODEL_STRUCT = os.getenv("RELINK_MODEL_STRUCT", "kimi-k2.7-code")
FALLBACK = os.getenv("RELINK_LLM_FALLBACK", "vertex").lower()
GEMINI_MODEL = os.getenv("RELINK_GEMINI_MODEL", "gemini-2.0-flash")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", ""))
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ALLOW_MOCK_FALLBACK = os.getenv("RELINK_ALLOW_MOCK_FALLBACK", "1") == "1"

# Token budgets by role. Reasoning models (e.g. glm-5.2) spend tokens on
# chain-of-thought before content — budgets must leave room for the reply.
DEFAULT_TOKENS = {"coach": 2048, "struct": 2048, "nudge": 1024}


@dataclass
class ChatResult:
    text: str
    provider_used: str
    fallback: bool = False
    fallback_reason: str | None = None
    model: str | None = None

    def meta(self) -> dict[str, Any]:
        return asdict(self)


def _strip_provider_prefix(model: str) -> str:
    m = (model or "").strip()
    if "/" in m:
        return m.split("/", 1)[1]
    return m


def ollama_model_id(role: str = "coach") -> str:
    raw = MODEL_STRUCT if role == "struct" else MODEL_COACH
    return _strip_provider_prefix(raw)


def resolve_provider() -> str:
    if PROVIDER == "gemini":
        return "gemini" if _vertex_ready() else ("mock" if ALLOW_MOCK_FALLBACK else "gemini")
    if PROVIDER == "ollama":
        if API_KEY:
            return "ollama"
        return "mock" if ALLOW_MOCK_FALLBACK else "ollama"
    if PROVIDER == "mock":
        return "mock"
    return "mock"


def _vertex_ready() -> bool:
    return bool(GCP_PROJECT) or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or bool(
        os.getenv("K_SERVICE")
    )


def health_info() -> dict[str, Any]:
    return {
        "ok": True,
        "provider": resolve_provider(),
        "fallback": FALLBACK if FALLBACK != "none" else None,
        "model_coach": ollama_model_id("coach"),
        "model_struct": ollama_model_id("struct"),
        "gemini_model": GEMINI_MODEL,
        "project": GCP_PROJECT or None,
        "location": GCP_LOCATION,
        "ollama_configured": bool(API_KEY),
        "adk": _adk_available(),
        "ollama_timeout_s": float(os.getenv("RELINK_OLLAMA_TIMEOUT", "45")),
    }


def _adk_available() -> bool:
    try:
        import google.adk  # noqa: F401

        return True
    except Exception:
        return False


async def chat(
    messages: list[dict[str, str]],
    *,
    role: str = "coach",
    temperature: float = 0.6,
    max_tokens: int | None = None,
) -> ChatResult:
    """Primary Ollama → Vertex Gemini fallback → optional mock."""
    if max_tokens is None:
        max_tokens = DEFAULT_TOKENS.get(role, 400)
    primary = resolve_provider()

    if primary == "mock":
        return ChatResult(text=mock_reply(messages, role=role), provider_used="mock", model="mock")

    if primary == "gemini":
        try:
            text = await _chat_vertex(messages, temperature=temperature, max_tokens=max_tokens)
            return ChatResult(
                text=text, provider_used="gemini", model=GEMINI_MODEL, fallback=False
            )
        except Exception as e:
            logger.warning("Gemini primary failed: %s", e)
            if ALLOW_MOCK_FALLBACK:
                return ChatResult(
                    text=mock_reply(messages, role=role),
                    provider_used="mock",
                    fallback=True,
                    fallback_reason=str(e)[:200],
                    model="mock",
                )
            raise

    try:
        text = await _chat_ollama(
            messages, role=role, temperature=temperature, max_tokens=max_tokens
        )
        return ChatResult(
            text=text, provider_used="ollama", model=ollama_model_id(role), fallback=False
        )
    except Exception as e:
        reason = _classify_error(e)
        logger.warning("Ollama failed (%s): %s", reason, e)
        if FALLBACK == "vertex" and _vertex_ready():
            try:
                text = await _chat_vertex(
                    messages, temperature=temperature, max_tokens=max_tokens
                )
                return ChatResult(
                    text=text,
                    provider_used="gemini",
                    fallback=True,
                    fallback_reason=reason,
                    model=GEMINI_MODEL,
                )
            except Exception as ge:
                logger.warning("Vertex fallback failed: %s", ge)
                if ALLOW_MOCK_FALLBACK:
                    return ChatResult(
                        text=mock_reply(messages, role=role),
                        provider_used="mock",
                        fallback=True,
                        fallback_reason=f"ollama:{reason};vertex:{ge}"[:200],
                        model="mock",
                    )
                raise
        if ALLOW_MOCK_FALLBACK:
            return ChatResult(
                text=mock_reply(messages, role=role),
                provider_used="mock",
                fallback=True,
                fallback_reason=reason,
                model="mock",
            )
        raise


def _classify_error(e: Exception) -> str:
    s = str(e).lower()
    if "401" in s or "403" in s or "auth" in s:
        return "auth"
    if "429" in s or "quota" in s or "rate" in s:
        return "quota"
    if "timeout" in s:
        return "timeout"
    if "5" in s and "status" in s:
        return "upstream"
    return "upstream"


async def _chat_ollama(
    messages: list[dict[str, str]],
    *,
    role: str,
    temperature: float,
    max_tokens: int,
) -> str:
    if not API_KEY:
        raise RuntimeError("OLLAMA_API_KEY not set")
    model = ollama_model_id(role)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = f"{API_BASE}/chat/completions"
    client = get_http_client()
    r = await client.post(url, headers=headers, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"ollama status={r.status_code} body={r.text[:300]}")
    data = r.json()
    msg = data["choices"][0]["message"]
    content = (msg.get("content") or "").strip()
    if content:
        return content
    # Some models put draft text only in reasoning when max_tokens is too low
    reasoning = (msg.get("reasoning") or "").strip()
    if reasoning:
        raise RuntimeError(
            "empty ollama content (reasoning-only; increase max_tokens)"
        )
    raise RuntimeError("empty ollama content")


async def _chat_vertex(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise RuntimeError("google-genai not installed") from e

    project = GCP_PROJECT or None
    client_kwargs: dict[str, Any] = {}
    if project:
        client_kwargs = {
            "vertexai": True,
            "project": project,
            "location": GCP_LOCATION,
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
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        text = getattr(resp, "text", None) or ""
        if not text and getattr(resp, "candidates", None):
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = str(resp)
        if not text:
            raise RuntimeError("empty gemini response")
        return text

    return await asyncio.to_thread(_run)


__all__ = [
    "ChatResult",
    "chat",
    "extract_json",
    "health_info",
    "mock_reply",
    "ollama_model_id",
    "resolve_provider",
]
