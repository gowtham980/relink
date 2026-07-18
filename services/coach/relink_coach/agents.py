"""Multi-agent protocols with SafetyGuard-first + ModelRouter (Ollama/Vertex/mock)."""

from __future__ import annotations

from typing import Any

from .json_util import extract_json
from .llm import ChatResult, chat
from .mock_replies import insight_fallback, plans_fallback, profile_fallback
from .models import (
    CoachResponse,
    InsightResponse,
    LlmMeta,
    NudgeResponse,
    PlanItem,
    PlansResponse,
    ProfileResponse,
    SafetyResponse,
    SlipResponse,
    UrgeResponse,
)
from .safety import SafetyResult, classify_safety

DISCLAIMER = (
    "Relink is a wellness support tool, not medical care or therapy. "
    "For clinical concerns, seek a licensed professional."
)


def _llm_meta(result: ChatResult) -> LlmMeta:
    return LlmMeta(
        provider_used=result.provider_used,
        fallback=result.fallback,
        fallback_reason=result.fallback_reason,
        model=result.model,
        disclaimer=DISCLAIMER,
    )


def _safety_block(safety: SafetyResult) -> SafetyResponse:
    return SafetyResponse(
        blocked=True,
        mode="safety",
        reply=safety.message,
        resources=safety.resources,
        disclaimer=DISCLAIMER,
    )


async def run_safety(user_text: str) -> SafetyResult:
    """Classify user text for crisis or medical safety concerns."""
    return classify_safety(user_text)


async def profile_habit(payload: dict[str, Any]) -> ProfileResponse:
    """Generate a values/identity profile and initial if-then plans."""
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
        max_tokens=2048,
    )
    try:
        data = extract_json(result.text)
        plans_raw = data.get("suggestedPlans", []) if isinstance(data, dict) else []
        suggested = [
            PlanItem(ifCue=str(p.get("ifCue", "")), thenAction=str(p.get("thenAction", "")))
            for p in plans_raw
            if isinstance(p, dict)
        ]
    except Exception:
        data = profile_fallback()
        suggested = [PlanItem(**p) for p in data.get("suggestedPlans", [])]
    meta = _llm_meta(result)
    return ProfileResponse(
        stageOfChange=str(data.get("stageOfChange", "preparation")),
        triggers=[str(t) for t in data.get("triggers", [])],
        riskWindows=[str(t) for t in data.get("riskWindows", [])],
        identity=str(data.get("identity", "Someone rebuilding healthier patterns")),
        suggestedPlans=suggested,
        **meta.model_dump(),
    )


async def generate_plans(payload: dict[str, Any]) -> PlansResponse:
    """Generate implementation-intention plans from profile context."""
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
        max_tokens=2048,
    )
    try:
        data = extract_json(result.text)
        if not isinstance(data, dict) or "plans" not in data:
            data = plans_fallback()
    except Exception:
        data = plans_fallback()
    plans = [
        PlanItem(ifCue=str(p.get("ifCue", "")), thenAction=str(p.get("thenAction", "")))
        for p in data.get("plans", [])
        if isinstance(p, dict)
    ]
    meta = _llm_meta(result)
    return PlansResponse(plans=plans, **meta.model_dump())


async def urge_turn(payload: dict[str, Any]) -> UrgeResponse | SafetyResponse:
    """Run one turn of the Urge SOS protocol."""
    message = payload.get("message", "")
    step = int(payload.get("step", 0) or 0)
    history = payload.get("history", [])
    active_plans = payload.get("activePlans", [])
    safety = await run_safety(str(message))
    if safety.blocked:
        return _safety_block(safety)
    system = (
        "MODE:URGE\nYou run Relink Urge SOS (urge surfing). Short, calm, 3-6 sentences. "
        f"Protocol step index: {step}. "
        f"Guide: name urge → rate 0-10 → breathe/surf → if-then → substitute. "
        f"User's active if-then plans: {active_plans}. Prefer reminding them of their own plan. "
        "Never shame. Not therapy. No medical advice."
    )
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for h in history[-6:]:
        msgs.append({"role": str(h.get("role", "user")), "content": str(h.get("content", ""))})
    msgs.append({"role": "user", "content": message or "I'm having an urge right now."})
    result = await chat(msgs, role="coach", max_tokens=2048)
    meta = _llm_meta(result)
    return UrgeResponse(
        blocked=False,
        mode="urge",
        reply=result.text,
        nextStep=min(step + 1, 4),
        **meta.model_dump(),
    )


async def slip_turn(payload: dict[str, Any]) -> SlipResponse | SafetyResponse:
    """Run one turn of Slip Recovery."""
    message = payload.get("message", "")
    safety = await run_safety(str(message))
    if safety.blocked:
        return _safety_block(safety)
    system = (
        "MODE:SLIP\nYou run Relink Slip Recovery. Normalize lapse ≠ relapse. "
        "Help map trigger, update high-risk situation, build next-24h plan. "
        "No shame, no identity attack."
    )
    result = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": message or "I slipped and I feel bad."},
        ],
        role="coach",
        max_tokens=2048,
    )
    meta = _llm_meta(result)
    return SlipResponse(blocked=False, mode="slip", reply=result.text, **meta.model_dump())


async def coach_turn(payload: dict[str, Any]) -> CoachResponse | SafetyResponse:
    """Run one turn of the MI-style adaptive coach."""
    message = payload.get("message", "")
    mode = payload.get("mode", "mi")
    history = payload.get("history", [])
    profile = payload.get("profile", {})
    recent_checkins = payload.get("recentCheckIns", [])
    active_plans = payload.get("activePlans", [])
    last_slip = payload.get("lastSlip")
    safety = await run_safety(str(message))
    if safety.blocked:
        return _safety_block(safety)
    system = (
        f"MODE:MI\nYou are Relink adaptive coach using motivational interviewing. "
        f"User mode hint: {mode}. Profile: {profile}. "
        f"Recent check-ins: {recent_checkins}. "
        f"Active if-then plans: {active_plans}. "
        f"Last slip repair: {last_slip}. "
        "Reference their real data when relevant. Elicit change talk, reflect, no lectures. "
        "Wellness tool only."
    )
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for h in history[-8:]:
        msgs.append({"role": str(h.get("role", "user")), "content": str(h.get("content", ""))})
    msgs.append({"role": "user", "content": str(message)})
    result = await chat(msgs, role="coach", max_tokens=2048)
    meta = _llm_meta(result)
    return CoachResponse(blocked=False, mode="mi", reply=result.text, **meta.model_dump())


async def insight_generate(payload: dict[str, Any]) -> InsightResponse:
    """Generate a pattern insight from recent check-ins and slips."""
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
        max_tokens=2048,
    )
    try:
        data = extract_json(result.text)
        if not isinstance(data, dict):
            data = insight_fallback()
    except Exception:
        data = (
            insight_fallback()
            if checkins or slips
            else {
                "summary": "Keep logging — patterns appear after a few check-ins.",
                "patterns": [],
                "suggestedPlanEdits": [],
            }
        )
    meta = _llm_meta(result)
    return InsightResponse(
        summary=str(data.get("summary", "")),
        patterns=[str(p) for p in data.get("patterns", [])],
        suggestedPlanEdits=[str(p) for p in data.get("suggestedPlanEdits", [])],
        **meta.model_dump(),
    )


async def nudge_compose(payload: dict[str, Any]) -> NudgeResponse:
    """Compose a short values-based nudge."""
    values = payload.get("values", [])
    system = (
        "MODE:NUDGE\nOne short non-shaming nudge (max 2 sentences). "
        "Values-based. Final answer only."
    )
    result = await chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Values: {values}"},
        ],
        role="coach",
        max_tokens=1024,
    )
    meta = _llm_meta(result)
    return NudgeResponse(nudge=result.text.strip(), **meta.model_dump())
