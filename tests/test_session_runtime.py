from pathlib import Path

import pytest

from psychometric_v2.deployment import DeploymentMode, DeploymentSettings
from psychometric_v2.session_runtime import (
    GenerationLimitReached,
    generation_attempts,
    generation_remaining,
    repository_for_session,
    start_generation,
)


def settings(mode: DeploymentMode) -> DeploymentSettings:
    return DeploymentSettings(mode=mode, public_demo_generation_limit=3)


def test_public_demo_repository_reuses_one_session_and_isolates_another(
    tmp_path: Path,
) -> None:
    first: dict[str, object] = {}
    second: dict[str, object] = {}

    first_repository = repository_for_session(
        first,
        settings(DeploymentMode.PUBLIC_DEMO),
        tmp_path,
    )
    rerun_repository = repository_for_session(
        first,
        settings(DeploymentMode.PUBLIC_DEMO),
        tmp_path,
    )
    second_repository = repository_for_session(
        second,
        settings(DeploymentMode.PUBLIC_DEMO),
        tmp_path,
    )

    assert first_repository.root == rerun_repository.root
    assert first_repository.root != second_repository.root
    assert first_repository.root != (tmp_path / "v2" / "projects").resolve()
    assert first_repository.load("adolescent-big-five-demo")
    assert second_repository.load("adolescent-big-five-demo")


def test_public_demo_repository_keeps_session_mutations_private(
    tmp_path: Path,
) -> None:
    first: dict[str, object] = {}
    second: dict[str, object] = {}
    configured = settings(DeploymentMode.PUBLIC_DEMO)
    first_repository = repository_for_session(first, configured, tmp_path)
    second_repository = repository_for_session(second, configured, tmp_path)
    first_project = first_repository.load("adolescent-big-five-demo")
    first_repository.save(first_project.validated_update(selected_item_id=None))

    assert first_repository.load(first_project.config.project_id).selected_item_id is None
    assert second_repository.load(first_project.config.project_id).selected_item_id is not None


def test_research_repository_uses_durable_workspace(tmp_path: Path) -> None:
    repository = repository_for_session(
        {},
        settings(DeploymentMode.RESEARCH),
        tmp_path,
    )

    assert repository.root == (tmp_path / "v2" / "projects").resolve()
    assert repository.load("adolescent-big-five-demo")


def test_generation_budget_counts_starts_and_blocks_fourth() -> None:
    state: dict[str, object] = {}
    configured = settings(DeploymentMode.PUBLIC_DEMO)

    for expected in (1, 2, 3):
        start_generation(state, configured)
        assert generation_attempts(state) == expected
        assert generation_remaining(state, configured) == 3 - expected

    with pytest.raises(GenerationLimitReached):
        start_generation(state, configured)
    assert generation_attempts(state) == 3


def test_research_mode_has_no_generation_budget() -> None:
    state: dict[str, object] = {}
    configured = settings(DeploymentMode.RESEARCH)

    for _ in range(5):
        start_generation(state, configured)

    assert generation_attempts(state) == 5
    assert generation_remaining(state, configured) is None
