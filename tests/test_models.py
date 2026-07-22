import json
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from psychometric_v2.models import (
    CandidateItem,
    ConstructSpecification,
    EvidenceStatus,
    GenerationMetadata,
    GenerationMode,
    ProjectConfig,
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
            facet_id="sociability",
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
            make_option(1, 1, option_id=" "),
            make_option(2, 2),
            make_option(3, 3),
            make_option(4, 4),
        ],
        [
            make_option(1, 1, option_id="same"),
            make_option(2, 2, option_id=" same "),
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
        "blank-id",
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
