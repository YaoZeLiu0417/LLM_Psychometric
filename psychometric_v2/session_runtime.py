from __future__ import annotations

import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.deployment import DeploymentMode, DeploymentSettings
from psychometric_v2.repository import JsonProjectRepository


_TEMP_DIRECTORY_KEY = "v2_public_demo_temp_directory"
_REPOSITORY_ROOT_KEY = "v2_public_demo_repository_root"
_GENERATION_ATTEMPTS_KEY = "v2_generation_attempts"


class GenerationLimitReached(PermissionError):
    pass


def repository_for_session(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
    workspace_root: Path,
) -> JsonProjectRepository:
    if settings.mode is DeploymentMode.RESEARCH:
        repository = JsonProjectRepository(workspace_root / "v2" / "projects")
        repository.ensure_seed(build_demo_project())
        return repository

    temporary = state.get(_TEMP_DIRECTORY_KEY)
    root_text = state.get(_REPOSITORY_ROOT_KEY)
    if not isinstance(temporary, tempfile.TemporaryDirectory) or not isinstance(
        root_text,
        str,
    ):
        temporary = tempfile.TemporaryDirectory(prefix="psychometric-public-demo-")
        root = Path(temporary.name) / "projects"
        state[_TEMP_DIRECTORY_KEY] = temporary
        state[_REPOSITORY_ROOT_KEY] = str(root)
    else:
        root = Path(root_text)

    repository = JsonProjectRepository(root)
    repository.ensure_seed(build_demo_project())
    return repository


def generation_attempts(state: MutableMapping[str, Any]) -> int:
    value = state.get(_GENERATION_ATTEMPTS_KEY, 0)
    return value if isinstance(value, int) and value >= 0 else 0


def generation_remaining(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
) -> int | None:
    if settings.mode is DeploymentMode.RESEARCH:
        return None
    return max(
        settings.public_demo_generation_limit - generation_attempts(state),
        0,
    )


def start_generation(
    state: MutableMapping[str, Any],
    settings: DeploymentSettings,
) -> None:
    remaining = generation_remaining(state, settings)
    if remaining is not None and remaining <= 0:
        raise GenerationLimitReached(
            "The generation limit for this session has been reached."
        )
    state[_GENERATION_ATTEMPTS_KEY] = generation_attempts(state) + 1
