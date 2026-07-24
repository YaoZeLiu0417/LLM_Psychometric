from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from threading import Lock, RLock
from typing import Any

from pydantic import ValidationError

from psychometric_v2.models import (
    CandidateItem,
    EvidenceStatus,
    GenerationMode,
    ResearchProject,
    ResponseOption,
    ReviewAction,
    ReviewVersion,
    utc_now_iso,
)
from psychometric_v2.quality import run_deterministic_checks


_PROJECT_LOCKS_GUARD = Lock()
_PROJECT_LOCKS: dict[str, RLock] = {}


class ReviewVersionConflict(ValueError):
    def __init__(self, expected_version: int, current_version: int) -> None:
        self.expected_version = expected_version
        self.current_version = current_version
        super().__init__(
            "review version conflict: "
            f"expected {expected_version}, current {current_version}"
        )


class MutationPermissionError(PermissionError):
    pass


def _project_lock(repository: Any, project_id: str) -> RLock:
    project_path = Path(repository.path_for(project_id)).resolve()
    lock_key = os.path.normcase(str(project_path))
    with _PROJECT_LOCKS_GUARD:
        return _PROJECT_LOCKS.setdefault(lock_key, RLock())


def _require_nonblank(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be blank")
    return value


def _clone_options(options: Iterable[Any]) -> tuple[ResponseOption, ...]:
    try:
        cloned = tuple(
            ResponseOption.model_validate(
                option.model_dump(mode="python")
                if isinstance(option, ResponseOption)
                else option
            )
            for option in options
        )
    except (TypeError, ValidationError, ValueError):
        raise ValueError("options are invalid") from None
    return cloned


class WorkbenchService:
    def __init__(
        self,
        repository: Any,
        *,
        mutation_authorized: bool = True,
    ) -> None:
        self.repository = repository
        self.mutation_authorized = mutation_authorized

    def _require_mutation_authorized(self) -> None:
        if not self.mutation_authorized:
            raise MutationPermissionError("Researcher Access is required.")

    @staticmethod
    def _validated_item_with_checks(
        values: dict[str, Any],
        previous: CandidateItem,
    ) -> CandidateItem:
        try:
            base = CandidateItem.model_validate({**values, "quality_checks": ()})
        except ValidationError:
            raise ValueError("options are invalid") from None
        deterministic_ids = {
            check.check_id for check in run_deterministic_checks(previous)
        }
        model_checks = tuple(
            check
            for check in previous.quality_checks
            if check.check_id not in deterministic_ids
        )
        deterministic = run_deterministic_checks(base)
        return CandidateItem.model_validate(
            {
                **base.model_dump(mode="python"),
                "quality_checks": (*deterministic, *model_checks),
            }
        )

    def review_item(
        self,
        project_id: str,
        item_id: str,
        edited_stem: str,
        edited_options: Iterable[ResponseOption | dict[str, object]],
        reviewer: str,
        action: ReviewAction | str,
        note: str,
        *,
        expected_version: int,
    ) -> ResearchProject:
        self._require_mutation_authorized()
        _require_nonblank("stem", edited_stem)
        _require_nonblank("reviewer", reviewer)
        _require_nonblank("note", note)
        try:
            review_action = ReviewAction(action)
        except (TypeError, ValueError):
            raise ValueError("action is invalid") from None

        with _project_lock(self.repository, project_id):
            project = self.repository.load(project_id)
            try:
                existing = project.items[item_id]
            except KeyError:
                raise KeyError(f"item not found: {item_id}") from None

            current_version = len(existing.review_versions)
            if expected_version != current_version:
                raise ReviewVersionConflict(expected_version, current_version)

            if (
                review_action is ReviewAction.PROMOTE_TO_PILOT
                and existing.evidence_status is not EvidenceStatus.HUMAN_REVIEWED
            ):
                raise ValueError(
                    "PROMOTE_TO_PILOT requires current HUMAN_REVIEWED status"
                )

            before_options = _clone_options(existing.options)
            after_options = _clone_options(edited_options)
            status = {
                ReviewAction.EDIT: EvidenceStatus.NEEDS_REVISION,
                ReviewAction.RETURN: EvidenceStatus.NEEDS_REVISION,
                ReviewAction.APPROVE: EvidenceStatus.HUMAN_REVIEWED,
                ReviewAction.PROMOTE_TO_PILOT: EvidenceStatus.PILOT_CANDIDATE,
            }[review_action]
            version = ReviewVersion(
                version=len(existing.review_versions) + 1,
                reviewer=reviewer,
                action=review_action,
                note=note,
                before_stem_zh=existing.stem_zh,
                before_options=before_options,
                after_stem_zh=edited_stem,
                after_options=_clone_options(after_options),
            )
            values = existing.model_dump(mode="python")
            values.update(
                stem_zh=edited_stem,
                options=after_options,
                evidence_status=status,
                review_versions=(*existing.review_versions, version),
            )
            reviewed = self._validated_item_with_checks(values, existing)
            updated = ResearchProject.model_validate(
                {
                    **project.model_dump(mode="python"),
                    "items": {**dict(project.items), item_id: reviewed},
                    "selected_item_id": item_id,
                    "updated_at": utc_now_iso(),
                }
            )
            self.repository.save(updated)
            return updated

    def save_generated_item(
        self,
        project_id: str,
        item: CandidateItem,
    ) -> ResearchProject:
        self._require_mutation_authorized()
        if not isinstance(item, CandidateItem):
            raise ValueError("item must be a validated CandidateItem")
        if item.generation_mode is not GenerationMode.LIVE:
            raise ValueError("generated item must use LIVE generation mode")
        with _project_lock(self.repository, project_id):
            project = self.repository.load(project_id)
            try:
                snapshot = CandidateItem.model_validate(
                    item.model_dump(mode="python")
                )
            except ValidationError:
                raise ValueError("item must be a validated CandidateItem") from None
            if snapshot.item_id in project.items:
                raise ValueError(f"item_id already exists: {snapshot.item_id}")
            items = {**dict(project.items), snapshot.item_id: snapshot}
            if any(key != value.item_id for key, value in items.items()):
                raise ValueError("item key must match item_id")
            updated = ResearchProject.model_validate(
                {
                    **project.model_dump(mode="python"),
                    "items": items,
                    "selected_item_id": snapshot.item_id,
                    "updated_at": utc_now_iso(),
                }
            )
            self.repository.save(updated)
            return updated
