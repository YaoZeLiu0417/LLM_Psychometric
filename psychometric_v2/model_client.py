from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from psychometric_v2.config import (
    LiveModelConfig,
    ModelError,
    ModelOutputError,
    ModelTimeout,
    ModelUnavailable,
)


_UNAVAILABLE_MESSAGE = "Model service is currently unavailable."
_TIMEOUT_MESSAGE = "Model request timed out."
_OUTPUT_MESSAGE = "Model returned an invalid structured response."


class OpenAICompatibleClient:
    def __init__(self, config: LiveModelConfig, client: Any | None = None) -> None:
        self.config = config
        self._client = client

    @property
    def model_id(self) -> str:
        return self.config.model_id

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI

            kwargs: dict[str, object] = {
                "api_key": self.config.api_key.get_secret_value(),
                "timeout": self.config.timeout_seconds,
            }
            if self.config.base_url is not None:
                kwargs["base_url"] = self.config.base_url
            self._client = OpenAI(**kwargs)
        except Exception:
            raise ModelUnavailable(_UNAVAILABLE_MESSAGE) from None
        return self._client

    @staticmethod
    def _is_timeout(error: BaseException) -> bool:
        if isinstance(error, TimeoutError):
            return True
        return type(error).__name__ in {
            "APITimeoutError",
            "ConnectTimeout",
            "ReadTimeout",
            "WriteTimeout",
            "PoolTimeout",
        }

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        try:
            response = self._get_client().chat.completions.create(
                model=self.config.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.35,
                response_format={"type": "json_object"},
                timeout=self.config.timeout_seconds,
            )
        except ModelTimeout:
            raise ModelTimeout(_TIMEOUT_MESSAGE) from None
        except ModelOutputError:
            raise ModelOutputError(_OUTPUT_MESSAGE) from None
        except ModelUnavailable:
            raise ModelUnavailable(_UNAVAILABLE_MESSAGE) from None
        except Exception as exc:
            if self._is_timeout(exc):
                raise ModelTimeout(_TIMEOUT_MESSAGE) from None
            raise ModelUnavailable(_UNAVAILABLE_MESSAGE) from None

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError):
            raise ModelOutputError(_OUTPUT_MESSAGE) from None
        if not isinstance(content, str) or not content.strip():
            raise ModelOutputError(_OUTPUT_MESSAGE)

        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            raise ModelOutputError(_OUTPUT_MESSAGE) from None
        if not isinstance(parsed, Mapping):
            raise ModelOutputError(_OUTPUT_MESSAGE)
        return dict(parsed)


__all__ = [
    "ModelError",
    "ModelOutputError",
    "ModelTimeout",
    "ModelUnavailable",
    "OpenAICompatibleClient",
]
