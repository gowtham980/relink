from unittest.mock import AsyncMock, patch

import pytest

from relink_coach.providers.config import Settings
from relink_coach.providers.router import chat, classify_error, health_info, resolve_provider


def test_resolve_mock():
    assert resolve_provider(Settings(provider="mock")) == "mock"


def test_resolve_ollama_with_key():
    assert resolve_provider(Settings(provider="ollama", api_key="k")) == "ollama"


def test_resolve_ollama_no_key_falls_mock():
    assert resolve_provider(Settings(provider="ollama", api_key="", allow_mock_fallback=True)) == "mock"


def test_resolve_ollama_no_key_strict():
    assert resolve_provider(Settings(provider="ollama", api_key="", allow_mock_fallback=False)) == "ollama"


def test_health_bare_ids():
    info = health_info(Settings(model_coach="openai/glm-5.2", model_struct="kimi-k2.7-code"))
    assert info["model_coach"] == "glm-5.2"
    assert info["model_struct"] == "kimi-k2.7-code"


def test_classify_error():
    assert classify_error(Exception("401 unauthorized")) == "auth"
    assert classify_error(Exception("timeout waiting")) == "timeout"
    assert classify_error(Exception("status=503")) == "upstream"


@pytest.mark.asyncio
async def test_chat_mock():
    r = await chat(
        [{"role": "system", "content": "MODE:URGE"}, {"role": "user", "content": "hi"}],
        settings=Settings(provider="mock"),
    )
    assert r.provider_used == "mock"
    assert r.text


@pytest.mark.asyncio
async def test_chat_ollama_success():
    s = Settings(provider="ollama", api_key="k", fallback="none", allow_mock_fallback=True)
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(return_value="from ollama"),
    ):
        r = await chat([{"role": "user", "content": "x"}], settings=s)
    assert r.provider_used == "ollama"
    assert r.text == "from ollama"
    assert r.fallback is False


@pytest.mark.asyncio
async def test_chat_ollama_to_mock_fallback():
    s = Settings(provider="ollama", api_key="k", fallback="none", allow_mock_fallback=True)
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        r = await chat(
            [{"role": "system", "content": "MODE:NUDGE"}, {"role": "user", "content": "v"}],
            settings=s,
        )
    assert r.provider_used == "mock"
    assert r.fallback is True
    assert r.fallback_reason == "timeout"


@pytest.mark.asyncio
async def test_chat_ollama_to_vertex_fallback():
    s = Settings(
        provider="ollama",
        api_key="k",
        fallback="vertex",
        allow_mock_fallback=False,
        gcp_project="proj",
    )
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ), patch(
        "relink_coach.providers.router.chat_vertex",
        new=AsyncMock(return_value="from gemini"),
    ):
        r = await chat([{"role": "user", "content": "x"}], settings=s)
    assert r.provider_used == "gemini"
    assert r.fallback is True
    assert r.text == "from gemini"


@pytest.mark.asyncio
async def test_chat_strict_raises():
    s = Settings(provider="ollama", api_key="k", fallback="none", allow_mock_fallback=False)
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await chat([{"role": "user", "content": "x"}], settings=s)
