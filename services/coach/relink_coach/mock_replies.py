"""Deterministic mock replies for CI and offline fallback."""

from __future__ import annotations

import json


def mock_reply(messages: list[dict[str, str]], *, role: str = "coach") -> str:
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    mode = _detect_mode(system, role)

    if mode == "profile":
        return json.dumps(profile_fallback())
    if mode == "plan":
        return json.dumps(plans_fallback())
    if mode == "urge":
        return (
            "You're in Urge SOS. Name the urge without fighting it — notice "
            "where it sits in your body. Rate it 0–10. Breathe slowly for 90 seconds; "
            "urges rise and fall like a wave. When it drops even one point, do your "
            "if-then: plug the phone away or leave the room. "
            "You already voted for who you're becoming by opening Relink."
        )
    if mode == "slip":
        return (
            "A slip is data, not identity. What happened right before? "
            "Update your high-risk map. For the next 24 hours: one small plan, "
            "one check-in, one person or place that supports you. "
            "You practiced recovery — that counts."
        )
    if mode == "insight":
        return json.dumps(insight_fallback())
    if mode == "nudge":
        return "You said mornings matter. One small vote now: delay the scroll by two minutes."

    snippet = user[:120] if user else "your habit"
    return (
        f"Thanks for showing up. About “{snippet}…” — what matters most to you "
        "about changing this? I'm here to draw out your own reasons, not lecture. "
        "What's one step that feels doable today?"
    )


def _detect_mode(system: str, role: str) -> str:
    # Explicit MODE tags first (avoid matching "plan" inside suggestedPlans / PlanEdits)
    for tag, mode in (
        ("MODE:PROFILE", "profile"),
        ("MODE:PLAN", "plan"),
        ("MODE:INSIGHT", "insight"),
        ("MODE:URGE", "urge"),
        ("MODE:SLIP", "slip"),
        ("MODE:NUDGE", "nudge"),
        ("MODE:MI", "coach"),
    ):
        if tag in system:
            return mode
    lower = system.lower()
    if "urge" in lower[:80]:
        return "urge"
    if role == "struct" and "implementation intention" in lower:
        return "plan"
    return "coach"


def profile_fallback() -> dict:
    return {
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


def plans_fallback() -> dict:
    return {
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


def insight_fallback() -> dict:
    return {
        "summary": "Harder evenings cluster after lonely or unstructured nights.",
        "patterns": [
            "Urges peak 21:00–23:00",
            "Check-ins with urge≥7 often follow skipped daytime movement",
        ],
        "suggestedPlanEdits": [
            "Add: If it is 20:30 and I am alone, then I message a friend or start a 15-minute walk."
        ],
    }
