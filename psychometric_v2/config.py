from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ASSET = ROOT / "psychometric_v2" / "assets" / "data" / "bfi2_anchors.json"
FONT_ASSET = (
    ROOT
    / "psychometric_v2"
    / "assets"
    / "fonts"
    / "SourceSans3-VariableFont_wght.ttf"
)
WORKSPACE_ROOT = ROOT / "workspace_data"

load_dotenv(ROOT / ".env", override=False)


class ModelError(RuntimeError):
    """Base class for errors that are safe to show in the UI."""


class ModelUnavailable(ModelError):
    pass


class ModelTimeout(ModelUnavailable):
    pass


class ModelOutputError(ModelError):
    pass


class LiveModelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    api_key: SecretStr
    model_id: str
    base_url: str | None = None
    timeout_seconds: float = Field(default=45.0, gt=0)

    @property
    def model(self) -> str:
        return self.model_id

    @property
    def timeout(self) -> float:
        return self.timeout_seconds

    @classmethod
    def from_env(cls) -> "LiveModelConfig":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model_id = os.getenv("LLM_MODEL", "").strip()
        missing = [
            name
            for name, value in (
                ("OPENAI_API_KEY", api_key),
                ("LLM_MODEL", model_id),
            )
            if not value
        ]
        if missing:
            names = " and ".join(missing)
            raise ModelUnavailable(f"Required model configuration is missing: {names}.")

        preferred_base = os.getenv("OPENAI_BASE_URL", "").strip()
        legacy_base = os.getenv("OPENAI_API_BASE", "").strip()
        timeout_text = (
            os.getenv("LLM_TIMEOUT_SECONDS", "").strip()
            or os.getenv("OPENAI_TIMEOUT", "").strip()
        )
        try:
            timeout_seconds = float(timeout_text) if timeout_text else 45.0
            return cls(
                api_key=api_key,
                model_id=model_id,
                base_url=preferred_base or legacy_base or None,
                timeout_seconds=timeout_seconds,
            )
        except (TypeError, ValueError):
            raise ModelUnavailable("Model configuration is invalid.") from None
