import json
import os
from pathlib import Path
from threading import Event, Thread, current_thread

import pytest

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import (
    EvidenceStatus,
    GenerationMetadata,
    GenerationMode,
    ResearchProject,
    ReviewAction,
    ReviewVersion,
)
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.taxonomy import FACETS


EXPECTED_ITEMS = (
    {
        "item_id": "demo-extraversion-sociability",
        "domain_id": "extraversion",
        "facet_id": "sociability",
        "anchor_id": "bfi2-sociability-01",
        "context_domain": "club",
        "setting": "新学期社团第一次小组活动",
        "actors": ("你", "几位不同班的同学"),
        "relationship": "初次见面的同龄人",
        "goal": "完成分组并开始活动",
        "trigger_event": "老师让大家自行认识并组成三人小组",
        "decision_point": "决定如何进入同伴互动",
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
        "context_domain": "group_work",
        "setting": "课堂小组方案讨论",
        "actors": ("你", "小组同学"),
        "relationship": "共同完成任务的同伴",
        "goal": "确定小组展示方案",
        "trigger_event": "一位同学提出了与你不同的方案",
        "decision_point": "决定如何表达分歧",
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
        "context_domain": "classroom",
        "setting": "一周内有多项学习任务",
        "actors": ("你",),
        "relationship": "个人任务管理",
        "goal": "按时完成作业、测验准备和小组材料",
        "trigger_event": "发现三项任务集中在同一周截止",
        "decision_point": "决定如何安排开始顺序",
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
        "context_domain": "classroom",
        "setting": "课堂展示临时返工",
        "actors": ("你", "任课老师"),
        "relationship": "学生与教师",
        "goal": "第二天完成修改后的展示",
        "trigger_event": "老师临时要求重做一个关键部分",
        "decision_point": "决定如何面对突然增加的不确定性",
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
        "context_domain": "classroom",
        "setting": "科学课实验结果异常",
        "actors": ("你", "实验搭档"),
        "relationship": "共同实验的同伴",
        "goal": "理解实验结果",
        "trigger_event": "实验结果与课本预测不一致",
        "decision_point": "决定如何处理异常结果",
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


def make_reviewed_project() -> ResearchProject:
    seed = build_demo_project()
    first_item = next(iter(seed.items.values()))
    reviewed_item = first_item.validated_update(
        evidence_status=EvidenceStatus.HUMAN_REVIEWED,
        review_versions=(
            ReviewVersion(
                version=1,
                reviewer="reviewer-1",
                action=ReviewAction.EDIT,
                note="保留人工审核内容",
                before_stem_zh=first_item.stem_zh,
                before_options=first_item.options,
                after_stem_zh="人工审核后的题干",
                after_options=first_item.options,
            ),
        ),
    )
    return seed.validated_update(
        items={**dict(seed.items), reviewed_item.item_id: reviewed_item}
    )


def test_demo_seed_has_exact_curated_content_and_provenance() -> None:
    project = build_demo_project()

    assert project.config.project_id == "adolescent-big-five-demo"
    assert project.config.title == "Adolescent Big Five Situational Judgment Workbench"
    assert tuple(project.items) == tuple(row["item_id"] for row in EXPECTED_ITEMS)
    assert project.selected_item_id == EXPECTED_ITEMS[0]["item_id"]
    assert len(project.items) == 5
    assert {item.domain_id for item in project.items.values()} == {
        "extraversion",
        "agreeableness",
        "conscientiousness",
        "negative_emotionality",
        "open_mindedness",
    }

    for expected, item in zip(EXPECTED_ITEMS, project.items.values(), strict=True):
        assert item.item_id == expected["item_id"]
        assert item.domain_id == expected["domain_id"]
        assert item.facet_id == expected["facet_id"]
        assert item.anchor_ids == (expected["anchor_id"],)
        assert item.stem_zh == expected["stem_zh"]
        assert item.evidence_status.value == "MODEL_DRAFT"
        assert item.generation_mode.value == "CURATED DEMO"
        assert item.generation_metadata is None
        assert item.review_versions == ()

        spec = item.construct_spec
        assert spec is not None
        assert spec.domain_id == item.domain_id
        assert spec.facet_id == item.facet_id
        assert spec.anchor_ids == item.anchor_ids
        assert spec.definition_zh == FACETS[item.facet_id].definition_zh
        assert spec.behavioral_indicators == tuple(
            option.rationale for option in item.options if option.score in {3, 4}
        )
        assert spec.exclusions == ("学业能力高低", "道德好坏评价")
        assert spec.potential_confounds == expected["confounds"]

        blueprint = item.scenario_blueprint
        assert blueprint is not None
        assert blueprint.setting == expected["setting"]
        assert blueprint.actors == expected["actors"]
        assert blueprint.relationship == expected["relationship"]
        assert blueprint.goal == expected["goal"]
        assert blueprint.trigger_event == expected["trigger_event"]
        assert blueprint.decision_point == expected["decision_point"]
        assert blueprint.context_domain == expected["context_domain"]

        assert tuple(
            (option.option_id, option.text_zh, option.score, option.rationale)
            for option in item.options
        ) == expected["options"]
        assert [option.display_order for option in item.options] == [1, 2, 3, 4]
        assert all(option.trait_level == option.score for option in item.options)
        assert all(
            option.desirability_note
            == "各选项均为可理解的行为选择，不代表道德正确性"
            for option in item.options
        )
        assert all(
            check.outcome.value == "PASS"
            for check in item.quality_checks
            if check.severity.value == "ERROR"
        )


def test_repository_round_trip_is_lossless(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path / "projects")
    project = build_demo_project()

    destination = repository.save(project)
    restored = repository.load(project.config.project_id)

    assert destination == repository.path_for(project.config.project_id)
    assert destination.read_text(encoding="utf-8") == project.model_dump_json(indent=2)
    assert restored == project
    assert not list(destination.parent.glob(f".{destination.name}.*.tmp"))


def test_repository_round_trip_preserves_live_generation_metadata(
    tmp_path: Path,
) -> None:
    repository = JsonProjectRepository(tmp_path / "projects")
    project = build_demo_project()
    base = project.items[project.selected_item_id]
    metadata = GenerationMetadata(
        model_id="fake-model",
        prompt_version=base.prompt_version,
        constraint_snapshot={
            "project_config": project.config.model_dump(mode="json"),
            "domain_id": base.domain_id,
            "facet_id": base.facet_id,
            "anchor_ids": list(base.anchor_ids),
            "context_domain": base.scenario_blueprint.context_domain,
        },
    )
    live = base.validated_update(
        item_id="live-repository-round-trip",
        generation_mode=GenerationMode.LIVE,
        model_id=metadata.model_id,
        generation_metadata=metadata,
    )
    expanded = project.validated_update(
        items={**dict(project.items), live.item_id: live},
        selected_item_id=live.item_id,
    )

    repository.save(expanded)
    restored = repository.load(project.config.project_id)

    assert restored.items[live.item_id].generation_metadata == metadata
    assert restored == expanded


def test_repository_loads_legacy_curated_json_without_generation_metadata(
    tmp_path: Path,
) -> None:
    repository = JsonProjectRepository(tmp_path / "projects")
    project = build_demo_project()
    payload = project.model_dump(mode="json")
    for item in payload["items"].values():
        item.pop("generation_metadata", None)
    destination = repository.path_for(project.config.project_id)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    restored = repository.load(project.config.project_id)

    assert all(item.generation_metadata is None for item in restored.items.values())


def test_save_intentionally_replaces_an_existing_project(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    original = build_demo_project()
    replacement = original.validated_update(
        updated_at="2026-07-22T12:00:00+09:00"
    )

    repository.save(original)
    repository.save(replacement)

    assert repository.load(original.config.project_id) == replacement
    assert (
        repository.path_for(original.config.project_id).read_text(encoding="utf-8")
        == replacement.model_dump_json(indent=2)
    )


def test_ensure_seed_does_not_overwrite_reviewed_content(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    reviewed = make_reviewed_project()
    repository.save(reviewed)

    ensured = repository.ensure_seed()

    assert ensured == reviewed
    assert next(iter(ensured.items.values())).review_versions[0].note == "保留人工审核内容"


def test_concurrent_ensure_seed_loser_loads_reviewed_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = JsonProjectRepository(tmp_path)
    reviewed = make_reviewed_project()
    unreviewed = build_demo_project()
    reviewed_published = Event()
    real_link = os.link
    returned: dict[str, ResearchProject] = {}
    failures: list[BaseException] = []

    def ordered_link(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        if current_thread().name == "reviewed-publisher":
            real_link(source, destination)
            reviewed_published.set()
            return
        if not reviewed_published.wait(timeout=5):
            raise TimeoutError("reviewed publisher did not reach atomic publication")
        real_link(source, destination)

    def ensure(name: str, project: ResearchProject) -> None:
        try:
            returned[name] = repository.ensure_seed(project)
        except BaseException as exc:
            failures.append(exc)

    monkeypatch.setattr("psychometric_v2.repository.os.link", ordered_link)
    seed_thread = Thread(
        target=ensure,
        args=("seed", unreviewed),
        name="seed-publisher",
    )
    reviewed_thread = Thread(
        target=ensure,
        args=("reviewed", reviewed),
        name="reviewed-publisher",
    )

    seed_thread.start()
    reviewed_thread.start()
    seed_thread.join(timeout=10)
    reviewed_thread.join(timeout=10)

    assert not seed_thread.is_alive()
    assert not reviewed_thread.is_alive()
    assert failures == []
    assert returned == {"seed": reviewed, "reviewed": reviewed}
    assert repository.load(reviewed.config.project_id) == reviewed
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize(
    "project_id",
    ["../escape", "..\\escape", "nested/project", "nested\\project"],
)
def test_path_for_rejects_path_traversal(tmp_path: Path, project_id: str) -> None:
    repository = JsonProjectRepository(tmp_path / "projects")

    with pytest.raises(ValueError, match="project_id"):
        repository.path_for(project_id)


def test_path_for_rejects_absolute_paths(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path / "projects")

    with pytest.raises(ValueError, match="project_id"):
        repository.path_for(str((tmp_path / "absolute").resolve()))


@pytest.mark.parametrize(
    "project_id",
    [
        "Demo-project",
        "demo-Project",
        "DEMO",
        "demo_project",
        "demo--project",
        "-demo",
        "demo-",
        "demo.project",
    ],
)
def test_repository_rejects_noncanonical_project_ids(
    tmp_path: Path, project_id: str
) -> None:
    repository = JsonProjectRepository(tmp_path)

    with pytest.raises(ValueError, match="canonical lowercase"):
        repository.path_for(project_id)


def test_save_and_load_reject_case_colliding_project_ids(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()
    uppercase_id = "Adolescent-Big-Five-Demo"
    uppercase_project = project.validated_update(
        config=project.config.validated_update(project_id=uppercase_id)
    )

    repository.save(project)

    with pytest.raises(ValueError, match="canonical lowercase"):
        repository.save(uppercase_project)
    with pytest.raises(ValueError, match="canonical lowercase"):
        repository.load(uppercase_id)
    assert repository.load(project.config.project_id) == project


def test_load_reports_missing_and_invalid_projects(tmp_path: Path) -> None:
    repository = JsonProjectRepository(tmp_path)

    with pytest.raises(FileNotFoundError, match="missing"):
        repository.load("missing")

    repository.path_for("broken").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="broken"):
        repository.load("broken")


def test_failed_atomic_replace_preserves_existing_file_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()
    destination = repository.save(project)
    original_bytes = destination.read_bytes()

    def fail_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr("psychometric_v2.repository.os.replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        repository.save(project.validated_update(updated_at="2026-07-22T12:00:00+09:00"))

    assert destination.read_bytes() == original_bytes
    assert not list(tmp_path.glob(f".{destination.name}.*.tmp"))


def test_temporary_write_failure_cleans_its_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = JsonProjectRepository(tmp_path)
    project = build_demo_project()

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr("psychometric_v2.repository.os.fsync", fail_fsync)

    with pytest.raises(OSError, match="fsync failed"):
        repository.save(project)

    assert not repository.path_for(project.config.project_id).exists()
    assert not list(tmp_path.glob(".*.tmp"))
