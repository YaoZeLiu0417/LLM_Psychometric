from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class DomainDefinition:
    domain_id: str
    label_en: str
    label_zh: str
    legacy_label_zh: str
    color: str


@dataclass(frozen=True)
class FacetDefinition:
    facet_id: str
    domain_id: str
    label_en: str
    label_zh: str
    definition_zh: str


DOMAINS = MappingProxyType({
    "extraversion": DomainDefinition(
        "extraversion", "Extraversion", "外向性", "外向性", "#D81B78"
    ),
    "agreeableness": DomainDefinition(
        "agreeableness", "Agreeableness", "宜人性", "宜人性", "#24A8D8"
    ),
    "conscientiousness": DomainDefinition(
        "conscientiousness", "Conscientiousness", "尽责性", "尽责性", "#F28C28"
    ),
    "negative_emotionality": DomainDefinition(
        "negative_emotionality",
        "Negative Emotionality",
        "负性情绪",
        "神经质",
        "#E44B5F",
    ),
    "open_mindedness": DomainDefinition(
        "open_mindedness",
        "Open-Mindedness",
        "开放思维",
        "开放性",
        "#40358C",
    ),
})

_FACET_ROWS = (
    (
        "sociability",
        "extraversion",
        "Sociability",
        "社交性",
        "主动接近他人并参与社会互动的倾向。",
    ),
    (
        "assertiveness",
        "extraversion",
        "Assertiveness",
        "自信表达",
        "在群体中清楚表达观点并承担主动角色的倾向。",
    ),
    (
        "energy_level",
        "extraversion",
        "Energy Level",
        "活力",
        "以积极节奏投入活动并保持行动能量的倾向。",
    ),
    (
        "compassion",
        "agreeableness",
        "Compassion",
        "同情",
        "关注他人感受并愿意提供支持的倾向。",
    ),
    (
        "respectfulness",
        "agreeableness",
        "Respectfulness",
        "尊重",
        "在分歧中遵守互动规范并尊重他人的倾向。",
    ),
    (
        "trust",
        "agreeableness",
        "Trust",
        "信任",
        "倾向于相信他人的善意与合作意愿。",
    ),
    (
        "organization",
        "conscientiousness",
        "Organization",
        "条理",
        "有序安排材料、步骤与时间的倾向。",
    ),
    (
        "productiveness",
        "conscientiousness",
        "Productiveness",
        "效率",
        "持续推进任务并完成既定目标的倾向。",
    ),
    (
        "responsibility",
        "conscientiousness",
        "Responsibility",
        "负责",
        "履行承诺并考虑行为后果的倾向。",
    ),
    (
        "anxiety",
        "negative_emotionality",
        "Anxiety",
        "焦虑",
        "面对不确定或压力时产生担忧和紧张的倾向。",
    ),
    (
        "depression",
        "negative_emotionality",
        "Depression",
        "低落",
        "经历挫折时出现低落和退缩体验的倾向。",
    ),
    (
        "emotional_volatility",
        "negative_emotionality",
        "Emotional Volatility",
        "情绪易变",
        "情绪受到事件影响而快速或强烈变化的倾向。",
    ),
    (
        "intellectual_curiosity",
        "open_mindedness",
        "Intellectual Curiosity",
        "求知好奇",
        "主动探索解释、新知识和复杂问题的倾向。",
    ),
    (
        "aesthetic_sensitivity",
        "open_mindedness",
        "Aesthetic Sensitivity",
        "审美敏感",
        "注意并体验艺术与环境审美特征的倾向。",
    ),
    (
        "creative_imagination",
        "open_mindedness",
        "Creative Imagination",
        "创造想象",
        "形成新颖联想、设想和表达方式的倾向。",
    ),
)

FACETS = MappingProxyType(
    {row[0]: FacetDefinition(*row) for row in _FACET_ROWS}
)

LEGACY_FEATURE_MAP = MappingProxyType({
    "外向性、社交": "sociability",
    "外向性、果断": "assertiveness",
    "外向性、活力": "energy_level",
    "宜人性、同情": "compassion",
    "宜人性、谦恭": "respectfulness",
    "宜人性、信任": "trust",
    "尽责性、条理": "organization",
    "尽责性、效率": "productiveness",
    "尽责性、负责": "responsibility",
    "神经质、焦虑": "anxiety",
    "神经质、抑郁": "depression",
    "神经质、易变": "emotional_volatility",
    "开放性、好奇": "intellectual_curiosity",
    "开放性、审美": "aesthetic_sensitivity",
    "开放性、想象": "creative_imagination",
})
