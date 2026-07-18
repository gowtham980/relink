from unittest.mock import AsyncMock, patch

import pytest

from relink_coach.providers.config import Settings
from relink_coach.providers.router import chat
from relink_coach import agents
from relink_coach.providers.types import ChatResult


@pytest.mark.asyncio
async def test_ollama_success_path():
    s = Settings(provider="ollama", api_key="test-key", fallback="none")
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(return_value="hello from ollama"),
    ):
        r = await chat(
            [{"role": "system", "content": "MODE:URGE"}, {"role": "user", "content": "hi"}],
            role="coach",
            settings=s,
        )
    assert r.provider_used == "ollama"
    assert r.text == "hello from ollama"
    assert r.fallback is False


@pytest.mark.asyncio
async def test_ollama_fails_to_mock():
    s = Settings(provider="ollama", api_key="test-key", fallback="none", allow_mock_fallback=True)
    with patch(
        "relink_coach.providers.router.chat_ollama",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        r = await chat(
            [{"role": "system", "content": "MODE:NUDGE"}, {"role": "user", "content": "v"}],
            role="coach",
            settings=s,
        )
    assert r.provider_used == "mock"
    assert r.fallback is True
    assert r.fallback_reason == "timeout"


@pytest.mark.asyncio
async def test_agents_json_fallback_paths():
    with patch(
        "relink_coach.agents.chat",
        new=AsyncMock(
            return_value=ChatResult(text="not-json{{{", provider_used="mock", model="mock")
        ),
    ):
        data = await agents.generate_plans({})
        assert "plans" in data
        data2 = await agents.profile_habit({})
        assert "stageOfChange" in data2 or "suggestedPlans" in data2
