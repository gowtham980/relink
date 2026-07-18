from relink_coach.llm import _classify_error, _strip_provider_prefix, ollama_model_id, resolve_provider
from relink_coach.providers.config import Settings


def test_classify_error_kinds():
    assert _classify_error(Exception("401 unauthorized")) == "auth"
    assert _classify_error(Exception("rate limit 429")) == "quota"
    assert _classify_error(Exception("timeout waiting")) == "timeout"
    assert _classify_error(Exception("status=503 upstream")) == "upstream"
    assert _classify_error(Exception("weird")) == "upstream"


def test_strip_and_model_id():
    assert _strip_provider_prefix("openai/kimi-k2.7-code") == "kimi-k2.7-code"
    assert ollama_model_id("struct", Settings(model_struct="kimi-k2.7-code"))
    assert resolve_provider(Settings(provider="mock")) == "mock"
