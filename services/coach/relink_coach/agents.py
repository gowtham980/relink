"""Multi-agent protocols (ADK-style orchestration without hard ADK dependency)."""

from __future__ import annotations

from typing import Any

from .llm import chat, extract_json
from .safety import SafetyResult, classify_safety

DISCLAIMER = (
    "Relink is a wellness support tool, not medical care or therapy. "
    "For clinical concerns, seek a licensed professional."
)


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
    raw = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        data = extract_json(raw)
    except Exception:
        data = extract_json(
            await chat(
                [
                    {"role": "system", "content": system + "\nJSON only."},
                    {"role": "user", "content": user},
                ],
                role="struct",
            )
        )
    data["disclaimer"] = DISCLAIMER
    return data


async def generate_plans(payload: dict[str, Any]) -> dict[str, Any]:
    context = payload.get("context", {})
    system = (
        "MODE:PLAN\nYou are Relink Plan Lab. Return ONLY JSON: "
        '{"plans":[{"ifCue":"...","thenAction":"..."}]} — three implementation intentions. '
        "Concrete, specific, non-shaming. No medical dosing."
    )
    user = f"Profile context: {context}"
    raw = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        return extract_json(raw)
    except Exception:
        return {
            "plans": [
                {
                    "ifCue": "I feel the urge to open the habit app",
                    "thenAction": "I open Relink Urge SOS and rate the urge first",
                }
            ]
        }


async def urge_turn(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message", "")
    step = payload.get("step", 0)
    history = payload.get("history", [])
    safety = await run_safety(message)
    if safety.blocked:
        return {
            "blocked": True,
            "mode": "safety",
            "reply": safety.message,
            "resources": safety.resources,
            "disclaimer": DISCLAIMER,
        }
    system = (
        "MODE:URGE\nYou run Relink Urge SOS (urge surfing). Short, calm, 3-6 sentences. "
        f"Protocol step index: {step}. Guide: name urge → rate 0-10 → breathe/surf → if-then → substitute. "
        "Never shame. Not therapy. No medical advice."
    )
    msgs = [{"role": "system", "content": system}]
    for h in history[-6:]:
        msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": message or "I'm having an urge right now."})
    reply = await chat(msgs, role="coach")
    return {
        "blocked": False,
        "mode": "urge",
        "reply": reply,
        "nextStep": min(step + 1, 4),
        "disclaimer": DISCLAIMER,
    }


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
        }
    system = (
        "MODE:SLIP\nYou run Relink Slip Recovery. Normalize lapse ≠ relapse. "
        "Help map trigger, update high-risk situation, build next-24h plan. No shame, no identity attack."
    )
    reply = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": message or "I slipped and I feel bad."},
        ],
        role="coach",
    )
    return {"blocked": False, "mode": "slip", "reply": reply, "disclaimer": DISCLAIMER}


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
        }
    system = (
        f"MODE:MI\nYou are Relink adaptive coach using motivational interviewing. "
        f"User mode hint: {mode}. Profile: {profile}. "
        "Elicit change talk, reflect, no lectures. Wellness tool only."
    )
    msgs = [{"role": "system", "content": system}]
    for h in history[-8:]:
        msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": message})
    reply = await chat(msgs, role="coach")
    return {"blocked": False, "mode": "mi", "reply": reply, "disclaimer": DISCLAIMER}


async def insight_generate(payload: dict[str, Any]) -> dict[str, Any]:
    checkins = payload.get("checkIns", [])
    slips = payload.get("slips", [])
    system = (
        "MODE:INSIGHT\nReturn ONLY JSON: summary (string), patterns (string[]), "
        "suggestedPlanEdits (string[]). Supportive, non-shaming pattern insight."
    )
    user = f"Check-ins: {checkins[-14:]}. Slips: {slips[-5:]}"
    raw = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        role="struct",
    )
    try:
        data = extract_json(raw)
    except Exception:
        data = {
            "summary": "Keep logging — patterns appear after a few check-ins.",
            "patterns": [],
            "suggestedPlanEdits": [],
        }
    data["disclaimer"] = DISCLAIMER
    return data


async def nudge_compose(payload: dict[str, Any]) -> dict[str, Any]:
    values = payload.get("values", [])
    system = "MODE:NUDGE\nOne short non-shaming nudge (max 2 sentences). Values-based."
    reply = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Values: {values}"},
        ],
        role="coach",
        max_tokens=120,
    )
    return {"nudge": reply.strip(), "disclaimer": DISCLAIMER}
