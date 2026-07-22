from __future__ import annotations

import json
from typing import Any

from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    ConstructSpecification,
    ProjectConfig,
    ScenarioBlueprint,
)


_COMMON_SYSTEM = """You support psychometric item drafting for Mainland Chinese students aged 12-15 (中国大陆 12–15 岁).
Return one JSON object only, using exactly the fields requested for this stage. Write all participant-facing content in 简体中文 and ground judgments in 可观察行为.
Do not provide chain-of-thought or hidden reasoning. Provide only concise observable rationale (简短、可观察的理由) where a rationale field is requested.
不得提供 chain-of-thought 或隐性推理。Participant-facing stems and options must not directly mention Big Five, trait, facet, construct, score, or scoring, and must not imply a morally correct answer."""


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, indent=2)


def construct_prompt(
    anchor: ConstructAnchor,
    facet: object,
    config: ProjectConfig,
) -> tuple[str, str]:
    fields = {
        "definition_zh": "string",
        "behavioral_indicators": ["string"],
        "exclusions": ["string"],
        "potential_confounds": ["string"],
    }
    user = f"""Stage: construct specification.
Population: 中国大陆 {config.age_min}–{config.age_max} 岁初中生. Locale: {config.locale}.
Selected facet: {getattr(facet, 'facet_id', facet)}.
Canonical anchor text: {anchor.text_zh}
Describe the intended construct through age-appropriate 可观察行为. Separate exclusions and likely confounds.
Return only these current-stage JSON fields:
{_json(fields)}"""
    return _COMMON_SYSTEM, user


def blueprint_prompt(
    spec: ConstructSpecification,
    config: ProjectConfig,
    context_domain: str,
) -> tuple[str, str]:
    fields = {
        "setting": "string",
        "actors": ["string"],
        "relationship": "string",
        "goal": "string",
        "trigger_event": "string",
        "decision_point": "string",
        "context_domain": "string",
    }
    user = f"""Stage: scenario blueprint.
Population: 中国大陆 {config.age_min}–{config.age_max} 岁初中生. Required context: {context_domain}.
Construct specification:
{_json(spec)}
Create an ecologically plausible everyday scenario with a concrete decision point and 可观察行为. Use 简体中文 and keep context_domain exactly {context_domain!r}.
Return only these current-stage JSON fields:
{_json(fields)}"""
    return _COMMON_SYSTEM, user


def options_prompt(
    spec: ConstructSpecification,
    blueprint: ScenarioBlueprint,
    config: ProjectConfig,
) -> tuple[str, str]:
    fields = {
        "stem_zh": "string",
        "options": [
            {
                "option_id": "string",
                "text_zh": "string",
                "trait_level": "integer 1..4",
                "score": "integer 1..4",
                "display_order": "integer 1..4",
                "rationale": "string",
                "desirability_note": "string",
            }
        ],
    }
    user = f"""Stage: participant stem and response options.
Population: 中国大陆 {config.age_min}–{config.age_max} 岁初中生. Context: {blueprint.context_domain}.
Construct specification:
{_json(spec)}
Scenario blueprint:
{_json(blueprint)}
Write one 简体中文 stem and exactly four distinct, plausible choices spanning four levels of 可观察行为. Participant-facing stem/options must not name Big Five, trait, facet, construct, score, or scoring. Keep rationale concise and observable; do not provide chain-of-thought or hidden reasoning.
Return only these current-stage JSON fields:
{_json(fields)}"""
    return _COMMON_SYSTEM, user


def quality_prompt(
    item: CandidateItem,
    config: ProjectConfig,
) -> tuple[str, str]:
    fields = {
        "checks": [
            {
                "check_id": "string",
                "label": "string",
                "severity": "INFO | WARNING | ERROR",
                "outcome": "PASS | FLAG",
                "evidence": "string",
                "recommendation": "string",
            }
        ]
    }
    user = f"""Stage: structured quality review.
Population: 中国大陆 {config.age_min}–{config.age_max} 岁初中生. Context: {item.scenario_blueprint.context_domain if item.scenario_blueprint else 'unknown'}.
Review this 简体中文 candidate using concise, 可观察 evidence only; do not provide chain-of-thought or hidden reasoning:
{_json(item)}
Return structured checks covering all of: 年龄适配, 生态合理性, 构念一致性, 混淆, 可区分性, 社会赞许性, 答案明显性, 语言复杂度, 安全.
Return only these current-stage JSON fields:
{_json(fields)}"""
    return _COMMON_SYSTEM, user
