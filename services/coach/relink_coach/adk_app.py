"""
Google ADK multi-agent graph for Relink.

When `google-adk` is installed, agents are defined with ADK LlmAgent + LiteLlm
(Ollama Cloud) and can be inspected/eval'd. Runtime invoke still goes through
relink_coach.agents + ModelRouter for FastAPI stability and Vertex fallback.

Install: pip install 'relink-coach[adk]'
"""

from __future__ import annotations

import os
from typing import Any

ADK_AVAILABLE = False
root_agent = None
AGENT_GRAPH: dict[str, Any] = {
    "name": "RelinkCoordinator",
    "description": "Safety-first habit coach: profile, plans, urge, slip, MI, insight, nudge",
    "sub_agents": [
        "SafetyGuard",
        "ProfilerAgent",
        "PlanLabAgent",
        "UrgeProtocolAgent",
        "SlipRecoveryAgent",
        "MiCoachAgent",
        "InsightAgent",
        "NudgeComposerAgent",
    ],
    "models": {
        "coach": os.getenv("RELINK_MODEL_COACH", "glm-5.2"),
        "struct": os.getenv("RELINK_MODEL_STRUCT", "kimi-k2.7-code"),
        "fallback": os.getenv("RELINK_GEMINI_MODEL", "gemini-2.0-flash"),
    },
    "routing": {
        "primary": "ollama_cloud",
        "fallback": "vertex_gemini",
        "safety": "pre_llm_rules",
    },
}


def build_adk_agents() -> Any:
    """Build ADK agent tree if google-adk + litellm available."""
    global ADK_AVAILABLE, root_agent
    try:
        from google.adk.agents import Agent, SequentialAgent
        from google.adk.models.lite_llm import LiteLlm
    except Exception:
        ADK_AVAILABLE = False
        root_agent = None
        return None

    api_base = os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1")
    api_key = os.getenv("OLLAMA_API_KEY", "")
    def _bare(m: str) -> str:
        m = (m or "").strip()
        return m.split("/", 1)[1] if "/" in m else m

    coach_bare = _bare(os.getenv("RELINK_MODEL_COACH", "glm-5.2"))
    struct_bare = _bare(os.getenv("RELINK_MODEL_STRUCT", "kimi-k2.7-code"))
    # LiteLLM needs openai/ prefix for OpenAI-compatible Ollama Cloud
    coach_model = f"openai/{coach_bare}"
    struct_model = f"openai/{struct_bare}"

    def _llm(model: str) -> Any:
        return LiteLlm(model=model, api_base=api_base, api_key=api_key or "unused")

    profiler = Agent(
        name="ProfilerAgent",
        model=_llm(struct_model),
        description="Onboarding profiler: triggers, values, if-then seeds as JSON",
        instruction=(
            "You are Relink Profiler. Return ONLY JSON: stageOfChange, triggers, "
            "riskWindows, identity, suggestedPlans[{ifCue,thenAction}]. No medical claims."
        ),
    )
    plan_lab = Agent(
        name="PlanLabAgent",
        model=_llm(struct_model),
        description="Implementation intention co-author",
        instruction=(
            'Return ONLY JSON {"plans":[{"ifCue":"...","thenAction":"..."}]} three plans. '
            "Concrete, non-shaming."
        ),
    )
    urge = Agent(
        name="UrgeProtocolAgent",
        model=_llm(coach_model),
        description="Urge surfing SOS protocol",
        instruction=(
            "MODE URGE SOS. Short calm guidance: name → rate 0-10 → surf → if-then → substitute. "
            "Never shame. Not therapy."
        ),
    )
    slip = Agent(
        name="SlipRecoveryAgent",
        model=_llm(coach_model),
        description="Shame-free slip recovery",
        instruction=(
            "Lapse ≠ relapse. Map trigger, next-24h plan. No identity attack. Wellness only."
        ),
    )
    mi = Agent(
        name="MiCoachAgent",
        model=_llm(coach_model),
        description="Motivational interviewing coach",
        instruction=(
            "Use MI: open questions, reflections, elicit change talk. No lectures. Not medical care."
        ),
    )
    insight = Agent(
        name="InsightAgent",
        model=_llm(struct_model),
        description="Weekly pattern insight JSON",
        instruction=(
            "Return ONLY JSON: summary, patterns[], suggestedPlanEdits[]. Supportive tone."
        ),
    )
    nudge = Agent(
        name="NudgeComposerAgent",
        model=_llm(coach_model),
        description="Short values-based nudge",
        instruction="Max 2 sentences, non-shaming, values-based nudge.",
    )

    # Sequential demo path for ADK web/eval: profile → plan
    onboard_flow = SequentialAgent(
        name="OnboardFlow",
        sub_agents=[profiler, plan_lab],
    )

    root_agent = Agent(
        name="RelinkCoordinator",
        model=_llm(coach_model),
        description=AGENT_GRAPH["description"],
        instruction=(
            "You coordinate Relink habit-change support. Prefer specialized sub-agents. "
            "Never give medical dosing or crisis counseling — redirect to human help."
        ),
        sub_agents=[onboard_flow, urge, slip, mi, insight, nudge],
    )
    ADK_AVAILABLE = True
    return root_agent


# Build on import if possible (optional)
try:
    build_adk_agents()
except Exception:
    ADK_AVAILABLE = False
    root_agent = None


def graph_info() -> dict[str, Any]:
    return {
        **AGENT_GRAPH,
        "adk_loaded": ADK_AVAILABLE,
        "root_agent": getattr(root_agent, "name", None) if root_agent else None,
    }
