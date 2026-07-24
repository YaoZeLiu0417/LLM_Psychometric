from __future__ import annotations

import os
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class DeploymentMode(str, Enum):
    RESEARCH = "research"
    PUBLIC_DEMO = "public_demo"


class DeploymentSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: DeploymentMode = DeploymentMode.PUBLIC_DEMO
    public_demo_generation_limit: int = Field(default=3, ge=1)

    @classmethod
    def from_env(cls) -> "DeploymentSettings":
        raw_mode = os.getenv("WORKBENCH_DEPLOYMENT", "").strip() or "public_demo"
        raw_limit = os.getenv("PUBLIC_DEMO_GENERATION_LIMIT", "").strip() or "3"
        try:
            return cls(
                mode=raw_mode,
                public_demo_generation_limit=int(raw_limit),
            )
        except (TypeError, ValueError, ValidationError):
            raise ValueError("Workbench deployment configuration is invalid.") from None
