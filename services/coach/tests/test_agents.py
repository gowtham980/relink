import os

import pytest

os.environ["RELINK_LLM_PROVIDER"] = "mock"

from relink_coach import agents


@pytest.mark.asyncio
async def test_profile_has_disclaimer():
    data = await agents.profile_habit({"habitType": "nicotine", "values": ["health"]})
    assert data.get("disclaimer")
    assert data.get("provider_used") == "mock"


@pytest.mark.asyncio
async def test_urge_safety_short_circuit():
    data = await agents.urge_turn({"message": "I want to end my life", "step": 0})
    assert data["blocked"] is True
    assert data["provider_used"] == "safety"
    assert "reply" not in data or data["reply"]


@pytest.mark.asyncio
async def test_plans_structure():
    data = await agents.generate_plans({"context": {}})
    assert "plans" in data
    assert isinstance(data["plans"], list)
    assert data["plans"]


@pytest.mark.asyncio
async def test_nudge_short():
    data = await agents.nudge_compose({"values": ["presence"]})
    assert data.get("nudge")
    assert len(data["nudge"]) < 500


@pytest.mark.asyncio
async def test_coach_accepts_workflow_context():
    data = await agents.coach_turn(
        {
            "message": "What should I focus on tonight?",
            "profile": {"habit": "scroll", "values": ["focus"]},
            "recentCheckIns": [{"urgeLevel": 8, "mood": 2, "slipped": False}],
            "activePlans": [{"ifCue": "phone in bed", "thenAction": "plug across room"}],
            "lastSlip": {"context": "late night alone", "next24h": "walk"},
        }
    )
    assert data.get("blocked") is False
    assert data.get("reply")
    assert data.get("disclaimer")


@pytest.mark.asyncio
async def test_urge_accepts_active_plans():
    data = await agents.urge_turn(
        {
            "message": "urge is strong",
            "step": 0,
            "activePlans": [{"ifCue": "unlock phone", "thenAction": "open Relink"}],
        }
    )
    assert data.get("blocked") is False
    assert data.get("reply")
