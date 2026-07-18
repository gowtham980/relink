"""Back-compat shim — prefer relink_coach.providers."""

from __future__ import annotations

from .json_util import extract_json
from .mock_replies import mock_reply
from .providers.config import Settings, clear_settings_cache, get_settings, load_settings
from .providers.ollama import chat_ollama as _chat_ollama_impl
from .providers.router import (
    DEFAULT_TOKENS,
    chat,
    classify_error,
    health_info,
    ollama_model_id,
    resolve_provider,
)
from .providers.types import ChatResult
from .providers.vertex import chat_vertex as _chat_vertex_impl

# Legacy module-level aliases (tests / older imports)
PROVIDER = get_settings().provider
API_BASE = get_settings().api_base
API_KEY = get_settings().api_key
MODEL_COACH = get_settings().model_coach
MODEL_STRUCT = get_settings().model_struct
FALLBACK = get_settings().fallback
GEMINI_MODEL = get_settings().gemini_model
GCP_PROJECT = get_settings().gcp_project
GCP_LOCATION = get_settings().gcp_location
ALLOW_MOCK_FALLBACK = get_settings().allow_mock_fallback


def _strip_provider_prefix(model: str) -> str:
    m = (model or "").strip()
    if "/" in m:
        return m.split("/", 1)[1]
    return m


def _classify_error(e: Exception) -> str:
    return classify_error(e)


async def _chat_ollama(
    messages: list[dict[str, str]],
    *,
    role: str,
    temperature: float,
    max_tokens: int,
) -> str:
    return await _chat_ollama_impl(
        messages,
        settings=get_settings(),
        role=role,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def _chat_vertex(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    return await _chat_vertex_impl(
        messages,
        settings=get_settings(),
        temperature=temperature,
        max_tokens=max_tokens,
    )


__all__ = [
    "ALLOW_MOCK_FALLBACK",
    "API_BASE",
    "API_KEY",
    "ChatResult",
    "DEFAULT_TOKENS",
    "FALLBACK",
    "GCP_LOCATION",
    "GCP_PROJECT",
    "GEMINI_MODEL",
    "MODEL_COACH",
    "MODEL_STRUCT",
    "PROVIDER",
    "Settings",
    "chat",
    "clear_settings_cache",
    "extract_json",
    "get_settings",
    "health_info",
    "load_settings",
    "mock_reply",
    "ollama_model_id",
    "resolve_provider",
    "_chat_ollama",
    "_chat_vertex",
    "_classify_error",
    "_strip_provider_prefix",
]
