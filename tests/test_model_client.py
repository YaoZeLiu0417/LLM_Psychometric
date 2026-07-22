import json
from types import SimpleNamespace

import pytest

from psychometric_v2.config import LiveModelConfig
from psychometric_v2.model_client import (
    ModelOutputError,
    ModelTimeout,
    ModelUnavailable,
    OpenAICompatibleClient,
)


class FakeCompletions:
    def __init__(self, result: object = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


def fake_sdk(
    content: object = '{"answer": "ok"}', *, error: Exception | None = None
) -> tuple[SimpleNamespace, FakeCompletions]:
    completions = FakeCompletions(
        result=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        ),
        error=error,
    )
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def config(**changes: object) -> LiveModelConfig:
    values: dict[str, object] = {
        "api_key": "top-secret-key",
        "model_id": "fake-model",
        "base_url": None,
        "timeout_seconds": 45.0,
    }
    values.update(changes)
    return LiveModelConfig(**values)


def test_from_env_requires_key_and_model_without_disclosing_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    with pytest.raises(ModelUnavailable) as captured:
        LiveModelConfig.from_env()

    assert "OPENAI_API_KEY" in str(captured.value)
    assert "LLM_MODEL" in str(captured.value)
    assert "top-secret" not in str(captured.value)


def test_from_env_prefers_openai_base_url_and_defaults_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://preferred.invalid/v1")
    monkeypatch.setenv("OPENAI_API_BASE", "https://legacy.invalid/v1")
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)

    loaded = LiveModelConfig.from_env()

    assert loaded.base_url == "https://preferred.invalid/v1"
    assert loaded.timeout_seconds == 45.0
    assert loaded.model_id == "model-a"


def test_from_env_falls_back_to_legacy_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_BASE", "https://legacy.invalid/v1")

    assert LiveModelConfig.from_env().base_url == "https://legacy.invalid/v1"


def test_complete_json_uses_the_constrained_request_contract() -> None:
    sdk, completions = fake_sdk('{"answer": "ok"}')
    client = OpenAICompatibleClient(config(timeout_seconds=12), client=sdk)

    assert client.complete_json("system text", "user text") == {"answer": "ok"}
    assert completions.calls == [
        {
            "model": "fake-model",
            "messages": [
                {"role": "system", "content": "system text"},
                {"role": "user", "content": "user text"},
            ],
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
            "timeout": 12.0,
        }
    ]


def test_complete_json_converts_timeout_to_public_error() -> None:
    sdk, _ = fake_sdk(error=TimeoutError("top-secret-key leaked upstream"))
    client = OpenAICompatibleClient(config(), client=sdk)

    with pytest.raises(ModelTimeout) as captured:
        client.complete_json("system", "user")

    assert "top-secret-key" not in str(captured.value)


@pytest.mark.parametrize(
    "content",
    ["not-json top-secret-key", "[]", "null", "", "   "],
    ids=["invalid", "array", "null", "empty", "whitespace"],
)
def test_complete_json_rejects_invalid_empty_or_non_object_content(
    content: str,
) -> None:
    sdk, _ = fake_sdk(content)
    client = OpenAICompatibleClient(config(), client=sdk)

    with pytest.raises(ModelOutputError) as captured:
        client.complete_json("system", "user")

    assert "top-secret-key" not in str(captured.value)
    if content:
        assert content not in str(captured.value)


def test_complete_json_rejects_malformed_response_without_raw_details() -> None:
    sdk = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions(result=SimpleNamespace()))
    )
    client = OpenAICompatibleClient(config(), client=sdk)

    with pytest.raises(ModelOutputError) as captured:
        client.complete_json("system", "user")

    assert "choices" not in str(captured.value)


def test_complete_json_converts_sdk_failure_without_secret_leakage() -> None:
    sdk, _ = fake_sdk(error=RuntimeError("request had top-secret-key"))
    client = OpenAICompatibleClient(config(), client=sdk)

    with pytest.raises(ModelUnavailable) as captured:
        client.complete_json("system", "user")

    assert str(captured.value) == "Model service is currently unavailable."
    assert json.dumps(captured.value.args) == '["Model service is currently unavailable."]'


def test_complete_json_resanitizes_public_error_raised_by_sdk() -> None:
    sdk, _ = fake_sdk(error=ModelUnavailable("top-secret-key from adapter"))
    client = OpenAICompatibleClient(config(), client=sdk)

    with pytest.raises(ModelUnavailable) as captured:
        client.complete_json("system", "user")

    assert str(captured.value) == "Model service is currently unavailable."
