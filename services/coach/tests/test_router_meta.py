import asyncio

from relink_coach.llm import chat
from relink_coach.safety import classify_safety


def test_chat_mock_returns_meta():
    r = asyncio.run(
        chat(
            [
                {"role": "system", "content": "MODE:URGE"},
                {"role": "user", "content": "help"},
            ],
            role="coach",
        )
    )
    assert r.text
    assert r.provider_used in ("mock", "ollama", "gemini")
    assert len(r.text) > 10


def test_safety_before_llm():
    assert classify_safety("I want to kill myself").blocked is True
