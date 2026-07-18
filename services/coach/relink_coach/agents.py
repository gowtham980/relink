"""Multi-agent protocols with SafetyGuard-first + ModelRouter (Ollama/Vertex/mock)."""

from __future__ import annotations

from typing import Any

from .llm import ChatResult, chat, extract_json
from .safety import SafetyResult, classify_safety

DISCLAIMER = (
    "Relink is a wellness support tool, not medical care or therapy. "
    "For clinical concerns, seek a licensed professional."
)


def _attach_llm_meta(data: dict[str, Any], result: ChatResult) -> dict[str, Any]:
    data["provider_used"] = result.provider_used
    data["fallback"] = result.fallback
    if result.fallback_reason:
        data["fallback_reason"] = result.fallback_reason
    if result.model:
        data["model"] = result.model
    data["disclaimer"] = DISCLAIMER
    return data


async def run_safety(user_text: str) -> SafetyResult:
    return classify_safety(user_text)


async def profile_habit(payload: dict[str, Any]) -> dict[str, Any]:
    habit = payload.get("habitType", "screen_time")
    notes = payload.get("notes", "")
    values = payload.get("values", [])
    system = (
        "MODE:PROFILE\nYou are Relink Profiler. Return ONLY JSON with keys: "
        "stageOfChange, triggers, riskWindows, identity, suggestedPlans "
        "(array of {ifCue, thenAction}). No medical claims. Supportive tone."
    )
    user = f"Habit: {habit}. Values: {values}. Notes: {notes}"
    result = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        data = extract_json(result.text)
    except Exception:
        result = await chat(
            [
                {"role": "system", "content": system + "\nJSON only."},
                {"role": "user", "content": user},
            ],
            role="struct",
        )
        data = extract_json(result.text)
    return _attach_llm_meta(data, result)


async def generate_plans(payload: dict[str, Any]) -> dict[str, Any]:
    context = payload.get("context", {})
    system = (
        "MODE:PLAN\nYou are Relink Plan Lab. Return ONLY JSON: "
        '{"plans":[{"ifCue":"...","thenAction":"..."}]} — three implementation intentions. '
        "Concrete, specific, non-shaming. No medical dosing."
    )
    user = f"Profile context: {context}"
    result = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        data = extract_json(result.text)
    except Exception:
        data = {
            "plans": [
                {
                    "ifCue": "I feel the urge to open the habit app",
                    "thenAction": "I open Relink Urge SOS and rate the urge first",
                }
            ]
        }
    return _attach_llm_meta(data, result)


async def urge_turn(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message", "")
    step = int(payload.get("step", 0) or 0)
    history = payload.get("history", [])
    safety = await run_safety(message)
    if safety.blocked:
        return {
            "blocked": True,
            "mode": "safety",
            "reply": safety.message,
            "resources": safety.resources,
            "disclaimer": DISCLAIMER,
            "provider_used": "safety",
            "fallback": False,
        }
    system = (
        "MODE:URGE\nYou run Relink Urge SOS (urge surfing). Short, calm, 3-6 sentences. "
        f"Protocol step index: {step}. Guide: name urge → rate 0-10 → breathe/surf → if-then → substitute. "
        "Never shame. Not therapy. No medical advice."
    )
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for h in history[-6:]:
        msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": message or "I'm having an urge right now."})
    result = await chat(msgs, role="coach")
    return _attach_llm_meta(
        {
            "blocked": False,
            "mode": "urge",
            "reply": result.text,
            "nextStep": min(step + 1, 4),
        },
        result,
    )


async def slip_turn(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message", "")
    safety = await run_safety(message)
    if safety.blocked:
        return {
            "blocked": True,
            "mode": "safety",
            "reply": safety.message,
            "resources": safety.resources,
            "disclaimer": DISCLAIMER,
            "provider_used": "safety",
            "fallback": False,
        }
    system = (
        "MODE:SLIP\nYou run Relink Slip Recovery. Normalize lapse ≠ relapse. "
        "Help map trigger, update high-risk situation, build next-24h plan. No shame, no identity attack."
    )
    result = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": message or "I slipped and I feel bad."},
        ],
        role="coach",
    )
    return _attach_llm_meta(
        {"blocked": False, "mode": "slip", "reply": result.text},
        result,
    )


async def coach_turn(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message", "")
    mode = payload.get("mode", "mi")
    history = payload.get("history", [])
    profile = payload.get("profile", {})
    safety = await run_safety(message)
    if safety.blocked:
        return {
            "blocked": True,
            "mode": "safety",
            "reply": safety.message,
            "resources": safety.resources,
            "disclaimer": DISCLAIMER,
            "provider_used": "safety",
            "fallback": False,
        }
    system = (
        f"MODE:MI\nYou are Relink adaptive coach using motivational interviewing. "
        f"User mode hint: {mode}. Profile: {profile}. "
        "Elicit change talk, reflect, no lectures. Wellness tool only."
    )
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for h in history[-8:]:
        msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": message})
    result = await chat(msgs, role="coach")
    return _attach_llm_meta(
        {"blocked": False, "mode": "mi", "reply": result.text},
        result,
    )


async def insight_generate(payload: dict[str, Any]) -> dict[str, Any]:
    checkins = payload.get("checkIns", [])
    slips = payload.get("slips", [])
    system = (
        "MODE:INSIGHT\nReturn ONLY JSON: summary (string), patterns (string[]), "
        "suggestedPlanEdits (string[]). Supportive, non-shaming pattern insight."
    )
    user = f"Check-ins: {checkins[-14:]}. Slips: {slips[-5:]}"
    result = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        data = extract_json(result.text)
    except Exception:
        data = {
            "summary": "Keep logging — patterns appear after a few check-ins.",
            "patterns": [],
            "suggestedPlanEdits": [],
        }
    return _attach_llm_meta(data, result)


async def nudge_compose(payload: dict[str, Any]) -> dict[str, Any]:
    values = payload.get("values", [])
    system = "MODE:NUDGE\nOne short non-shaming nudge (max 2 sentences). Values-based."
    result = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Values: {values}"},
        ],
        role="coach",
        max_tokens=120,
    )
    return _attach_llm_meta({"nudge": result.text.strip()}, result)
