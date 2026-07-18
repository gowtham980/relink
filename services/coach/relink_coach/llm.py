"""ModelRouter: Ollama Cloud primary → Vertex Gemini fallback → mock."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from typing import Any

import httpx

logger = logging.getLogger("relink.llm")

PROVIDER = os.getenv("RELINK_LLM_PROVIDER", "mock").lower()
API_BASE = os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1").rstrip("/")
API_KEY = os.getenv("OLLAMA_API_KEY", "")
MODEL_COACH = os.getenv("RELINK_MODEL_COACH", "openai/glm-5.2")
MODEL_STRUCT = os.getenv("RELINK_MODEL_STRUCT", "openai/kimi-k2.7-code")
FALLBACK = os.getenv("RELINK_LLM_FALLBACK", "vertex").lower()  # vertex | none
GEMINI_MODEL = os.getenv("RELINK_GEMINI_MODEL", "gemini-2.0-flash")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", ""))
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ALLOW_MOCK_FALLBACK = os.getenv("RELINK_ALLOW_MOCK_FALLBACK", "1") == "1"


@dataclass
class ChatResult:
    text: str
    provider_used: str
    fallback: bool = False
    fallback_reason: str | None = None
    model: str | None = None

    def meta(self) -> dict[str, Any]:
        return asdict(self)


def _strip_provider_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def resolve_provider() -> str:
    if PROVIDER == "gemini":
        return "gemini" if _vertex_ready() else ("mock" if ALLOW_MOCK_FALLBACK else "gemini")
    if PROVIDER == "ollama":
        if API_KEY:
            return "ollama"
        return "mock" if ALLOW_MOCK_FALLBACK else "ollama"
    if PROVIDER == "mock":
        return "mock"
    return "mock"


def _vertex_ready() -> bool:
    return bool(GCP_PROJECT) or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
        "K_SERVICE"
    )  # Cloud Run


def health_info() -> dict[str, Any]:
    return {
        "ok": True,
        "provider": resolve_provider(),
        "fallback": FALLBACK if FALLBACK != "none" else None,
        "model_coach": MODEL_COACH,
        "model_struct": MODEL_STRUCT,
        "gemini_model": GEMINI_MODEL,
        "project": GCP_PROJECT or None,
        "location": GCP_LOCATION,
        "ollama_configured": bool(API_KEY),
        "adk": _adk_available(),
    }


def _adk_available() -> bool:
    try:
        import google.adk  # noqa: F401

        return True
    except Exception:
        return False


async def chat(
    messages: list[dict[str, str]],
    *,
    role: str = "coach",
    temperature: float = 0.6,
    max_tokens: int = 800,
) -> ChatResult:
    """Primary Ollama → Vertex Gemini fallback → optional mock."""
    primary = resolve_provider()

    if primary == "mock":
        return ChatResult(text=mock_reply(messages, role=role), provider_used="mock", model="mock")

    if primary == "gemini":
        try:
            text = await _chat_vertex(messages, temperature=temperature, max_tokens=max_tokens)
            return ChatResult(
                text=text, provider_used="gemini", model=GEMINI_MODEL, fallback=False
            )
        except Exception as e:
            logger.warning("Gemini primary failed: %s", e)
            if ALLOW_MOCK_FALLBACK:
                return ChatResult(
                    text=mock_reply(messages, role=role),
                    provider_used="mock",
                    fallback=True,
                    fallback_reason=str(e)[:200],
                    model="mock",
                )
            raise

    # primary ollama
    try:
        text = await _chat_ollama(
            messages, role=role, temperature=temperature, max_tokens=max_tokens
        )
        model = _strip_provider_prefix(MODEL_STRUCT if role == "struct" else MODEL_COACH)
        return ChatResult(text=text, provider_used="ollama", model=model, fallback=False)
    except Exception as e:
        reason = _classify_error(e)
        logger.warning("Ollama failed (%s): %s", reason, e)
        if FALLBACK == "vertex" and _vertex_ready():
            try:
                text = await _chat_vertex(
                    messages, temperature=temperature, max_tokens=max_tokens
                )
                return ChatResult(
                    text=text,
                    provider_used="gemini",
                    fallback=True,
                    fallback_reason=reason,
                    model=GEMINI_MODEL,
                )
            except Exception as ge:
                logger.warning("Vertex fallback failed: %s", ge)
                if ALLOW_MOCK_FALLBACK:
                    return ChatResult(
                        text=mock_reply(messages, role=role),
                        provider_used="mock",
                        fallback=True,
                        fallback_reason=f"ollama:{reason};vertex:{ge}"[:200],
                        model="mock",
                    )
                raise
        if ALLOW_MOCK_FALLBACK:
            return ChatResult(
                text=mock_reply(messages, role=role),
                provider_used="mock",
                fallback=True,
                fallback_reason=reason,
                model="mock",
            )
        raise


def _classify_error(e: Exception) -> str:
    s = str(e).lower()
    if "401" in s or "403" in s or "auth" in s:
        return "auth"
    if "429" in s or "quota" in s or "rate" in s:
        return "quota"
    if "timeout" in s:
        return "timeout"
    if "5" in s and "status" in s:
        return "upstream"
    return "upstream"


async def _chat_ollama(
    messages: list[dict[str, str]],
    *,
    role: str,
    temperature: float,
    max_tokens: int,
) -> str:
    if not API_KEY:
        raise RuntimeError("OLLAMA_API_KEY not set")
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
        if r.status_code >= 400:
            raise RuntimeError(f"ollama status={r.status_code} body={r.text[:300]}")
        data = r.json()
        return data["choices"][0]["message"]["content"]


async def _chat_vertex(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    """Vertex AI Gemini via google-genai (ADC on Cloud Run / local gcloud auth)."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise RuntimeError("google-genai not installed") from e

    project = GCP_PROJECT or None
    client_kwargs: dict[str, Any] = {}
    if project:
        client_kwargs = {
            "vertexai": True,
            "project": project,
            "location": GCP_LOCATION,
        }
    client = genai.Client(**client_kwargs)

    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    contents: list[Any] = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    if not contents:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text="Hello")])]

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction="\n".join(system_parts) if system_parts else None,
    )

    # google-genai is sync; run in thread to avoid blocking event loop badly
    import asyncio

    def _run() -> str:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        text = getattr(resp, "text", None) or ""
        if not text and getattr(resp, "candidates", None):
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = str(resp)
        if not text:
            raise RuntimeError("empty gemini response")
        return text

    return await asyncio.to_thread(_run)


def mock_reply(messages: list[dict[str, str]], *, role: str = "coach") -> str:
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    mode = "coach"
    if "MODE:URGE" in system or "urge" in system.lower()[:80]:
        mode = "urge"
    if "MODE:SLIP" in system:
        mode = "slip"
    if "MODE:PLAN" in system or (role == "struct" and "plan" in system.lower()):
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
