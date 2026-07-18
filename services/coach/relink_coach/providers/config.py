from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _strip_provider_prefix(model: str) -> str:
    m = (model or "").strip()
    if "/" in m:
        return m.split("/", 1)[1]
    return m


@dataclass(frozen=True)
class Settings:
    provider: str = "mock"
    api_base: str = "https://ollama.com/v1"
    api_key: str = ""
    model_coach: str = "glm-5.2"
    model_struct: str = "kimi-k2.7-code"
    fallback: str = "vertex"
    gemini_model: str = "gemini-2.0-flash"
    gcp_project: str = ""
    gcp_location: str = "us-central1"
    allow_mock_fallback: bool = True
    ollama_timeout: float = 45.0

    def coach_model_id(self) -> str:
        return _strip_provider_prefix(self.model_coach)

    def struct_model_id(self) -> str:
        return _strip_provider_prefix(self.model_struct)

    def model_for(self, role: str) -> str:
        return self.struct_model_id() if role == "struct" else self.coach_model_id()

    def vertex_ready(self) -> bool:
        return (
            bool(self.gcp_project)
            or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            or bool(os.getenv("K_SERVICE"))
        )


def load_settings() -> Settings:
    return Settings(
        provider=os.getenv("RELINK_LLM_PROVIDER", "mock").lower(),
        api_base=os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1").rstrip("/"),
        api_key=os.getenv("OLLAMA_API_KEY", ""),
        model_coach=os.getenv("RELINK_MODEL_COACH", "glm-5.2"),
        model_struct=os.getenv("RELINK_MODEL_STRUCT", "kimi-k2.7-code"),
        fallback=os.getenv("RELINK_LLM_FALLBACK", "vertex").lower(),
        gemini_model=os.getenv("RELINK_GEMINI_MODEL", "gemini-2.0-flash"),
        gcp_project=os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "")),
        gcp_location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        allow_mock_fallback=os.getenv("RELINK_ALLOW_MOCK_FALLBACK", "1") == "1",
        ollama_timeout=float(os.getenv("RELINK_OLLAMA_TIMEOUT", "45")),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
