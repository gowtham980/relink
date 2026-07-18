from unittest.mock import MagicMock, patch

import pytest

from relink_coach.providers.config import Settings
from relink_coach.providers.vertex import chat_vertex


@pytest.mark.asyncio
async def test_vertex_happy_path():
    settings = Settings(gcp_project="p", gemini_model="gemini-2.0-flash")

    fake_resp = MagicMock()
    fake_resp.text = "hello from vertex"
    fake_resp.candidates = None

    fake_models = MagicMock()
    fake_models.generate_content.return_value = fake_resp

    fake_client = MagicMock()
    fake_client.models = fake_models

    import google.genai as real_genai

    with patch.object(real_genai, "Client", return_value=fake_client):
        text = await chat_vertex(
            [
                {"role": "system", "content": "be helpful"},
                {"role": "user", "content": "hi"},
            ],
            settings=settings,
        )
        assert text == "hello from vertex"


@pytest.mark.asyncio
async def test_vertex_empty_raises():
    settings = Settings(gcp_project="p")
    fake_resp = MagicMock()
    fake_resp.text = ""
    fake_resp.candidates = []
    fake_models = MagicMock()
    fake_models.generate_content.return_value = fake_resp
    fake_client = MagicMock()
    fake_client.models = fake_models

    import google.genai as real_genai

    with (
        patch.object(real_genai, "Client", return_value=fake_client),
        pytest.raises(RuntimeError, match="empty gemini"),
    ):
        await chat_vertex([{"role": "user", "content": "hi"}], settings=settings)
