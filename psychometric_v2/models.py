from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from psychometric_v2.taxonomy import DOMAINS, FACETS, LEGACY_FEATURE_MAP


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_timezone_aware_iso(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value


def _validate_nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("value must not be blank")
    return value


def _validate_identifier(value: str) -> str:
    _validate_nonblank(value)
    if value != value.strip():
        raise ValueError("identifier must not contain surrounding whitespace")
    return value


def _validate_identifier_collection(values: tuple[str, ...]) -> tuple[str, ...]:
    for value in values:
        _validate_identifier(value)
    if len(set(values)) != len(values):
        raise ValueError("identifiers must be unique")
    return values


def _validate_taxonomy_pair(domain_id: str, facet_id: str) -> None:
    facet = FACETS.get(facet_id)
    if domain_id not in DOMAINS:
        raise ValueError("domain_id must identify a known domain")
    if facet is None or facet.domain_id != domain_id:
        raise ValueError("facet_id must belong to domain_id")


_AwareIsoString = Annotated[str, AfterValidator(_validate_timezone_aware_iso)]


class GenerationMode(str, Enum):
    LIVE = "LIVE GENERATION"
    CURATED = "CURATED DEMO"


class EvidenceStatus(str, Enum):
    MODEL_DRAFT = "MODEL_DRAFT"
    NEEDS_REVISION = "NEEDS_REVISION"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    PILOT_CANDIDATE = "PILOT_CANDIDATE"


class CheckSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CheckOutcome(str, Enum):
    PASS = "PASS"
    FLAG = "FLAG"


class ReviewAction(str, Enum):
    EDIT = "EDIT"
    RETURN = "RETURN"
    APPROVE = "APPROVE"
    PROMOTE_TO_PILOT = "PROMOTE_TO_PILOT"


class ProjectConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: str
    title: str
    population: str = "Mainland Chinese junior-secondary students"
    age_min: int = Field(default=12, ge=0, le=120)
    age_max: int = Field(default=15, ge=0, le=120)
    locale: str = "zh-CN"
    context_domains: tuple[str, ...] = Field(
        default_factory=lambda: (
            "classroom",
            "group_work",
            "peer",
            "family",
            "club",
            "online",
        )
    )
    instruction_zh: str = "如果是你，你最可能怎么做？"
    prompt_version: str = "v2.0-demo"

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator(
        "title", "population", "locale", "instruction_zh", "prompt_version"
    )
    @classmethod
    def validate_nonblank_fields(cls, value: str) -> str:
        return _validate_nonblank(value)

    @field_validator("context_domains")
    @classmethod
    def validate_context_domains(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("context_domains must not be empty")
        return _validate_identifier_collection(values)

    @model_validator(mode="after")
    def validate_age_range(self) -> "ProjectConfig":
        if self.age_min > self.age_max:
            raise ValueError("age_min must not exceed age_max")
        return self


class ConstructAnchor(BaseModel):
    model_config = ConfigDict(frozen=True)

    anchor_id: str
    item_number: int
    text_zh: str
    legacy_feature: str
    domain_id: str
    facet_id: str
    reverse: bool
    source: str = "legacy_big_five_60"

    @field_validator("anchor_id")
    @classmethod
    def validate_anchor_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @model_validator(mode="after")
    def validate_taxonomy_provenance(self) -> "ConstructAnchor":
        _validate_taxonomy_pair(self.domain_id, self.facet_id)
        if LEGACY_FEATURE_MAP.get(self.legacy_feature) != self.facet_id:
            raise ValueError("legacy_feature must map exactly to facet_id")
        return self


class ConstructSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain_id: str
    facet_id: str
    anchor_ids: tuple[str, ...]
    definition_zh: str
    behavioral_indicators: tuple[str, ...]
    exclusions: tuple[str, ...]
    potential_confounds: tuple[str, ...]

    @field_validator("anchor_ids")
    @classmethod
    def validate_anchor_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_identifier_collection(values)

    @model_validator(mode="after")
    def validate_taxonomy(self) -> "ConstructSpecification":
        _validate_taxonomy_pair(self.domain_id, self.facet_id)
        return self


class ScenarioBlueprint(BaseModel):
    model_config = ConfigDict(frozen=True)

    setting: str
    actors: tuple[str, ...]
    relationship: str
    goal: str
    trigger_event: str
    decision_point: str
    context_domain: str


class ResponseOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    option_id: str
    text_zh: str
    trait_level: int = Field(ge=1, le=4)
    score: int = Field(ge=1, le=4)
    display_order: int = Field(ge=1, le=4)
    rationale: str
    desirability_note: str

    @field_validator("option_id")
    @classmethod
    def validate_option_id(cls, value: str) -> str:
        return _validate_identifier(value)


def _validate_option_set(
    options: tuple[ResponseOption, ...],
) -> tuple[ResponseOption, ...]:
    expected_levels = {1, 2, 3, 4}
    if len(options) != 4:
        raise ValueError("option sets require exactly four options")
    if {option.score for option in options} != expected_levels:
        raise ValueError("option scores must cover 1, 2, 3, and 4")
    if {option.trait_level for option in options} != expected_levels:
        raise ValueError("trait levels must cover 1, 2, 3, and 4")
    if {option.display_order for option in options} != expected_levels:
        raise ValueError("display order must cover 1, 2, 3, and 4")
    if any(option.trait_level != option.score for option in options):
        raise ValueError("trait level must equal score")

    option_ids = [option.option_id.strip() for option in options]
    if any(not option_id for option_id in option_ids):
        raise ValueError("option IDs must not be blank")
    if len(set(option_ids)) != 4:
        raise ValueError("option IDs must be unique")

    option_texts = [option.text_zh.strip() for option in options]
    if any(not option_text for option_text in option_texts):
        raise ValueError("option text must not be blank")
    if len(set(option_texts)) != 4:
        raise ValueError("option text must be unique")
    return options


class QualityCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    check_id: str
    label: str
    severity: CheckSeverity
    outcome: CheckOutcome
    evidence: str
    recommendation: str = ""


class ReviewVersion(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    created_at: _AwareIsoString = Field(default_factory=utc_now_iso)
    reviewer: str
    action: ReviewAction
    note: str
    before_stem_zh: str
    before_options: tuple[ResponseOption, ...]
    after_stem_zh: str
    after_options: tuple[ResponseOption, ...]

    @field_validator("before_options", "after_options")
    @classmethod
    def validate_option_snapshots(
        cls, options: tuple[ResponseOption, ...]
    ) -> tuple[ResponseOption, ...]:
        return _validate_option_set(options)


class CandidateItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    domain_id: str
    facet_id: str
    anchor_ids: tuple[str, ...] = Field(min_length=1)
    instruction_zh: str
    stem_zh: str
    construct_spec: ConstructSpecification | None = None
    scenario_blueprint: ScenarioBlueprint | None = None
    options: tuple[ResponseOption, ...]
    quality_checks: tuple[QualityCheck, ...] = Field(default_factory=tuple)
    evidence_status: EvidenceStatus = EvidenceStatus.MODEL_DRAFT
    generation_mode: GenerationMode = GenerationMode.CURATED
    model_id: str | None = None
    prompt_version: str = "v2.0-demo"
    created_at: _AwareIsoString = Field(default_factory=utc_now_iso)
    review_versions: tuple[ReviewVersion, ...] = Field(default_factory=tuple)

    @field_validator("item_id")
    @classmethod
    def validate_item_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("anchor_ids")
    @classmethod
    def validate_anchor_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_identifier_collection(values)

    @model_validator(mode="after")
    def validate_contract(self) -> "CandidateItem":
        _validate_option_set(self.options)

        _validate_taxonomy_pair(self.domain_id, self.facet_id)

        if self.construct_spec is not None:
            if self.construct_spec.domain_id != self.domain_id:
                raise ValueError("construct specification domain must match candidate")
            if self.construct_spec.facet_id != self.facet_id:
                raise ValueError("construct specification facet must match candidate")
            if self.construct_spec.anchor_ids != self.anchor_ids:
                raise ValueError("construct specification anchors must match candidate")
        return self


class ResearchProject(BaseModel):
    model_config = ConfigDict(frozen=True)

    config: ProjectConfig
    items: Mapping[str, CandidateItem] = Field(
        default_factory=lambda: MappingProxyType({})
    )
    selected_item_id: str | None = None
    updated_at: _AwareIsoString = Field(default_factory=utc_now_iso)

    @field_validator("items")
    @classmethod
    def freeze_items(
        cls, items: Mapping[str, CandidateItem]
    ) -> Mapping[str, CandidateItem]:
        return MappingProxyType(dict(items))

    @field_serializer("items")
    def serialize_items(
        self, items: Mapping[str, CandidateItem]
    ) -> dict[str, CandidateItem]:
        return dict(items)

    @model_validator(mode="after")
    def validate_item_references(self) -> "ResearchProject":
        if any(key != item.item_id for key, item in self.items.items()):
            raise ValueError("item keys must match item_id values")
        if self.selected_item_id is not None and self.selected_item_id not in self.items:
            raise ValueError("selected_item_id must identify an item in the project")
        return self


class GenerationMetadata(BaseModel):
    model_id: str
    prompt_version: str
    generated_at: _AwareIsoString = Field(default_factory=utc_now_iso)
    constraint_snapshot: dict[str, Any]
