import asyncio
import os

os.environ.setdefault("RELINK_LLM_PROVIDER", "mock")

from relink_coach.llm import chat, health_info, ollama_model_id, resolve_provider, _strip_provider_prefix
from relink_coach.providers.config import Settings, clear_settings_cache
from relink_coach.safety import classify_safety


def test_chat_mock_returns_meta():
    clear_settings_cache()
    r = asyncio.run(
        chat(
            [
                {"role": "system", "content": "MODE:URGE"},
                {"role": "user", "content": "help"},
            ],
            role="coach",
            settings=Settings(provider="mock"),
        )
    )
    assert r.text
    assert r.provider_used == "mock"
    assert len(r.text) > 10


def test_struct_mock_profile_json():
    r = asyncio.run(
        chat(
            [
                {"role": "system", "content": "MODE:PROFILE"},
                {"role": "user", "content": "screen time"},
            ],
            role="struct",
            settings=Settings(provider="mock"),
        )
    )
    assert "stageOfChange" in r.text or "suggestedPlans" in r.text


def test_safety_before_llm():
    assert classify_safety("I want to kill myself").blocked is True


def test_health_bare_model_ids():
    info = health_info(Settings(model_coach="glm-5.2", model_struct="kimi-k2.7-code"))
    assert "/" not in info["model_coach"]
    assert ollama_model_id("coach", Settings())
    assert resolve_provider(Settings(provider="mock")) == "mock"


def test_strip_openai_prefix():
    assert _strip_provider_prefix("openai/glm-5.2") == "glm-5.2"
    assert _strip_provider_prefix("glm-5.2") == "glm-5.2"
