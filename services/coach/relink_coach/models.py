"""Typed Pydantic response models for Relink coach actions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LlmMeta(BaseModel):
    provider_used: str
    fallback: bool = False
    fallback_reason: str | None = None
    model: str | None = None
    disclaimer: str


class PlanItem(BaseModel):
    ifCue: str
    thenAction: str


class ProfileResponse(LlmMeta):
    stageOfChange: str = "preparation"
    triggers: list[str] = Field(default_factory=list)
    riskWindows: list[str] = Field(default_factory=list)
    identity: str = "Someone rebuilding healthier patterns"
    suggestedPlans: list[PlanItem] = Field(default_factory=list)


class PlansResponse(LlmMeta):
    plans: list[PlanItem] = Field(default_factory=list)


class UrgeResponse(LlmMeta):
    blocked: bool = False
    mode: str = "urge"
    reply: str
    nextStep: int = 1


class SlipResponse(LlmMeta):
    blocked: bool = False
    mode: str = "slip"
    reply: str


class CoachResponse(LlmMeta):
    blocked: bool = False
    mode: str = "mi"
    reply: str


class InsightResponse(LlmMeta):
    summary: str = ""
    patterns: list[str] = Field(default_factory=list)
    suggestedPlanEdits: list[str] = Field(default_factory=list)


class NudgeResponse(LlmMeta):
    nudge: str


class SafetyResponse(BaseModel):
    blocked: bool = True
    mode: str = "safety"
    reply: str | None = None
    resources: list[dict[str, str]] = Field(default_factory=list)
    disclaimer: str
    provider_used: str = "safety"
    fallback: bool = False


InvokeResponse = (
    ProfileResponse
    | PlansResponse
    | UrgeResponse
    | SlipResponse
    | CoachResponse
    | InsightResponse
    | NudgeResponse
    | SafetyResponse
)
