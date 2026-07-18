from __future__ import annotations

import logging

from ..mock_replies import mock_reply
from .config import Settings, get_settings
from .ollama import chat_ollama
from .types import ChatResult
from .vertex import chat_vertex

logger = logging.getLogger("relink.llm")

DEFAULT_TOKENS = {"coach": 2048, "struct": 2048, "nudge": 1024}


def resolve_provider(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    if s.provider == "gemini":
        return "gemini" if s.vertex_ready() else ("mock" if s.allow_mock_fallback else "gemini")
    if s.provider == "ollama":
        if s.api_key:
            return "ollama"
        return "mock" if s.allow_mock_fallback else "ollama"
    if s.provider == "mock":
        return "mock"
    return "mock"


def ollama_model_id(role: str = "coach", settings: Settings | None = None) -> str:
    s = settings or get_settings()
    return s.model_for(role)


def _adk_available() -> bool:
    try:
        import google.adk  # noqa: F401

        return True
    except Exception:
        return False


def health_info(settings: Settings | None = None) -> dict:
    s = settings or get_settings()
    return {
        "ok": True,
        "provider": resolve_provider(s),
        "fallback": s.fallback if s.fallback != "none" else None,
        "model_coach": s.coach_model_id(),
        "model_struct": s.struct_model_id(),
        "gemini_model": s.gemini_model,
        "project": s.gcp_project or None,
        "location": s.gcp_location,
        "ollama_configured": bool(s.api_key),
        "adk": _adk_available(),
        "ollama_timeout_s": s.ollama_timeout,
    }


def classify_error(e: Exception) -> str:
    s = str(e).lower()
    if "401" in s or "403" in s or "auth" in s:
        return "auth"
    if "429" in s or "quota" in s or "rate" in s:
        return "quota"
    if "timeout" in s:
        return "timeout"
    if "status=5" in s or "status 5" in s:
        return "upstream"
    return "upstream"


async def chat(
    messages: list[dict[str, str]],
    *,
    role: str = "coach",
    temperature: float = 0.6,
    max_tokens: int | None = None,
    settings: Settings | None = None,
) -> ChatResult:
    """Primary Ollama → Vertex Gemini fallback → optional mock."""
    s = settings or get_settings()
    if max_tokens is None:
        max_tokens = DEFAULT_TOKENS.get(role, 2048)
    primary = resolve_provider(s)

    if primary == "mock":
        return ChatResult(text=mock_reply(messages, role=role), provider_used="mock", model="mock")

    if primary == "gemini":
        try:
            text = await chat_vertex(
                messages, settings=s, temperature=temperature, max_tokens=max_tokens
            )
            return ChatResult(
                text=text, provider_used="gemini", model=s.gemini_model, fallback=False
            )
        except Exception as e:
            logger.warning("Gemini primary failed: %s", e)
            if s.allow_mock_fallback:
                return ChatResult(
                    text=mock_reply(messages, role=role),
                    provider_used="mock",
                    fallback=True,
                    fallback_reason=str(e)[:200],
                    model="mock",
                )
            raise

    try:
        text = await chat_ollama(
            messages,
            settings=s,
            role=role,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return ChatResult(
            text=text, provider_used="ollama", model=s.model_for(role), fallback=False
        )
    except Exception as e:
        reason = classify_error(e)
        logger.warning("Ollama failed (%s): %s", reason, e)
        if s.fallback == "vertex" and s.vertex_ready():
            try:
                text = await chat_vertex(
                    messages, settings=s, temperature=temperature, max_tokens=max_tokens
                )
                return ChatResult(
                    text=text,
                    provider_used="gemini",
                    fallback=True,
                    fallback_reason=reason,
                    model=s.gemini_model,
                )
            except Exception as ge:
                logger.warning("Vertex fallback failed: %s", ge)
                if s.allow_mock_fallback:
                    return ChatResult(
                        text=mock_reply(messages, role=role),
                        provider_used="mock",
                        fallback=True,
                        fallback_reason=f"ollama:{reason};vertex:{ge}"[:200],
                        model="mock",
                    )
                raise
        if s.allow_mock_fallback:
            return ChatResult(
                text=mock_reply(messages, role=role),
                provider_used="mock",
                fallback=True,
                fallback_reason=reason,
                model="mock",
            )
        raise
