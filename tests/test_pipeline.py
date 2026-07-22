from collections import deque

import pytest

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.model_client import ModelUnavailable
from psychometric_v2.models import (
    CheckOutcome,
    CheckSeverity,
    ConstructSpecification,
    EvidenceStatus,
    GenerationMode,
    ProjectConfig,
    ScenarioBlueprint,
)
from psychometric_v2.pipeline import GenerationPipeline, GenerationStageError
from psychometric_v2.prompts import (
    blueprint_prompt,
    construct_prompt,
    options_prompt,
    quality_prompt,
)


REQUIRED_QUALITY_IDS = (
    "AGE_FIT",
    "ECOLOGICAL_PLAUSIBILITY",
    "CONSTRUCT_ALIGNMENT",
    "CONFOUNDS",
    "DISTINGUISHABILITY",
    "SOCIAL_DESIRABILITY",
    "ANSWER_OBVIOUSNESS",
    "LANGUAGE_COMPLEXITY",
    "SAFETY",
)


class QueueClient:
    model_id = "fake-model"

    def __init__(self, responses: list[object]) -> None:
        self.responses = deque(responses)
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system: str, user: str) -> dict[str, object]:
        self.calls.append((system, user))
        response = self.responses.popleft()
        if isinstance(response, Exception):
            raise response
        assert isinstance(response, dict)
        return response


def project_config() -> ProjectConfig:
    return ProjectConfig(
        project_id="live-generation-test",
        title="Live generation test",
        instruction_zh="如果是你，你最可能怎么做？",
        prompt_version="v2.1-test",
    )


def construct_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "definition_zh": "在同伴互动中主动接近并维持交流的可观察倾向。",
        "behavioral_indicators": ["主动发起交谈", "持续回应同伴"],
        "exclusions": ["单纯的口语能力"],
        "potential_confounds": ["社交焦虑"],
    }
    payload.update(changes)
    return payload


def blueprint_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "setting": "社团分组活动",
        "actors": ["你", "几位同龄同学"],
        "relationship": "初次见面的同伴",
        "goal": "组成小组并开始活动",
        "trigger_event": "老师请大家自由组队",
        "decision_point": "决定如何加入同伴互动",
        "context_domain": "club",
    }
    payload.update(changes)
    return payload


def option_payload(option_id: str, score: int, order: int) -> dict[str, object]:
    return {
        "option_id": option_id,
        "text_zh": f"先观察情况，再采取第{score}种具体行动",
        "trait_level": score,
        "score": score,
        "display_order": order,
        "rationale": f"呈现可观察的第{score}级行为",
        "desirability_note": "这是可理解的行为选择，不代表道德对错",
    }


def options_payload(*, valid: bool = True, **changes: object) -> dict[str, object]:
    options = [option_payload(f"o{score}", score, score) for score in range(1, 5)]
    if not valid:
        options.pop()
    payload: dict[str, object] = {
        "stem_zh": "社团活动中，老师请大家自由组成小组，这时你最可能怎么做？",
        "options": options,
    }
    payload.update(changes)
    return payload


def quality_payload(
    *,
    missing: tuple[str, ...] = (),
    extra_ids: tuple[str, ...] = (),
) -> dict[str, object]:
    check_ids = [
        check_id for check_id in REQUIRED_QUALITY_IDS if check_id not in missing
    ]
    check_ids.extend(extra_ids)
    return {
        "checks": [
            {
                "check_id": check_id,
                "label": check_id,
                "severity": CheckSeverity.WARNING.value,
                "outcome": CheckOutcome.PASS.value,
                "evidence": "场景和措辞符合初中生日常经验。",
                "recommendation": "",
            }
            for check_id in check_ids
        ]
    }


def stage_responses() -> list[dict[str, object]]:
    return [
        construct_payload(),
        blueprint_payload(),
        options_payload(),
        quality_payload(),
    ]


def test_prompts_scope_each_stage_and_require_safe_observable_chinese() -> None:
    client = QueueClient([construct_payload(), blueprint_payload(), options_payload()])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    config = project_config()
    spec = pipeline.construct(anchor, config)
    blueprint = pipeline.blueprint(spec, config, "club")
    item = pipeline.options(spec, blueprint, config)

    prompt_pairs = (
        construct_prompt(anchor, anchor.facet_id, config),
        blueprint_prompt(spec, config, "club"),
        options_prompt(spec, blueprint, config),
        quality_prompt(item, config),
    )

    for system, user in prompt_pairs:
        combined = f"{system}\n{user}"
        assert "中国大陆" in combined
        assert "12–15" in combined or "12-15" in combined
        assert "简体中文" in combined
        assert "可观察" in combined
        assert "chain-of-thought" in combined.lower()
        assert "不得" in combined or "不要" in combined
        assert "简短" in combined or "concise" in combined.lower()

    assert "definition_zh" in "".join(construct_prompt(anchor, anchor.facet_id, config))
    assert "context_domain" in "".join(blueprint_prompt(spec, config, "club"))
    assert "stem_zh" in "".join(options_prompt(spec, blueprint, config))
    quality_text = "".join(quality_prompt(item, config))
    for check in (
        "年龄适配",
        "生态合理性",
        "构念一致性",
        "混淆",
        "可区分性",
        "社会赞许性",
        "答案明显性",
        "语言复杂度",
        "安全",
    ):
        assert check in quality_text
    for check_id in REQUIRED_QUALITY_IDS:
        assert check_id in quality_text


def test_pipeline_repairs_invalid_options_once_and_merges_quality_checks() -> None:
    client = QueueClient(
        [
            construct_payload(
                domain_id="forged-domain",
                facet_id="forged-facet",
                anchor_ids=["forged-anchor"],
            ),
            blueprint_payload(context_domain="forged-context"),
            options_payload(valid=False, anchor_ids=["forged-anchor"]),
            options_payload(anchor_ids=["forged-anchor"]),
            quality_payload(),
        ]
    )
    pipeline = GenerationPipeline(client, anchor_asset=ANCHOR_ASSET)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    config = project_config()

    candidate = pipeline.generate_candidate(config, anchor, "club")

    assert len(client.calls) == 5
    repair_system, repair_user = client.calls[3]
    assert "repair" in repair_system.lower() or "修复" in repair_system
    assert "JSON schema" in repair_user
    assert "options" in repair_user
    assert "forged-anchor" in repair_user
    assert candidate.domain_id == anchor.domain_id
    assert candidate.facet_id == anchor.facet_id
    assert candidate.anchor_ids == (anchor.anchor_id,)
    assert candidate.construct_spec is not None
    assert candidate.construct_spec.domain_id == anchor.domain_id
    assert candidate.construct_spec.anchor_ids == (anchor.anchor_id,)
    assert candidate.scenario_blueprint is not None
    assert candidate.scenario_blueprint.context_domain == "club"
    assert candidate.evidence_status is EvidenceStatus.MODEL_DRAFT
    assert candidate.generation_mode is GenerationMode.LIVE
    assert candidate.model_id == "fake-model"
    assert candidate.prompt_version == "v2.1-test"
    assert candidate.generation_metadata is not None
    assert candidate.generation_metadata.model_id == candidate.model_id
    assert candidate.generation_metadata.prompt_version == candidate.prompt_version
    assert candidate.generation_metadata.model_dump(mode="json")[
        "constraint_snapshot"
    ] == {
        "project_config": config.model_dump(mode="json"),
        "domain_id": anchor.domain_id,
        "facet_id": anchor.facet_id,
        "anchor_ids": [anchor.anchor_id],
        "context_domain": "club",
    }
    assert candidate.item_id.startswith("live-sociability-")
    check_ids = {check.check_id for check in candidate.quality_checks}
    assert "OPTION_COUNT" in check_ids
    assert set(REQUIRED_QUALITY_IDS).issubset(check_ids)


def test_pipeline_repairs_blank_option_provenance_once() -> None:
    invalid = options_payload()
    invalid["options"][0]["rationale"] = " "  # type: ignore[index]
    client = QueueClient([invalid, options_payload()])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    spec = ConstructSpecification(
        domain_id=anchor.domain_id,
        facet_id=anchor.facet_id,
        anchor_ids=(anchor.anchor_id,),
        **construct_payload(),
    )
    blueprint = ScenarioBlueprint(**blueprint_payload())

    candidate = pipeline.options(spec, blueprint, project_config())

    assert len(client.calls) == 2
    assert "rationale" in client.calls[1][1]
    assert all(option.rationale.strip() for option in candidate.options)
    assert all(option.desirability_note.strip() for option in candidate.options)


def test_pipeline_repairs_model_check_id_collision_before_merge() -> None:
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(),
            quality_payload(extra_ids=("PROVENANCE",)),
            quality_payload(),
        ]
    )
    pipeline = GenerationPipeline(client)

    candidate = pipeline.generate_candidate(
        project_config(), "bfi2-sociability-01", "club"
    )

    check_ids = [check.check_id for check in candidate.quality_checks]
    assert len(client.calls) == 5
    assert len(check_ids) == len(set(check_ids))
    assert check_ids.count("PROVENANCE") == 1
    assert set(REQUIRED_QUALITY_IDS).issubset(check_ids)
    assert "reserved" in client.calls[4][1].lower()


def test_pipeline_repairs_missing_required_quality_dimension_once() -> None:
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(),
            quality_payload(missing=("SAFETY",)),
            quality_payload(),
        ]
    )
    pipeline = GenerationPipeline(client)

    candidate = pipeline.generate_candidate(
        project_config(), "bfi2-sociability-01", "club"
    )

    assert len(client.calls) == 5
    assert "SAFETY" in client.calls[4][1]
    assert set(REQUIRED_QUALITY_IDS).issubset(
        {check.check_id for check in candidate.quality_checks}
    )


def test_pipeline_repairs_required_quality_id_with_surrounding_whitespace() -> None:
    malformed = quality_payload()
    malformed["checks"][0]["check_id"] = " AGE_FIT "  # type: ignore[index]
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(),
            malformed,
            quality_payload(),
        ]
    )
    pipeline = GenerationPipeline(client)

    candidate = pipeline.generate_candidate(
        project_config(), "bfi2-sociability-01", "club"
    )

    assert len(client.calls) == 5
    assert {check.check_id for check in candidate.quality_checks}.issuperset(
        REQUIRED_QUALITY_IDS
    )


def test_pipeline_rejects_second_quality_response_missing_required_dimension() -> None:
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(),
            quality_payload(missing=("SAFETY",)),
            quality_payload(missing=("SAFETY",)),
        ]
    )
    pipeline = GenerationPipeline(client)

    with pytest.raises(GenerationStageError) as captured:
        pipeline.generate_candidate(
            project_config(), "bfi2-sociability-01", "club"
        )

    assert captured.value.stage == "quality"
    assert len(client.calls) == 5
    assert "candidate" in captured.value.partial_results


def test_pipeline_stops_after_second_stage_validation_failure() -> None:
    client = QueueClient([options_payload(valid=False), options_payload(valid=False)])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")
    spec = ConstructSpecification(
        domain_id=anchor.domain_id,
        facet_id=anchor.facet_id,
        anchor_ids=(anchor.anchor_id,),
        **construct_payload(),
    )
    blueprint = ScenarioBlueprint(**blueprint_payload())

    with pytest.raises(GenerationStageError) as captured:
        pipeline.options(spec, blueprint, project_config())

    assert captured.value.stage == "options"
    assert len(client.calls) == 2
    assert "先观察" not in captured.value.public_message
    assert captured.value.public_message == (
        "The options stage returned invalid structured data."
    )


def test_orchestration_preserves_completed_stages_on_failure() -> None:
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(valid=False),
            options_payload(valid=False),
        ]
    )
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")

    with pytest.raises(GenerationStageError) as captured:
        pipeline.generate_candidate(project_config(), anchor, "club")

    partial = captured.value.partial_results
    assert partial["construct"].facet_id == "sociability"
    assert partial["blueprint"].context_domain == "club"
    assert len(client.calls) == 4


def test_quality_failure_preserves_candidate_with_deterministic_checks() -> None:
    client = QueueClient(
        [
            construct_payload(),
            blueprint_payload(),
            options_payload(),
            {"checks": []},
            {"checks": []},
        ]
    )
    pipeline = GenerationPipeline(client)

    with pytest.raises(GenerationStageError) as captured:
        pipeline.generate_candidate(
            project_config(), "bfi2-sociability-01", "club"
        )

    assert captured.value.stage == "quality"
    candidate = captured.value.partial_results["candidate"]
    assert "OPTION_COUNT" in {check.check_id for check in candidate.quality_checks}
    assert len(client.calls) == 5


def test_construct_reloads_canonical_anchor_instead_of_trusting_caller_text() -> None:
    client = QueueClient([construct_payload()])
    pipeline = GenerationPipeline(client)
    canonical = pipeline.load_anchor("bfi2-sociability-01")
    forged = canonical.validated_update(text_zh="FORGED ANCHOR TEXT")

    spec = pipeline.construct(forged, project_config())

    assert spec.anchor_ids == (canonical.anchor_id,)
    assert "FORGED ANCHOR TEXT" not in client.calls[0][1]
    assert canonical.text_zh in client.calls[0][1]


def test_transport_failure_is_not_retried() -> None:
    client = QueueClient([ModelUnavailable("must not escape")])
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")

    with pytest.raises(GenerationStageError) as captured:
        pipeline.construct(anchor, project_config())

    assert len(client.calls) == 1
    assert "must not escape" not in str(captured.value)


def test_load_anchor_rejects_unknown_id_clearly() -> None:
    pipeline = GenerationPipeline(QueueClient([]))

    with pytest.raises(KeyError, match="unknown anchor_id"):
        pipeline.load_anchor("not-an-anchor")


def test_live_item_ids_are_unique() -> None:
    client = QueueClient(stage_responses() + stage_responses())
    pipeline = GenerationPipeline(client)
    anchor = pipeline.load_anchor("bfi2-sociability-01")

    first = pipeline.generate_candidate(project_config(), anchor, "club")
    second = pipeline.generate_candidate(project_config(), anchor, "club")

    assert first.item_id != second.item_id
