from typing import Any

from psychometric_v2.models import (
    CandidateItem,
    ConstructSpecification,
    EvidenceStatus,
    GenerationMode,
    ProjectConfig,
    ResearchProject,
    ResponseOption,
    ScenarioBlueprint,
)
from psychometric_v2.quality import run_deterministic_checks
from psychometric_v2.taxonomy import FACETS


_DESIRABILITY_NOTE = "各选项均为可理解的行为选择，不代表道德正确性"
_EXCLUSIONS = ("学业能力高低", "道德好坏评价")
_INSTRUCTION_ZH = "如果是你，你最可能怎么做？"
_DEMO_TIMESTAMP = "2026-07-22T00:00:00+09:00"

_ITEM_ROWS: tuple[dict[str, Any], ...] = (
    {
        "item_id": "demo-extraversion-sociability",
        "domain_id": "extraversion",
        "facet_id": "sociability",
        "anchor_id": "bfi2-sociability-01",
        "setting": "新学期社团第一次小组活动",
        "actors": ("你", "几位不同班的同学"),
        "relationship": "初次见面的同龄人",
        "goal": "完成分组并开始活动",
        "trigger_event": "老师让大家自行认识并组成三人小组",
        "decision_point": "决定如何进入同伴互动",
        "context_domain": "club",
        "stem_zh": "新学期社团第一次活动，老师请大家自行认识并组成三人小组。周围大多是不同班、还不熟悉的同学。这时你最可能：",
        "confounds": ("自信表达", "社交焦虑"),
        "options": (
            ("ext-b", "先观察大家的交流，等有人邀请时再加入", 2, "被邀请后参与互动"),
            ("ext-d", "主动和附近几位同学打招呼，并邀请大家一起组队", 4, "主动发起并扩展互动"),
            ("ext-a", "先找一位看起来容易交流的同学聊几句", 3, "主动建立一对一互动"),
            ("ext-c", "先看看活动材料，等分组快结束时再决定", 1, "保持低社交发起水平"),
        ),
    },
    {
        "item_id": "demo-agreeableness-respectfulness",
        "domain_id": "agreeableness",
        "facet_id": "respectfulness",
        "anchor_id": "bfi2-respectfulness-01",
        "setting": "课堂小组方案讨论",
        "actors": ("你", "小组同学"),
        "relationship": "共同完成任务的同伴",
        "goal": "确定小组展示方案",
        "trigger_event": "一位同学提出了与你不同的方案",
        "decision_point": "决定如何表达分歧",
        "context_domain": "group_work",
        "stem_zh": "小组正在确定课堂展示方案。一位同学提出的做法与你的想法差别很大，但留给大家讨论的时间不多。这时你最可能：",
        "confounds": ("冲突回避", "自信表达"),
        "options": (
            ("agr-c", "直接说明自己方案的优势，希望大家尽快采用", 2, "表达分歧时较少协调他人观点"),
            ("agr-a", "先问清对方的理由，再说明自己的考虑并寻找可以结合的部分", 4, "在分歧中充分尊重并协调观点"),
            ("agr-d", "在对方解释时不断指出问题，坚持自己的方案更合适", 1, "较少为对方保留完整表达空间"),
            ("agr-b", "礼貌说明自己不同意的地方，然后请全组一起比较两种方案", 3, "以规范方式表达分歧"),
        ),
    },
    {
        "item_id": "demo-conscientiousness-organization",
        "domain_id": "conscientiousness",
        "facet_id": "organization",
        "anchor_id": "bfi2-organization-01",
        "setting": "一周内有多项学习任务",
        "actors": ("你",),
        "relationship": "个人任务管理",
        "goal": "按时完成作业、测验准备和小组材料",
        "trigger_event": "发现三项任务集中在同一周截止",
        "decision_point": "决定如何安排开始顺序",
        "context_domain": "classroom",
        "stem_zh": "你发现本周同时要交两份作业、准备一次小测，还要完成小组展示材料。这时你最可能：",
        "confounds": ("学习能力", "服从性"),
        "options": (
            ("con-b", "先处理截止时间最近的任务，其余任务边做边调整", 3, "有基本优先顺序"),
            ("con-d", "先做自己最想做的部分，之后再看剩余时间怎么安排", 1, "主要依即时偏好安排任务"),
            ("con-a", "列出每项任务的截止时间和所需步骤，再安排每天的进度", 4, "系统组织时间与步骤"),
            ("con-c", "记住各项截止时间，有空时选择其中一项推进", 2, "有截止意识但组织程度有限"),
        ),
    },
    {
        "item_id": "demo-negative-emotionality-anxiety",
        "domain_id": "negative_emotionality",
        "facet_id": "anxiety",
        "anchor_id": "bfi2-anxiety-01",
        "setting": "课堂展示临时返工",
        "actors": ("你", "任课老师"),
        "relationship": "学生与教师",
        "goal": "第二天完成修改后的展示",
        "trigger_event": "老师临时要求重做一个关键部分",
        "decision_point": "决定如何面对突然增加的不确定性",
        "context_domain": "classroom",
        "stem_zh": "放学前，老师告诉你明天的课堂展示有一个关键部分需要重新准备，而你原本以为已经完成了。这时你最可能：",
        "confounds": ("实际任务难度", "短暂应激"),
        "options": (
            ("neg-c", "有些担心时间不够，但先确认要求再开始修改", 2, "短暂担忧后恢复行动"),
            ("neg-a", "不断想着可能来不及，开始修改时也很难集中注意", 4, "担忧持续并干扰行动"),
            ("neg-d", "先整理需要改动的内容，按剩余时间重新安排", 1, "面对不确定性保持较低焦虑"),
            ("neg-b", "明显紧张，需要先缓一会儿才能着手处理", 3, "较强紧张并延迟行动"),
        ),
    },
    {
        "item_id": "demo-open-mindedness-curiosity",
        "domain_id": "open_mindedness",
        "facet_id": "intellectual_curiosity",
        "anchor_id": "bfi2-intellectual_curiosity-01",
        "setting": "科学课实验结果异常",
        "actors": ("你", "实验搭档"),
        "relationship": "共同实验的同伴",
        "goal": "理解实验结果",
        "trigger_event": "实验结果与课本预测不一致",
        "decision_point": "决定如何处理异常结果",
        "context_domain": "classroom",
        "stem_zh": "科学课实验结束后，你们得到的结果与课本上的预测不一致，实验步骤看起来也没有明显错误。这时你最可能：",
        "confounds": ("学科成绩", "课堂服从"),
        "options": (
            ("open-d", "记录老师给出的正确结果，不再继续追究原因", 1, "较少继续探索解释"),
            ("open-b", "重新检查关键步骤，并向老师询问可能的原因", 3, "主动检查并寻求解释"),
            ("open-a", "提出几种可能解释，查找资料并尝试设计一个小验证", 4, "扩展解释并主动验证"),
            ("open-c", "和搭档讨论哪里可能不同，然后按课堂要求完成记录", 2, "有限探索后回到既定任务"),
        ),
    },
)


def _build_item(row: dict[str, Any]) -> CandidateItem:
    options = tuple(
        ResponseOption(
            option_id=option_id,
            text_zh=text_zh,
            trait_level=score,
            score=score,
            display_order=display_order,
            rationale=rationale,
            desirability_note=_DESIRABILITY_NOTE,
        )
        for display_order, (option_id, text_zh, score, rationale) in enumerate(
            row["options"], start=1
        )
    )
    anchor_ids = (row["anchor_id"],)
    item = CandidateItem(
        item_id=row["item_id"],
        domain_id=row["domain_id"],
        facet_id=row["facet_id"],
        anchor_ids=anchor_ids,
        instruction_zh=_INSTRUCTION_ZH,
        stem_zh=row["stem_zh"],
        construct_spec=ConstructSpecification(
            domain_id=row["domain_id"],
            facet_id=row["facet_id"],
            anchor_ids=anchor_ids,
            definition_zh=FACETS[row["facet_id"]].definition_zh,
            behavioral_indicators=tuple(
                option.rationale for option in options if option.score in {3, 4}
            ),
            exclusions=_EXCLUSIONS,
            potential_confounds=row["confounds"],
        ),
        scenario_blueprint=ScenarioBlueprint(
            setting=row["setting"],
            actors=row["actors"],
            relationship=row["relationship"],
            goal=row["goal"],
            trigger_event=row["trigger_event"],
            decision_point=row["decision_point"],
            context_domain=row["context_domain"],
        ),
        options=options,
        evidence_status=EvidenceStatus.MODEL_DRAFT,
        generation_mode=GenerationMode.CURATED,
        created_at=_DEMO_TIMESTAMP,
    )
    return item.validated_update(quality_checks=run_deterministic_checks(item))


def build_demo_project() -> ResearchProject:
    items = tuple(_build_item(row) for row in _ITEM_ROWS)
    return ResearchProject(
        config=ProjectConfig(
            project_id="adolescent-big-five-demo",
            title="Adolescent Big Five Situational Judgment Workbench",
            instruction_zh=_INSTRUCTION_ZH,
        ),
        items={item.item_id: item for item in items},
        selected_item_id=items[0].item_id,
        updated_at=_DEMO_TIMESTAMP,
    )
