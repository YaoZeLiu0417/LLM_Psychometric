from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from psychometric_v2.config import ANCHOR_ASSET, ModelError
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    ConstructSpecification,
    EvidenceStatus,
    GenerationMode,
    ProjectConfig,
    QualityCheck,
    ResponseOption,
    ScenarioBlueprint,
)
from psychometric_v2.prompts import (
    REQUIRED_QUALITY_CHECK_IDS,
    blueprint_prompt,
    construct_prompt,
    options_prompt,
    quality_prompt,
)
from psychometric_v2.quality import run_deterministic_checks


_StageModelT = TypeVar("_StageModelT", bound=BaseModel)


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("value must not be blank")
    return value


def _nonempty_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        raise ValueError("list must not be empty")
    if any(not value.strip() for value in values):
        raise ValueError("list values must not be blank")
    return values


class _StageModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class _ConstructResponse(_StageModel):
    definition_zh: str
    behavioral_indicators: tuple[str, ...]
    exclusions: tuple[str, ...]
    potential_confounds: tuple[str, ...]

    @field_validator("definition_zh")
    @classmethod
    def validate_definition(cls, value: str) -> str:
        return _nonblank(value)

    @field_validator(
        "behavioral_indicators", "exclusions", "potential_confounds"
    )
    @classmethod
    def validate_lists(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _nonempty_strings(values)


class _BlueprintResponse(_StageModel):
    setting: str
    actors: tuple[str, ...]
    relationship: str
    goal: str
    trigger_event: str
    decision_point: str
    context_domain: str

    @field_validator(
        "setting",
        "relationship",
        "goal",
        "trigger_event",
        "decision_point",
        "context_domain",
    )
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _nonblank(value)

    @field_validator("actors")
    @classmethod
    def validate_actors(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _nonempty_strings(values)


class _OptionsResponse(_StageModel):
    stem_zh: str
    options: tuple[ResponseOption, ...]

    @field_validator("stem_zh")
    @classmethod
    def validate_stem(cls, value: str) -> str:
        return _nonblank(value)

    @model_validator(mode="after")
    def validate_option_set(self) -> "_OptionsResponse":
        options = self.options
        expected = {1, 2, 3, 4}
        if len(options) != 4:
            raise ValueError("exactly four options are required")
        if {option.score for option in options} != expected:
            raise ValueError("option scores must cover 1..4")
        if {option.trait_level for option in options} != expected:
            raise ValueError("trait levels must cover 1..4")
        if {option.display_order for option in options} != expected:
            raise ValueError("display order must cover 1..4")
        if any(option.trait_level != option.score for option in options):
            raise ValueError("trait level and score must match")
        ids = [option.option_id.strip() for option in options]
        texts = [option.text_zh.strip() for option in options]
        if any(not value for value in (*ids, *texts)):
            raise ValueError("option identifiers and text must not be blank")
        if len(set(ids)) != 4 or len(set(texts)) != 4:
            raise ValueError("option identifiers and text must be unique")
        return self


class _QualityResponse(_StageModel):
    checks: tuple[QualityCheck, ...]

    @field_validator("checks")
    @classmethod
    def validate_checks(
        cls,
        checks: tuple[QualityCheck, ...],
        info: ValidationInfo,
    ) -> tuple[QualityCheck, ...]:
        if not checks:
            raise ValueError("checks must not be empty")
        raw_ids = [check.check_id for check in checks]
        ids = [check_id.strip() for check_id in raw_ids]
        if any(not check_id for check_id in ids) or len(set(ids)) != len(ids):
            raise ValueError("quality check IDs must be nonblank and unique")
        if raw_ids != ids:
            raise ValueError(
                "quality check IDs must not contain surrounding whitespace"
            )
        context = info.context or {}
        required_ids = set(context.get("required_check_ids", ()))
        missing_ids = required_ids.difference(ids)
        if missing_ids:
            missing = ", ".join(sorted(missing_ids))
            raise ValueError(f"missing required model quality check IDs: {missing}")
        reserved_ids = set(context.get("reserved_check_ids", ()))
        if reserved_ids.intersection(ids):
            raise ValueError(
                "model quality check IDs must not use reserved deterministic IDs"
            )
        return checks


class GenerationStageError(RuntimeError):
    def __init__(
        self,
        stage: str,
        public_message: str,
        partial_results: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(public_message)
        self.stage = stage
        self.public_message = public_message
        self.partial_results = dict(partial_results or {})


class GenerationPipeline:
    def __init__(self, client: Any, anchor_asset: object = ANCHOR_ASSET) -> None:
        self.client = client
        self.anchors = load_anchor_asset(anchor_asset)

    def load_anchor(self, anchor_id: str) -> ConstructAnchor:
        try:
            return self.anchors[anchor_id]
        except KeyError:
            raise KeyError(f"unknown anchor_id: {anchor_id}") from None

    def _request_stage(
        self,
        stage: str,
        prompt: tuple[str, str],
        response_model: type[_StageModelT],
        validation_context: Mapping[str, object] | None = None,
    ) -> _StageModelT:
        system, user = prompt
        raw: dict[str, Any] | None = None
        for attempt in range(2):
            try:
                raw = self.client.complete_json(system, user)
            except ModelError:
                raise GenerationStageError(
                    stage,
                    f"The {stage} stage could not reach the model service.",
                ) from None

            try:
                return response_model.model_validate(
                    raw,
                    context=validation_context,
                )
            except (ValidationError, ValueError) as validation_error:
                if attempt == 1:
                    raise GenerationStageError(
                        stage,
                        f"The {stage} stage returned invalid structured data.",
                    ) from None
                system = (
                    f"Repair the {stage} stage JSON. Return only the corrected JSON "
                    "object; do not provide chain-of-thought or hidden reasoning."
                )
                user = (
                    "Fix the validation errors while preserving valid content.\n"
                    f"Validation message:\n{validation_error}\n"
                    "Exact JSON schema:\n"
                    f"{json.dumps(response_model.model_json_schema(), ensure_ascii=False)}"
                    "\n"
                    "Invalid JSON:\n"
                    f"{json.dumps(raw, ensure_ascii=False)}"
                )
        raise AssertionError("unreachable")

    def construct(
        self,
        anchor: ConstructAnchor,
        config: ProjectConfig,
    ) -> ConstructSpecification:
        canonical_anchor = self.load_anchor(anchor.anchor_id)
        parsed = self._request_stage(
            "construct",
            construct_prompt(canonical_anchor, canonical_anchor.facet_id, config),
            _ConstructResponse,
        )
        return ConstructSpecification(
            domain_id=canonical_anchor.domain_id,
            facet_id=canonical_anchor.facet_id,
            anchor_ids=(canonical_anchor.anchor_id,),
            **parsed.model_dump(),
        )

    def blueprint(
        self,
        spec: ConstructSpecification,
        config: ProjectConfig,
        context_domain: str,
    ) -> ScenarioBlueprint:
        if not context_domain.strip():
            raise ValueError("context_domain must not be blank")
        if context_domain not in config.context_domains:
            raise ValueError("context_domain must be allowed by the project config")
        parsed = self._request_stage(
            "blueprint",
            blueprint_prompt(spec, config, context_domain),
            _BlueprintResponse,
        )
        values = parsed.model_dump()
        values["context_domain"] = context_domain
        return ScenarioBlueprint.model_validate(values)

    def options(
        self,
        spec: ConstructSpecification,
        blueprint: ScenarioBlueprint,
        config: ProjectConfig,
    ) -> CandidateItem:
        parsed = self._request_stage(
            "options",
            options_prompt(spec, blueprint, config),
            _OptionsResponse,
        )
        return CandidateItem(
            item_id=f"live-{spec.facet_id}-{uuid4().hex}",
            domain_id=spec.domain_id,
            facet_id=spec.facet_id,
            anchor_ids=spec.anchor_ids,
            instruction_zh=config.instruction_zh,
            stem_zh=parsed.stem_zh,
            construct_spec=spec,
            scenario_blueprint=blueprint,
            options=parsed.options,
            evidence_status=EvidenceStatus.MODEL_DRAFT,
            generation_mode=GenerationMode.LIVE,
            model_id=self.client.model_id,
            prompt_version=config.prompt_version,
        )

    def quality(
        self,
        item: CandidateItem,
        config: ProjectConfig,
    ) -> tuple[QualityCheck, ...]:
        deterministic_ids = {
            check.check_id for check in run_deterministic_checks(item)
        }
        parsed = self._request_stage(
            "quality",
            quality_prompt(item, config),
            _QualityResponse,
            validation_context={
                "required_check_ids": REQUIRED_QUALITY_CHECK_IDS,
                "reserved_check_ids": deterministic_ids,
            },
        )
        return parsed.checks

    generate_construct = construct
    generate_blueprint = blueprint
    generate_options = options
    generate_quality = quality
    candidate = options

    def generate_candidate(
        self,
        config: ProjectConfig,
        anchor: ConstructAnchor | str,
        context_domain: str,
    ) -> CandidateItem:
        selected_anchor = (
            self.load_anchor(anchor) if isinstance(anchor, str) else anchor
        )
        partial: dict[str, object] = {}
        try:
            spec = self.construct(selected_anchor, config)
            partial["construct"] = spec
            blueprint = self.blueprint(spec, config, context_domain)
            partial["blueprint"] = blueprint
            candidate = self.options(spec, blueprint, config)
            partial["options"] = candidate
            deterministic = run_deterministic_checks(candidate)
            checked_candidate = CandidateItem.model_validate(
                {
                    **candidate.model_dump(mode="python"),
                    "quality_checks": deterministic,
                }
            )
            partial["options"] = checked_candidate
            partial["candidate"] = checked_candidate
            model_checks = self.quality(checked_candidate, config)
            return CandidateItem.model_validate(
                {
                    **checked_candidate.model_dump(mode="python"),
                    "quality_checks": (*deterministic, *model_checks),
                }
            )
        except GenerationStageError as error:
            raise GenerationStageError(
                error.stage,
                error.public_message,
                partial_results=partial,
            ) from None
