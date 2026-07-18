from relink_coach.safety import classify_safety


def test_crisis_blocked():
    r = classify_safety("I want to kill myself")
    assert r.blocked is True
    assert r.kind == "crisis"
    assert r.resources


def test_normal_ok():
    r = classify_safety("I scrolled too much last night")
    assert r.blocked is False


def test_medical_blocked():
    r = classify_safety("How do I go cold turkey off alcohol at home?")
    assert r.blocked is True
    assert r.kind == "medical"
