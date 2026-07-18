"""FastAPI entry — Relink coach service (ADK graph + ModelRouter)."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import agents
from .adk_app import graph_info
from .http_client import shutdown_http, startup_http
from .llm import health_info

load_dotenv()


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "RELINK_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,"
        "https://relink-web-kuw4c4fivq-uc.a.run.app,"
        "https://relink-web-1035020186370.us-central1.run.app",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await startup_http()
    yield
    await shutdown_http()


app = FastAPI(
    title="Relink Coach",
    version="0.3.0",
    description="Multi-agent habit coach: Ollama Cloud primary, Vertex Gemini fallback, ADK graph",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class InvokeBody(BaseModel):
    action: str = Field(..., min_length=1, max_length=32, description="profile|plans|urge|slip|coach|insight|nudge")
    payload: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, Any]:
    info = health_info()
    info["agents"] = graph_info()
    info["version"] = "0.3.0"
    return info


@app.get("/v1/agents")
async def agents_graph() -> dict[str, Any]:
    return graph_info()


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
    if len(str(body.payload)) > 50_000:
        raise HTTPException(413, "Payload too large")
    return await fn(body.payload)


def run() -> None:
    import uvicorn

    port = int(os.getenv("COACH_PORT", "8787"))
    uvicorn.run("relink_coach.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
