import copy
import json
import pickle
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from psychometric_v2.models import (
    CandidateItem,
    CheckOutcome,
    CheckSeverity,
    ConstructAnchor,
    ConstructSpecification,
    EvidenceStatus,
    GenerationMetadata,
    GenerationMode,
    ProjectConfig,
    QualityCheck,
    ResearchProject,
    ResponseOption,
    ReviewAction,
    ReviewVersion,
)


def make_option(
    score: int,
    order: int,
    *,
    trait_level: int | None = None,
    option_id: str | None = None,
    text_zh: str | None = None,
) -> ResponseOption:
    return ResponseOption(
        option_id=f"o{order}" if option_id is None else option_id,
        text_zh=f"行为选项{order}" if text_zh is None else text_zh,
        trait_level=score if trait_level is None else trait_level,
        score=score,
        display_order=order,
        rationale=f"可观察行为水平{score}",
        desirability_note="无明显道德优劣",
    )


def make_options() -> list[ResponseOption]:
    return [make_option(score, score) for score in range(1, 5)]


def make_candidate(**changes: object) -> CandidateItem:
    values: dict[str, object] = {
        "item_id": "item-1",
        "domain_id": "extraversion",
        "facet_id": "sociability",
        "anchor_ids": ["bfi2-sociability-01"],
        "instruction_zh": "如果是你，你最可能怎么做？",
        "stem_zh": "一次社团活动开始前，几位同学还不熟悉彼此。",
        "options": make_options(),
    }
    values.update(changes)
    return CandidateItem(**values)


def make_review(**changes: object) -> ReviewVersion:
    values: dict[str, object] = {
        "version": 1,
        "reviewer": "reviewer-1",
        "action": ReviewAction.EDIT,
        "note": "clarify wording",
        "before_stem_zh": "修改前题干",
        "before_options": make_options(),
        "after_stem_zh": "修改后题干",
        "after_options": make_options(),
    }
    values.update(changes)
    return ReviewVersion(**values)


def make_anchor(**changes: object) -> ConstructAnchor:
    values: dict[str, object] = {
        "anchor_id": "bfi2-sociability-01",
        "item_number": 1,
        "text_zh": "我很外向，喜欢社交。",
        "legacy_feature": "外向性、社交",
        "domain_id": "extraversion",
        "facet_id": "sociability",
        "reverse": False,
    }
    values.update(changes)
    return ConstructAnchor(**values)


def make_construct_spec(**changes: object) -> ConstructSpecification:
    values: dict[str, object] = {
        "domain_id": "extraversion",
        "facet_id": "sociability",
        "anchor_ids": ["bfi2-sociability-01"],
        "definition_zh": "定义",
        "behavioral_indicators": ["行为"],
        "exclusions": [],
        "potential_confounds": [],
    }
    values.update(changes)
    return ConstructSpecification(**values)


def make_quality_check() -> QualityCheck:
    return QualityCheck(
        check_id="age-fit",
        label="年龄适配",
        severity=CheckSeverity.INFO,
        outcome=CheckOutcome.PASS,
        evidence="语言适合目标年龄。",
    )


def pickle_round_trip(value: object) -> object:
    return pickle.loads(pickle.dumps(value))


def test_candidate_requires_four_unique_score_levels() -> None:
    item = CandidateItem(
        item_id="item-1",
        domain_id="extraversion",
        facet_id="sociability",
        anchor_ids=["bfi2-sociability-01"],
        instruction_zh="如果是你，你最可能怎么做？",
        stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
        options=[
            make_option(4, 1),
            make_option(1, 2),
            make_option(3, 3),
            make_option(2, 4),
        ],
        evidence_status=EvidenceStatus.MODEL_DRAFT,
    )
    assert {option.score for option in item.options} == {1, 2, 3, 4}


def test_candidate_rejects_duplicate_scores() -> None:
    with pytest.raises(ValidationError):
        CandidateItem(
            item_id="item-1",
            domain_id="extraversion",
            facet_id="sociability",
            anchor_ids=["bfi2-sociability-01"],
            instruction_zh="如果是你，你最可能怎么做？",
            stem_zh="一次社团活动开始前，几位同学还不熟悉彼此。",
            options=[
                make_option(1, 1),
                make_option(1, 2),
                make_option(3, 3),
                make_option(4, 4),
            ],
        )


def test_validated_is_not_an_allowed_evidence_status() -> None:
    assert "VALIDATED" not in {status.value for status in EvidenceStatus}


def test_list_input_is_normalized_to_immutable_options() -> None:
    item = make_candidate(options=make_options())

    assert isinstance(item.options, tuple)
    with pytest.raises(TypeError):
        item.options[0] = make_option(1, 1)  # type: ignore[index]
    with pytest.raises(ValidationError):
        item.options[0].text_zh = "被篡改的选项"


def test_review_history_snapshots_cannot_be_rewritten() -> None:
    review = make_review()

    assert isinstance(review.before_options, tuple)
    assert isinstance(review.after_options, tuple)
    with pytest.raises(ValidationError):
        review.before_stem_zh = "被篡改的题干"
    with pytest.raises(TypeError):
        review.before_options[0] = make_option(1, 1)  # type: ignore[index]
    with pytest.raises(ValidationError):
        review.after_options[0].text_zh = "被篡改的选项"


def test_review_snapshots_enforce_candidate_option_rules() -> None:
    with pytest.raises(ValidationError):
        make_review(before_options=make_options()[:3])


@pytest.mark.parametrize(
    ("domain_id", "facet_id"),
    [
        ("unknown", "sociability"),
        ("agreeableness", "sociability"),
    ],
)
def test_candidate_requires_a_valid_taxonomy_pair(
    domain_id: str, facet_id: str
) -> None:
    with pytest.raises(ValidationError):
        make_candidate(domain_id=domain_id, facet_id=facet_id)


@pytest.mark.parametrize(
    "anchor_ids",
    [
        [""],
        ["   "],
        ["anchor-1", "anchor-1"],
        ["anchor-1", " anchor-1 "],
    ],
)
def test_candidate_requires_nonblank_unique_anchor_ids(
    anchor_ids: list[str],
) -> None:
    with pytest.raises(ValidationError):
        make_candidate(anchor_ids=anchor_ids)


@pytest.mark.parametrize(
    "construct_spec",
    [
        ConstructSpecification(
            domain_id="agreeableness",
            facet_id="compassion",
            anchor_ids=["bfi2-sociability-01"],
            definition_zh="定义",
            behavioral_indicators=["行为"],
            exclusions=[],
            potential_confounds=[],
        ),
        ConstructSpecification(
            domain_id="extraversion",
            facet_id="assertiveness",
            anchor_ids=["bfi2-sociability-01"],
            definition_zh="定义",
            behavioral_indicators=["行为"],
            exclusions=[],
            potential_confounds=[],
        ),
        ConstructSpecification(
            domain_id="extraversion",
            facet_id="sociability",
            anchor_ids=["different-anchor"],
            definition_zh="定义",
            behavioral_indicators=["行为"],
            exclusions=[],
            potential_confounds=[],
        ),
    ],
)
def test_candidate_construct_spec_must_match_provenance(
    construct_spec: ConstructSpecification,
) -> None:
    with pytest.raises(ValidationError):
        make_candidate(construct_spec=construct_spec)


@pytest.mark.parametrize(
    "options",
    [
        make_options()[:3],
        [
            make_option(1, 1),
            make_option(1, 2),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1, trait_level=2),
            make_option(2, 2, trait_level=1),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1),
            make_option(2, 1),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1, option_id="same"),
            make_option(2, 2, option_id="same"),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1, text_zh=" "),
            make_option(2, 2),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1, text_zh="相同行为"),
            make_option(2, 2, text_zh=" 相同行为 "),
            make_option(3, 3),
            make_option(4, 4),
        ],
    ],
    ids=[
        "count",
        "scores",
        "trait-level-match",
        "display-order",
        "duplicate-id",
        "blank-text",
        "duplicate-text",
    ],
)
def test_candidate_rejects_invalid_option_sets(
    options: list[ResponseOption],
) -> None:
    with pytest.raises(ValidationError):
        make_candidate(options=options)


def test_research_project_requires_item_keys_to_match_item_ids() -> None:
    with pytest.raises(ValidationError):
        ResearchProject(
            config=ProjectConfig(project_id="p", title="Project"),
            items={"wrong-key": make_candidate()},
        )


def test_research_project_requires_selected_item_to_exist() -> None:
    with pytest.raises(ValidationError):
        ResearchProject(
            config=ProjectConfig(project_id="p", title="Project"),
            items={"item-1": make_candidate()},
            selected_item_id="missing-item",
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"project_id": ""},
        {"project_id": "   "},
        {"title": " "},
        {"instruction_zh": "\t"},
        {"age_min": -1},
        {"age_max": -1},
        {"age_min": 16, "age_max": 15},
    ],
)
def test_project_config_rejects_invalid_core_fields(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {"project_id": "p", "title": "Project"}
    values.update(changes)

    with pytest.raises(ValidationError):
        ProjectConfig(**values)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: make_candidate(created_at="2026-07-22T12:00:00"),
        lambda: make_review(created_at="2026-07-22T12:00:00"),
        lambda: ResearchProject(
            config=ProjectConfig(project_id="p", title="Project"),
            updated_at="2026-07-22T12:00:00",
        ),
        lambda: GenerationMetadata(
            model_id="model",
            prompt_version="v2.0-demo",
            generated_at="2026-07-22T12:00:00",
            constraint_snapshot={},
        ),
    ],
    ids=["candidate", "review", "project", "generation"],
)
def test_persisted_timestamps_must_be_timezone_aware(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_json_round_trip_preserves_models_and_enum_values() -> None:
    item = make_candidate(
        evidence_status=EvidenceStatus.HUMAN_REVIEWED,
        generation_mode=GenerationMode.LIVE,
        created_at="2026-07-22T12:00:00+09:00",
    )

    payload = json.loads(item.model_dump_json())
    restored = CandidateItem.model_validate_json(item.model_dump_json())

    assert payload["evidence_status"] == "HUMAN_REVIEWED"
    assert payload["generation_mode"] == "LIVE GENERATION"
    assert restored == item


def test_project_config_is_a_durable_immutable_snapshot() -> None:
    config = ProjectConfig(project_id="p", title="Project")

    assert isinstance(config.context_domains, tuple)
    with pytest.raises(ValidationError):
        config.title = "Changed"
    with pytest.raises(TypeError):
        config.context_domains[0] = "changed"  # type: ignore[index]


def test_candidate_rejects_field_assignment_after_validation() -> None:
    item = make_candidate()

    with pytest.raises(ValidationError):
        item.domain_id = "agreeableness"


def test_candidate_nested_collections_are_durable_snapshots() -> None:
    item = make_candidate(
        construct_spec=make_construct_spec(),
        quality_checks=[make_quality_check()],
        review_versions=[make_review()],
    )

    assert isinstance(item.anchor_ids, tuple)
    assert isinstance(item.quality_checks, tuple)
    assert isinstance(item.review_versions, tuple)
    with pytest.raises(TypeError):
        item.anchor_ids[0] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        item.quality_checks[0] = make_quality_check()  # type: ignore[index]
    with pytest.raises(ValidationError):
        item.quality_checks[0].evidence = "changed"
    with pytest.raises(TypeError):
        item.review_versions[0] = make_review()  # type: ignore[index]
    with pytest.raises(ValidationError):
        item.construct_spec.domain_id = "agreeableness"  # type: ignore[union-attr]
    with pytest.raises(TypeError):
        item.construct_spec.anchor_ids[0] = "changed"  # type: ignore[index,union-attr]


def test_research_project_rejects_field_and_items_mutation() -> None:
    item = make_candidate()
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project"),
        items={item.item_id: item},
        selected_item_id=item.item_id,
    )

    with pytest.raises(ValidationError):
        project.selected_item_id = None
    with pytest.raises(TypeError):
        project.items["other"] = item  # type: ignore[index]


def test_research_project_json_round_trip_preserves_references() -> None:
    item = make_candidate()
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project"),
        items={item.item_id: item},
        selected_item_id=item.item_id,
    )

    payload = project.model_dump_json()
    restored = ResearchProject.model_validate_json(payload)

    assert restored == project
    assert restored.selected_item_id in restored.items
    with pytest.raises(TypeError):
        restored.items["other"] = item  # type: ignore[index]


@pytest.mark.parametrize(
    "changes",
    [
        {"domain_id": "unknown"},
        {"domain_id": "agreeableness"},
        {"facet_id": "assertiveness"},
        {"legacy_feature": "外向性、果断"},
        {"legacy_feature": "unknown"},
    ],
)
def test_construct_anchor_rejects_invalid_taxonomy_provenance(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        make_anchor(**changes)


@pytest.mark.parametrize(
    ("domain_id", "facet_id"),
    [
        ("unknown", "sociability"),
        ("agreeableness", "sociability"),
    ],
)
def test_construct_specification_requires_a_valid_taxonomy_pair(
    domain_id: str, facet_id: str
) -> None:
    with pytest.raises(ValidationError):
        make_construct_spec(domain_id=domain_id, facet_id=facet_id)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProjectConfig(project_id=" project ", title="Project"),
        lambda: make_anchor(anchor_id=" anchor-1 "),
        lambda: make_construct_spec(anchor_ids=[" anchor-1 "]),
        lambda: make_candidate(item_id=" item-1 "),
        lambda: make_candidate(anchor_ids=[" anchor-1 "]),
        lambda: make_option(1, 1, option_id=" "),
        lambda: make_option(1, 1, option_id=" o1 "),
    ],
    ids=[
        "project",
        "anchor",
        "construct-spec",
        "candidate",
        "candidate-anchor",
        "option-blank",
        "option",
    ],
)
def test_lookup_identifiers_reject_surrounding_whitespace(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(ValidationError):
        factory()


@pytest.mark.parametrize(
    "changes",
    [
        {"population": " "},
        {"locale": ""},
        {"prompt_version": "\t"},
        {"context_domains": []},
        {"context_domains": ["classroom", "classroom"]},
        {"context_domains": ["classroom", " classroom "]},
        {"context_domains": ["classroom", " "]},
    ],
)
def test_project_config_rejects_invalid_research_context(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {"project_id": "p", "title": "Project"}
    values.update(changes)

    with pytest.raises(ValidationError):
        ProjectConfig(**values)


def test_project_config_supports_general_age_ranges_with_an_upper_bound() -> None:
    config = ProjectConfig(
        project_id="p",
        title="Adult project",
        age_min=18,
        age_max=65,
    )

    assert (config.age_min, config.age_max) == (18, 65)
    with pytest.raises(ValidationError):
        ProjectConfig(project_id="p", title="Invalid", age_min=18, age_max=121)


@pytest.mark.parametrize(
    "clone",
    [
        copy.deepcopy,
        lambda project: project.model_copy(deep=True),
        pickle_round_trip,
    ],
    ids=["deepcopy", "model-copy-deep", "pickle"],
)
def test_research_project_supports_immutable_deep_clones(
    clone: Callable[[object], object],
) -> None:
    item = make_candidate()
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project"),
        items={item.item_id: item},
        selected_item_id=item.item_id,
    )

    cloned = clone(project)

    assert cloned == project
    assert cloned is not project
    assert cloned.model_dump(mode="json") == project.model_dump(mode="json")
    with pytest.raises(TypeError):
        cloned.items["other"] = item  # type: ignore[index,union-attr]


def test_research_project_mapping_storage_cannot_be_reassigned() -> None:
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project")
    )

    with pytest.raises((AttributeError, TypeError)):
        project.items._items = ()  # type: ignore[attr-defined]


def test_model_copy_update_revalidates_candidate_and_project() -> None:
    item = make_candidate()
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project"),
        items={item.item_id: item},
        selected_item_id=item.item_id,
    )

    with pytest.raises(ValidationError):
        item.model_copy(update={"domain_id": "agreeableness"})
    with pytest.raises(ValidationError):
        item.model_copy(update={"anchor_ids": []})
    with pytest.raises(ValidationError):
        project.model_copy(update={"selected_item_id": "missing"})


def test_validated_updates_rebuild_deeply_immutable_snapshots() -> None:
    item = make_candidate()
    updated_item = item.validated_update(
        stem_zh="更新后的题干",
        anchor_ids=["bfi2-sociability-01"],
    )
    copied_item = item.model_copy(
        update={
            "stem_zh": "通过兼容 API 更新",
            "anchor_ids": ["bfi2-sociability-01"],
        }
    )
    project = ResearchProject(
        config=ProjectConfig(project_id="p", title="Project"),
        items={item.item_id: item},
        selected_item_id=item.item_id,
    )
    updated_project = project.validated_update(
        items={updated_item.item_id: updated_item},
        selected_item_id=updated_item.item_id,
    )

    assert updated_item.stem_zh == "更新后的题干"
    assert copied_item.stem_zh == "通过兼容 API 更新"
    assert isinstance(updated_item.anchor_ids, tuple)
    assert isinstance(copied_item.anchor_ids, tuple)
    assert updated_project.items[updated_item.item_id] == updated_item
    with pytest.raises(TypeError):
        updated_project.items["other"] = item  # type: ignore[index]


def make_generation_metadata() -> GenerationMetadata:
    return GenerationMetadata(
        model_id="model-1",
        prompt_version="v2.0-demo",
        generated_at="2026-07-22T12:00:00+09:00",
        constraint_snapshot={
            "population": {"locale": "zh-CN", "ages": [12, 15]},
            "contexts": ["classroom", "peer"],
        },
    )


def test_generation_metadata_is_a_deeply_immutable_snapshot() -> None:
    metadata = make_generation_metadata()

    with pytest.raises(ValidationError):
        metadata.model_id = "changed"
    with pytest.raises(TypeError):
        metadata.constraint_snapshot["new"] = True  # type: ignore[index]
    with pytest.raises(TypeError):
        metadata.constraint_snapshot["population"]["locale"] = "en-US"  # type: ignore[index]
    with pytest.raises(TypeError):
        metadata.constraint_snapshot["contexts"][0] = "family"  # type: ignore[index]
    with pytest.raises(ValidationError):
        metadata.model_copy(update={"generated_at": "2026-07-22T12:00:00"})


@pytest.mark.parametrize(
    "clone",
    [
        copy.deepcopy,
        lambda metadata: metadata.model_copy(deep=True),
        pickle_round_trip,
    ],
    ids=["deepcopy", "model-copy-deep", "pickle"],
)
def test_generation_metadata_supports_persistence_round_trips(
    clone: Callable[[object], object],
) -> None:
    metadata = make_generation_metadata()

    cloned = clone(metadata)
    json_payload = metadata.model_dump(mode="json")
    restored = GenerationMetadata.model_validate_json(metadata.model_dump_json())

    assert cloned == metadata
    assert restored == metadata
    assert json_payload["constraint_snapshot"] == {
        "population": {"locale": "zh-CN", "ages": [12, 15]},
        "contexts": ["classroom", "peer"],
    }
    with pytest.raises(TypeError):
        cloned.constraint_snapshot["new"] = True  # type: ignore[index,union-attr]


@pytest.mark.parametrize(
    "constraint_snapshot",
    [
        {"nested": {1: "value"}},
        {"nested": {"value": float("nan")}},
        {"nested": {"value": float("inf")}},
        {"nested": {"value": float("-inf")}},
    ],
    ids=["non-string-key", "nan", "positive-infinity", "negative-infinity"],
)
def test_generation_metadata_rejects_noncanonical_json_values(
    constraint_snapshot: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        GenerationMetadata(
            model_id="model-1",
            prompt_version="v2.0-demo",
            constraint_snapshot=constraint_snapshot,
        )
