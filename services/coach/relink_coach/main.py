"""FastAPI entry — Relink coach service."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import agents
from .llm import MODEL_COACH, MODEL_STRUCT, resolve_provider

load_dotenv()

app = FastAPI(title="Relink Coach", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvokeBody(BaseModel):
    action: str = Field(..., description="profile|plans|urge|slip|coach|insight|nudge")
    payload: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "provider": resolve_provider(),
        "model_coach": MODEL_COACH,
        "model_struct": MODEL_STRUCT,
    }


@app.post("/v1/invoke")
async def invoke(body: InvokeBody) -> dict[str, Any]:
    action = body.action.lower().strip()
    handlers = {
        "profile": agents.profile_habit,
        "plans": agents.generate_plans,
        "urge": agents.urge_turn,
        "slip": agents.slip_turn,
        "coach": agents.coach_turn,
        "insight": agents.insight_generate,
        "nudge": agents.nudge_compose,
    }
    fn = handlers.get(action)
    if not fn:
        raise HTTPException(400, f"Unknown action: {action}")
    # soft rate: payload size
    if len(str(body.payload)) > 50_000:
        raise HTTPException(413, "Payload too large")
    return await fn(body.payload)


def run() -> None:
    import uvicorn

    port = int(os.getenv("COACH_PORT", "8787"))
    uvicorn.run("relink_coach.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
