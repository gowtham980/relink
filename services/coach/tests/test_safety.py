from relink_coach.safety import classify_safety


def test_crisis_blocked():
    r = classify_safety("I want to kill myself")
    assert r.blocked is True
    assert r.kind == "crisis"
    assert r.resources
    assert any("iasp" in (x.get("url") or "").lower() for x in r.resources)


def test_crisis_variants():
    for text in (
        "thinking about suicide",
        "I want to end my life",
        "I want to die tonight",
        "planning self-harm",
        "I might hurt myself",
        "no reason to live anymore",
    ):
        r = classify_safety(text)
        assert r.blocked is True, text
        assert r.kind == "crisis"


def test_normal_ok():
    r = classify_safety("I scrolled too much last night")
    assert r.blocked is False
    assert r.kind is None


def test_empty_and_none():
    assert classify_safety("").blocked is False
    assert classify_safety(None).blocked is False  # type: ignore[arg-type]


def test_medical_blocked():
    r = classify_safety("How do I go cold turkey off alcohol at home?")
    assert r.blocked is True
    assert r.kind == "medical"


def test_medical_benzo():
    r = classify_safety("I want to go cold turkey from xanax")
    assert r.blocked is True
    assert r.kind == "medical"


def test_non_crisis_kill_word_alone_not_enough():
    # "kill" without self-harm phrase should not trip crisis patterns
    r = classify_safety("I want to kill my bad habit of scrolling")
    assert r.blocked is False
