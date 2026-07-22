from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    project_id: str
    title: str
    population: str = "Mainland Chinese junior-secondary students"
    age_min: int = 12
    age_max: int = 15
    locale: str = "zh-CN"
    context_domains: list[str] = Field(
        default_factory=lambda: [
            "classroom",
            "group_work",
            "peer",
            "family",
            "club",
            "online",
        ]
    )
    instruction_zh: str = "如果是你，你最可能怎么做？"
    prompt_version: str = "v2.0-demo"


class ConstructAnchor(BaseModel):
    anchor_id: str
    item_number: int
    text_zh: str
    legacy_feature: str
    domain_id: str
    facet_id: str
    reverse: bool
    source: str = "legacy_big_five_60"


class ConstructSpecification(BaseModel):
    domain_id: str
    facet_id: str
    anchor_ids: list[str]
    definition_zh: str
    behavioral_indicators: list[str]
    exclusions: list[str]
    potential_confounds: list[str]


class ScenarioBlueprint(BaseModel):
    setting: str
    actors: list[str]
    relationship: str
    goal: str
    trigger_event: str
    decision_point: str
    context_domain: str


class ResponseOption(BaseModel):
    option_id: str
    text_zh: str
    trait_level: int = Field(ge=1, le=4)
    score: int = Field(ge=1, le=4)
    display_order: int = Field(ge=1, le=4)
    rationale: str
    desirability_note: str


class QualityCheck(BaseModel):
    check_id: str
    label: str
    severity: CheckSeverity
    outcome: CheckOutcome
    evidence: str
    recommendation: str = ""


class ReviewVersion(BaseModel):
    version: int
    created_at: str = Field(default_factory=utc_now_iso)
    reviewer: str
    action: ReviewAction
    note: str
    before_stem_zh: str
    before_options: list[ResponseOption]
    after_stem_zh: str
    after_options: list[ResponseOption]


class CandidateItem(BaseModel):
    item_id: str
    domain_id: str
    facet_id: str
    anchor_ids: list[str] = Field(min_length=1)
    instruction_zh: str
    stem_zh: str
    construct_spec: ConstructSpecification | None = None
    scenario_blueprint: ScenarioBlueprint | None = None
    options: list[ResponseOption]
    quality_checks: list[QualityCheck] = Field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.MODEL_DRAFT
    generation_mode: GenerationMode = GenerationMode.CURATED
    model_id: str | None = None
    prompt_version: str = "v2.0-demo"
    created_at: str = Field(default_factory=utc_now_iso)
    review_versions: list[ReviewVersion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_options(self) -> "CandidateItem":
        if len(self.options) != 4:
            raise ValueError("candidate items require exactly four options")
        if {option.score for option in self.options} != {1, 2, 3, 4}:
            raise ValueError("option scores must cover 1, 2, 3, and 4")
        if {option.display_order for option in self.options} != {1, 2, 3, 4}:
            raise ValueError("display order must cover 1, 2, 3, and 4")
        if len({option.text_zh.strip() for option in self.options}) != 4:
            raise ValueError("option text must be unique")
        return self


class ResearchProject(BaseModel):
    config: ProjectConfig
    items: dict[str, CandidateItem] = Field(default_factory=dict)
    selected_item_id: str | None = None
    updated_at: str = Field(default_factory=utc_now_iso)


class GenerationMetadata(BaseModel):
    model_id: str
    prompt_version: str
    generated_at: str = Field(default_factory=utc_now_iso)
    constraint_snapshot: dict[str, Any]
