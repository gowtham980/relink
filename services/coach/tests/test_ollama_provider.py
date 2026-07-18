import pytest
import respx
from httpx import Response

from relink_coach.http_client import shutdown_http, startup_http
from relink_coach.providers.config import Settings
from relink_coach.providers.ollama import chat_ollama


@pytest.fixture
async def http_life():
    await startup_http()
    yield
    await shutdown_http()


@pytest.mark.asyncio
@respx.mock
async def test_ollama_content_ok(http_life):
    settings = Settings(
        provider="ollama",
        api_base="https://ollama.test/v1",
        api_key="k",
        model_coach="glm-5.2",
    )
    respx.post("https://ollama.test/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "ride the wave"}}]},
        )
    )
    text = await chat_ollama(
        [{"role": "user", "content": "urge"}],
        settings=settings,
        role="coach",
        max_tokens=100,
    )
    assert text == "ride the wave"


@pytest.mark.asyncio
@respx.mock
async def test_ollama_reasoning_only_raises(http_life):
    settings = Settings(api_base="https://ollama.test/v1", api_key="k")
    respx.post("https://ollama.test/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "", "reasoning": "think..."}}]},
        )
    )
    with pytest.raises(RuntimeError, match="reasoning-only"):
        await chat_ollama(
            [{"role": "user", "content": "x"}],
            settings=settings,
            max_tokens=50,
        )


@pytest.mark.asyncio
@respx.mock
async def test_ollama_http_error(http_life):
    settings = Settings(api_base="https://ollama.test/v1", api_key="k")
    respx.post("https://ollama.test/v1/chat/completions").mock(
        return_value=Response(503, text="busy")
    )
    with pytest.raises(RuntimeError, match="status=503"):
        await chat_ollama([{"role": "user", "content": "x"}], settings=settings)


@pytest.mark.asyncio
async def test_ollama_missing_key():
    settings = Settings(api_key="")
    with pytest.raises(RuntimeError, match="OLLAMA_API_KEY"):
        await chat_ollama([{"role": "user", "content": "x"}], settings=settings)
