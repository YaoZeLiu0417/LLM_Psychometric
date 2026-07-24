from copy import deepcopy
from threading import Event, Thread

import pytest

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import (
    CandidateItem,
    CheckOutcome,
    CheckSeverity,
    EvidenceStatus,
    GenerationMetadata,
    GenerationMode,
    QualityCheck,
    ReviewAction,
)
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.workbench import (
    MutationPermissionError,
    ReviewVersionConflict,
    WorkbenchService,
)


def service_with_seed(tmp_path):
    repository = JsonProjectRepository(tmp_path / "projects")
    project = build_demo_project()
    repository.save(project)
    return WorkbenchService(repository), repository, project


def generation_metadata(
    item: CandidateItem,
    *,
    model_id: str = "fake-model",
) -> GenerationMetadata:
    return GenerationMetadata(
        model_id=model_id,
        prompt_version=item.prompt_version,
        constraint_snapshot={
            "domain_id": item.domain_id,
            "facet_id": item.facet_id,
            "anchor_ids": list(item.anchor_ids),
        },
    )


def review(
    service: WorkbenchService,
    project_id: str,
    item: CandidateItem,
    *,
    stem: str | None = None,
    options=None,
    reviewer: str = "reviewer-a",
    action: ReviewAction = ReviewAction.EDIT,
    note: str = "记录本次修改理由",
):
    return service.review_item(
        project_id,
        item.item_id,
        stem if stem is not None else item.stem_zh,
        item.options if options is None else options,
        reviewer,
        action,
        note,
        expected_version=len(item.review_versions),
    )


def test_edit_builds_immutable_independent_history_and_persists(tmp_path) -> None:
    service, repository, original_project = service_with_seed(tmp_path)
    original_item = next(iter(original_project.items.values()))
    original_dump = deepcopy(original_item.model_dump(mode="json"))

    updated_project = review(
        service,
        original_project.config.project_id,
        original_item,
        stem="社团活动中需要自由组队，你会怎样开始行动？",
    )

    updated = updated_project.items[original_item.item_id]
    version = updated.review_versions[0]
    assert original_item.model_dump(mode="json") == original_dump
    assert updated is not original_item
    assert updated.evidence_status is EvidenceStatus.NEEDS_REVISION
    assert version.version == 1
    assert version.before_stem_zh == original_item.stem_zh
    assert version.after_stem_zh == updated.stem_zh
    assert version.before_options is not version.after_options
    assert version.before_options[0] is not version.after_options[0]
    assert repository.load(original_project.config.project_id) == updated_project


def test_approve_uses_human_reviewed_without_validated_status(tmp_path) -> None:
    service, _, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))

    approved_project = review(
        service,
        project.config.project_id,
        item,
        action=ReviewAction.APPROVE,
        note="内容符合人工审核要求",
    )

    assert approved_project.items[item.item_id].evidence_status is EvidenceStatus.HUMAN_REVIEWED
    assert "VALIDATED" not in {status.value for status in EvidenceStatus}


def test_promotion_requires_current_human_reviewed_status(tmp_path) -> None:
    service, _, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))

    with pytest.raises(ValueError, match="HUMAN_REVIEWED"):
        review(
            service,
            project.config.project_id,
            item,
            action=ReviewAction.PROMOTE_TO_PILOT,
            note="尝试进入预测试",
        )

    approved = review(
        service,
        project.config.project_id,
        item,
        action=ReviewAction.APPROVE,
        note="人工审核通过",
    )
    reviewed_item = approved.items[item.item_id]
    promoted = review(
        service,
        project.config.project_id,
        reviewed_item,
        action=ReviewAction.PROMOTE_TO_PILOT,
        note="进入预测试候选",
    )

    assert promoted.items[item.item_id].evidence_status is EvidenceStatus.PILOT_CANDIDATE


def test_review_requires_nonblank_note_stem_and_reviewer(tmp_path) -> None:
    service, _, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))

    for field, values in (
        ("note", {"note": " "}),
        ("stem", {"stem": "\t"}),
        ("reviewer", {"reviewer": ""}),
    ):
        with pytest.raises(ValueError, match=field):
            review(service, project.config.project_id, item, **values)


def test_review_rejects_missing_project_item_and_invalid_options(tmp_path) -> None:
    service, _, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))

    with pytest.raises(FileNotFoundError, match="missing-project"):
        review(service, "missing-project", item)
    with pytest.raises(KeyError, match="missing-item"):
        service.review_item(
            project.config.project_id,
            "missing-item",
            item.stem_zh,
            item.options,
            "reviewer",
            ReviewAction.EDIT,
            "修改",
            expected_version=0,
        )
    with pytest.raises(ValueError, match="options"):
        review(
            service,
            project.config.project_id,
            item,
            options=item.options[:3],
        )


def test_review_raises_typed_version_conflict(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))
    review(
        service,
        project.config.project_id,
        item,
        stem="Externally persisted revision",
        note="external save",
    )

    with pytest.raises(ReviewVersionConflict) as caught:
        service.review_item(
            project.config.project_id,
            item.item_id,
            "Stale editor revision",
            item.options,
            "reviewer-b",
            ReviewAction.EDIT,
            "stale save",
            expected_version=0,
        )

    assert isinstance(caught.value, ValueError)
    assert caught.value.expected_version == 0
    assert caught.value.current_version == 1
    assert str(caught.value) == "review version conflict: expected 0, current 1"
    persisted = repository.load(project.config.project_id).items[item.item_id]
    assert len(persisted.review_versions) == 1
    assert persisted.review_versions[0].note == "external save"


def test_return_sets_needs_revision_and_versions_are_numbered(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))

    first_project = review(
        service,
        project.config.project_id,
        item,
        stem="第一次修改后的题干",
        action=ReviewAction.EDIT,
        note="第一次修改",
    )
    first = first_project.items[item.item_id]
    second_project = review(
        service,
        project.config.project_id,
        first,
        stem="第二次退回后的题干",
        action=ReviewAction.RETURN,
        note="仍需修改",
    )
    second = second_project.items[item.item_id]

    assert [version.version for version in second.review_versions] == [1, 2]
    assert second.review_versions[1].before_stem_zh == first.stem_zh
    assert second.review_versions[1].after_stem_zh == second.stem_zh
    assert second.evidence_status is EvidenceStatus.NEEDS_REVISION
    assert repository.load(project.config.project_id) == second_project


def test_review_rebuilds_deterministic_checks_and_preserves_model_checks(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)
    item = next(iter(project.items.values()))
    model_check = QualityCheck(
        check_id="MODEL_ECOLOGY",
        label="生态合理性",
        severity=CheckSeverity.WARNING,
        outcome=CheckOutcome.PASS,
        evidence="场景合理",
    )
    item_with_model_check = CandidateItem.model_validate(
        {
            **item.model_dump(mode="python"),
            "quality_checks": (*item.quality_checks, model_check),
            "generation_mode": GenerationMode.LIVE,
            "model_id": "fake-model",
            "generation_metadata": generation_metadata(item),
        }
    )
    project_with_model_check = project.validated_update(
        items={**dict(project.items), item.item_id: item_with_model_check}
    )
    repository.save(project_with_model_check)

    result = review(
        service,
        project.config.project_id,
        item_with_model_check,
        stem="保留模型检查并重跑确定性检查的题干",
    )
    updated = result.items[item.item_id]

    assert "MODEL_ECOLOGY" in {check.check_id for check in updated.quality_checks}
    assert "OPTION_COUNT" in {check.check_id for check in updated.quality_checks}
    assert updated.generation_mode is GenerationMode.LIVE
    assert updated.model_id == "fake-model"


def test_save_generated_item_adds_selects_validated_snapshot_and_persists(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)
    source = next(iter(project.items.values()))
    generated = CandidateItem.model_validate(
        {
            **source.model_dump(mode="python"),
            "item_id": "live-sociability-test123",
            "generation_mode": GenerationMode.LIVE,
            "model_id": "fake-model",
            "generation_metadata": generation_metadata(source),
        }
    )

    saved = service.save_generated_item(project.config.project_id, generated)

    assert saved.selected_item_id == generated.item_id
    assert saved.items[generated.item_id] == generated
    assert repository.load(project.config.project_id) == saved


def test_save_generated_item_rejects_existing_id_without_losing_review_history(
    tmp_path,
) -> None:
    service, repository, project = service_with_seed(tmp_path)
    source = next(iter(project.items.values()))
    reviewed_project = review(
        service,
        project.config.project_id,
        source,
        stem="已经完成一次人工修改的题干",
    )
    reviewed = reviewed_project.items[source.item_id]
    colliding_generated = CandidateItem.model_validate(
        {
            **source.model_dump(mode="python"),
            "generation_mode": GenerationMode.LIVE,
            "model_id": "fake-model",
            "generation_metadata": generation_metadata(source),
        }
    )

    with pytest.raises(ValueError, match="already exists"):
        service.save_generated_item(
            project.config.project_id,
            colliding_generated,
        )

    reloaded = repository.load(project.config.project_id)
    assert reloaded == reviewed_project
    assert reloaded.items[source.item_id].review_versions == reviewed.review_versions


def test_review_transaction_is_serialized_across_service_instances(tmp_path) -> None:
    root = tmp_path / "projects"
    repository_one = JsonProjectRepository(root)
    repository_two = JsonProjectRepository(root.resolve())
    project = build_demo_project()
    repository_one.save(project)
    item = next(iter(project.items.values()))
    service_one = WorkbenchService(repository_one)
    service_two = WorkbenchService(repository_two)
    first_loaded = Event()
    release_first = Event()
    second_entered_load = Event()
    real_first_load = repository_one.load
    real_second_load = repository_two.load
    failures: list[tuple[str, BaseException]] = []

    def slow_first_load(project_id: str):
        loaded = real_first_load(project_id)
        first_loaded.set()
        if not release_first.wait(timeout=5):
            raise TimeoutError("test did not release the first transaction")
        return loaded

    def observed_second_load(project_id: str):
        second_entered_load.set()
        return real_second_load(project_id)

    repository_one.load = slow_first_load  # type: ignore[method-assign]
    repository_two.load = observed_second_load  # type: ignore[method-assign]

    def edit(service: WorkbenchService, stem: str, note: str) -> None:
        try:
            service.review_item(
                project.config.project_id,
                item.item_id,
                stem,
                item.options,
                "thread-reviewer",
                ReviewAction.EDIT,
                note,
                expected_version=0,
            )
        except BaseException as exc:
            failures.append((note, exc))

    first_thread = Thread(
        target=edit,
        args=(service_one, "第一个线程修改后的题干", "first"),
    )
    second_thread = Thread(
        target=edit,
        args=(service_two, "第二个线程修改后的题干", "second"),
    )
    first_thread.start()
    assert first_loaded.wait(timeout=5)
    second_thread.start()
    second_entered_before_release = second_entered_load.wait(timeout=0.2)
    release_first.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert len(failures) == 1
    failed_note, failure = failures[0]
    assert failed_note == "second"
    assert isinstance(failure, ValueError)
    assert str(failure) == "review version conflict: expected 0, current 1"
    assert not second_entered_before_release
    restored = repository_one.load(project.config.project_id)
    restored_item = restored.items[item.item_id]
    assert [version.version for version in restored_item.review_versions] == [1]
    assert [version.note for version in restored_item.review_versions] == ["first"]
    assert restored_item.stem_zh == "第一个线程修改后的题干"


def test_save_generated_item_rejects_invalid_or_mismatched_input(tmp_path) -> None:
    service, repository, project = service_with_seed(tmp_path)

    with pytest.raises(ValueError, match="CandidateItem"):
        service.save_generated_item(project.config.project_id, {"item_id": "wrong"})

    curated = next(iter(project.items.values()))
    with pytest.raises(
        ValueError,
        match="generated item must use LIVE generation mode",
    ):
        service.save_generated_item(project.config.project_id, curated)

    assert repository.load(project.config.project_id) == project


def test_unauthorized_service_denies_review_without_loading_or_writing(
    tmp_path,
) -> None:
    service, repository, project = service_with_seed(tmp_path)
    service = WorkbenchService(repository, mutation_authorized=False)
    item = next(iter(project.items.values()))

    with pytest.raises(MutationPermissionError, match="Researcher Access"):
        review(service, project.config.project_id, item)

    assert repository.load(project.config.project_id) == project


def test_unauthorized_service_denies_generation_before_input_validation(
    tmp_path,
) -> None:
    service, repository, project = service_with_seed(tmp_path)
    service = WorkbenchService(repository, mutation_authorized=False)

    with pytest.raises(MutationPermissionError, match="Researcher Access"):
        service.save_generated_item(project.config.project_id, {"invalid": True})

    assert repository.load(project.config.project_id) == project
