import pytest

from relink_coach.json_util import extract_json


def test_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_fenced_embedded():
    text = 'Here you go:\n```json\n{"plans":[{"ifCue":"x","thenAction":"y"}]}\n```'
    data = extract_json(text)
    assert "plans" in data


def test_empty_raises():
    with pytest.raises(ValueError):
        extract_json("")


def test_invalid_raises():
    with pytest.raises(Exception):
        extract_json("not json at all")
