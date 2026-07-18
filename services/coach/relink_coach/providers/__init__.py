"""LLM providers: Ollama Cloud primary, Vertex Gemini fallback, mock."""

from .config import Settings, get_settings
from .router import chat, health_info, ollama_model_id, resolve_provider
from .types import ChatResult

__all__ = [
    "ChatResult",
    "Settings",
    "chat",
    "get_settings",
    "health_info",
    "ollama_model_id",
    "resolve_provider",
]
