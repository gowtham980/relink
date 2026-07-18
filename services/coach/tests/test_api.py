import os

os.environ["RELINK_LLM_PROVIDER"] = "mock"
os.environ["RELINK_ALLOW_MOCK_FALLBACK"] = "1"

from fastapi.testclient import TestClient

from relink_coach.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "model_coach" in data
    assert "agents" in data
    assert data.get("version")


def test_agents_graph():
    r = client.get("/v1/agents")
    assert r.status_code == 200
    data = r.json()
    assert "modes" in data or "agents" in data or isinstance(data, dict)


def test_unknown_action():
    r = client.post("/v1/invoke", json={"action": "nope", "payload": {}})
    assert r.status_code == 400


def test_payload_too_large():
    r = client.post(
        "/v1/invoke",
        json={"action": "urge", "payload": {"message": "x" * 60_000}},
    )
    assert r.status_code == 413


def test_urge_ok():
    r = client.post(
        "/v1/invoke",
        json={"action": "urge", "payload": {"message": "urge is strong", "step": 0}},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("blocked") is False
    assert data.get("reply")
    assert data.get("disclaimer")
    assert data.get("provider_used") in ("mock", "ollama", "gemini", "safety")


def test_urge_crisis_blocks_without_llm_content():
    r = client.post(
        "/v1/invoke",
        json={"action": "urge", "payload": {"message": "I want to kill myself"}},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["blocked"] is True
    assert data["provider_used"] == "safety"
    assert data.get("resources")


def test_coach_ok():
    r = client.post(
        "/v1/invoke",
        json={"action": "coach", "payload": {"message": "Why is change hard?"}},
    )
    assert r.status_code == 200
    assert r.json().get("reply")
    assert r.json().get("disclaimer")


def test_slip_ok():
    r = client.post(
        "/v1/invoke",
        json={"action": "slip", "payload": {"message": "I slipped last night"}},
    )
    assert r.status_code == 200
    assert r.json()["mode"] in ("slip", "safety")


def test_profile_ok():
    r = client.post(
        "/v1/invoke",
        json={
            "action": "profile",
            "payload": {"habitType": "social_media", "values": ["focus"], "notes": ""},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "stageOfChange" in data or "suggestedPlans" in data
    assert data.get("disclaimer")


def test_plans_ok():
    r = client.post(
        "/v1/invoke",
        json={"action": "plans", "payload": {"context": {"habit": "scroll"}}},
    )
    assert r.status_code == 200
    assert "plans" in r.json()


def test_insight_ok():
    r = client.post(
        "/v1/invoke",
        json={
            "action": "insight",
            "payload": {
                "checkIns": [{"date": "2026-07-01", "urgeLevel": 7}],
                "slips": [],
            },
        },
    )
    assert r.status_code == 200
    assert "summary" in r.json()


def test_nudge_ok():
    r = client.post(
        "/v1/invoke",
        json={"action": "nudge", "payload": {"values": ["family"]}},
    )
    assert r.status_code == 200
    assert r.json().get("nudge")


def test_medical_safety_on_coach():
    r = client.post(
        "/v1/invoke",
        json={
            "action": "coach",
            "payload": {"message": "How do I go cold turkey off alcohol tonight?"},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["blocked"] is True
    assert data["provider_used"] == "safety"
