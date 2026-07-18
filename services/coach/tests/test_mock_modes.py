import json

from relink_coach.mock_replies import mock_reply


def test_profile_mode_not_confused_with_plans_word():
    text = mock_reply(
        [
            {
                "role": "system",
                "content": "MODE:PROFILE\nReturn suggestedPlans array",
            },
            {"role": "user", "content": "scroll"},
        ],
        role="struct",
    )
    data = json.loads(text)
    assert "stageOfChange" in data
    assert "suggestedPlans" in data


def test_insight_mode():
    text = mock_reply(
        [
            {
                "role": "system",
                "content": "MODE:INSIGHT\nReturn suggestedPlanEdits",
            },
            {"role": "user", "content": "data"},
        ],
        role="struct",
    )
    data = json.loads(text)
    assert "summary" in data
