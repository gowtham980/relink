"""LLM client: Ollama Cloud (OpenAI-compat) or mock."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

PROVIDER = os.getenv("RELINK_LLM_PROVIDER", "mock").lower()
API_BASE = os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1").rstrip("/")
API_KEY = os.getenv("OLLAMA_API_KEY", "")
MODEL_COACH = os.getenv("RELINK_MODEL_COACH", "openai/glm-5.2")
MODEL_STRUCT = os.getenv("RELINK_MODEL_STRUCT", "openai/kimi-k2.7-code")


def _strip_provider_prefix(model: str) -> str:
    # LiteLLM-style openai/glm-5.2 → glm-5.2 for OpenAI-compat cloud API
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def resolve_provider() -> str:
    if PROVIDER == "ollama" and API_KEY:
        return "ollama"
    if PROVIDER == "ollama" and not API_KEY:
        return "mock"
    return PROVIDER if PROVIDER in ("mock", "ollama") else "mock"


async def chat(
    messages: list[dict[str, str]],
    *,
    role: str = "coach",
    temperature: float = 0.6,
    max_tokens: int = 800,
) -> str:
    provider = resolve_provider()
    if provider == "mock":
        return mock_reply(messages, role=role)

    model = _strip_provider_prefix(MODEL_STRUCT if role == "struct" else MODEL_COACH)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = f"{API_BASE}/chat/completions"
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


def mock_reply(messages: list[dict[str, str]], *, role: str = "coach") -> str:
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    mode = "coach"
    if "MODE:URGE" in system or "urge" in system.lower()[:80]:
        mode = "urge"
    if "MODE:SLIP" in system:
        mode = "slip"
    if "MODE:PLAN" in system or role == "struct" and "plan" in system.lower():
        mode = "plan"
    if "MODE:PROFILE" in system:
        mode = "profile"
    if "MODE:INSIGHT" in system:
        mode = "insight"
    if "MODE:NUDGE" in system:
        mode = "nudge"

    if mode == "profile":
        return json.dumps(
            {
                "stageOfChange": "preparation",
                "triggers": ["boredom", "late night", "loneliness"],
                "riskWindows": ["21:00-24:00"],
                "identity": "Someone who protects their mornings",
                "suggestedPlans": [
                    {
                        "ifCue": "I unlock my phone in bed after 10pm",
                        "thenAction": "I plug it across the room and open Relink Urge SOS",
                    },
                    {
                        "ifCue": "I feel bored between tasks",
                        "thenAction": "I stand up, drink water, and set a 10-minute timer",
                    },
                    {
                        "ifCue": "I want to open social media",
                        "thenAction": "I open Relink check-in first and rate my urge 0-10",
                    },
                ],
            }
        )
    if mode == "plan":
        return json.dumps(
            {
                "plans": [
                    {
                        "ifCue": "I feel the urge to scroll",
                        "thenAction": "I name the urge, rate it, and wait 2 minutes before any app",
                    },
                    {
                        "ifCue": "Friends invite a high-risk setting",
                        "thenAction": "I suggest a lower-risk alternative and text my reason",
                    },
                    {
                        "ifCue": "I slip",
                        "thenAction": "I open Slip Recovery within 1 hour without self-blame",
                    },
                ]
            }
        )
    if mode == "urge":
        return (
            "You're in Urge SOS. Name the urge without fighting it — notice where it sits in your body. "
            "Rate it 0–10. Breathe slowly for 90 seconds; urges rise and fall like a wave. "
            "When it drops even one point, do your if-then: plug the phone away or leave the room. "
            "You already voted for who you're becoming by opening Relink."
        )
    if mode == "slip":
        return (
            "A slip is data, not identity. What happened right before? Update your high-risk map. "
            "For the next 24 hours: one small plan, one check-in, one person or place that supports you. "
            "You practiced recovery — that counts."
        )
    if mode == "insight":
        return json.dumps(
            {
                "summary": "Harder evenings cluster after lonely or unstructured nights.",
                "patterns": [
                    "Urges peak 21:00–23:00",
                    "Check-ins with urge≥7 often follow skipped daytime movement",
                ],
                "suggestedPlanEdits": [
                    "Add: If it is 20:30 and I am alone, then I message a friend or start a 15-minute walk."
                ],
            }
        )
    if mode == "nudge":
        return "You said mornings matter. One small vote now: delay the scroll by two minutes."

    # default MI coach
    snippet = user[:120] if user else "your habit"
    return (
        f"Thanks for showing up. About “{snippet}…” — what matters most to you about changing this? "
        "I'm here to draw out your own reasons, not lecture. What's one step that feels doable today?"
    )


def extract_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        raise
