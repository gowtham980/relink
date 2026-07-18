import os
from unittest.mock import AsyncMock, patch

import pytest

# Force ollama path with key present
os.environ["RELINK_LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_API_KEY"] = "test-key-not-real"
os.environ["RELINK_LLM_FALLBACK"] = "none"
os.environ["RELINK_ALLOW_MOCK_FALLBACK"] = "1"


@pytest.mark.asyncio
async def test_ollama_success_path():
    import relink_coach.llm as llm

    llm.PROVIDER = "ollama"
    llm.API_KEY = "test-key"
    llm.FALLBACK = "none"
    llm.ALLOW_MOCK_FALLBACK = True

    with patch.object(llm, "_chat_ollama", new=AsyncMock(return_value="hello from ollama")):
        r = await llm.chat(
            [{"role": "system", "content": "MODE:URGE"}, {"role": "user", "content": "hi"}],
            role="coach",
        )
    assert r.provider_used == "ollama"
    assert r.text == "hello from ollama"
    assert r.fallback is False


@pytest.mark.asyncio
async def test_ollama_fails_to_mock():
    import relink_coach.llm as llm

    llm.PROVIDER = "ollama"
    llm.API_KEY = "test-key"
    llm.FALLBACK = "none"
    llm.ALLOW_MOCK_FALLBACK = True

    with patch.object(llm, "_chat_ollama", new=AsyncMock(side_effect=RuntimeError("timeout"))):
        r = await llm.chat(
            [{"role": "system", "content": "MODE:NUDGE"}, {"role": "user", "content": "v"}],
            role="coach",
        )
    assert r.provider_used == "mock"
    assert r.fallback is True
    assert r.fallback_reason == "timeout"


@pytest.mark.asyncio
async def test_ollama_http_post():
    import relink_coach.llm as llm
    from relink_coach.http_client import shutdown_http, startup_http

    llm.PROVIDER = "ollama"
    llm.API_KEY = "k"
    llm.API_BASE = "https://example.invalid/v1"

    class FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    class FakeClient:
        is_closed = False

        async def post(self, *a, **k):
            return FakeResp()

        async def aclose(self):
            self.is_closed = True

    await startup_http()
    with patch("relink_coach.llm.get_http_client", return_value=FakeClient()):
        text = await llm._chat_ollama(
            [{"role": "user", "content": "x"}],
            role="coach",
            temperature=0.5,
            max_tokens=100,
        )
    assert text == "ok"
    await shutdown_http()


@pytest.mark.asyncio
async def test_ollama_reasoning_only_raises():
    import relink_coach.llm as llm

    llm.API_KEY = "k"

    class FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "", "reasoning": "think..."}}]}

    class FakeClient:
        is_closed = False

        async def post(self, *a, **k):
            return FakeResp()

    with patch("relink_coach.llm.get_http_client", return_value=FakeClient()):
        with pytest.raises(RuntimeError, match="reasoning-only"):
            await llm._chat_ollama(
                [{"role": "user", "content": "x"}],
                role="coach",
                temperature=0.5,
                max_tokens=50,
            )


@pytest.mark.asyncio
async def test_agents_json_fallback_paths():
    os.environ["RELINK_LLM_PROVIDER"] = "mock"
    import relink_coach.llm as llm
    from relink_coach import agents

    llm.PROVIDER = "mock"

    with patch.object(
        llm,
        "chat",
        new=AsyncMock(
            return_value=llm.ChatResult(text="not-json{{{", provider_used="mock", model="mock")
        ),
    ):
        # re-import agents uses chat from llm module at import time - patch agents.chat
        with patch("relink_coach.agents.chat", new=AsyncMock(
            return_value=llm.ChatResult(text="not-json{{{", provider_used="mock", model="mock")
        )):
            data = await agents.generate_plans({})
            assert "plans" in data
            data2 = await agents.profile_habit({})
            assert "stageOfChange" in data2 or "suggestedPlans" in data2
