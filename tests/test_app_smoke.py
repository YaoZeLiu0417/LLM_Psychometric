import csv
import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from streamlit.testing.v1 import AppTest

from psychometric_v2 import config as v2_config
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    GenerationMetadata,
    GenerationMode,
    ReviewAction,
)
from psychometric_v2.pipeline import GenerationStageError
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages import construct_map, generation, review
from psychometric_v2.workbench import WorkbenchService


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app_v2.py"
PAGES = {
    "PROJECT": (
        "2023 COLLEGE STUDENT STUDY -> 2026 ADOLESCENT RECONSTRUCTION -> FUTURE VALIDATION",
        "2023 STUDY / COLLEGE STUDENT SAMPLE",
        "Historical summary from the 2023 college-student study; raw response data are no longer available.",
    ),
    "CONSTRUCT MAP": (
        "CONSTRUCT TAXONOMY",
        "Source anchors guide content; the facet is the generation unit.",
        "SOURCE ANCHORS",
    ),
    "GENERATION STUDIO": (
        "CONSTRUCT SPECIFICATION",
        "SCENARIO BLUEPRINT",
        "RESPONSE OPTIONS",
        "QUALITY CHECKS",
        "PROVENANCE",
    ),
    "REVIEW": ("REVIEW QUEUE", "PROVENANCE", "MODEL_DRAFT"),
    "PARTICIPANT VIEW": (
        "如果是你，你最可能怎么做？",
        "新学期社团第一次活动",
    ),
}


def _generation_metadata(
    item: CandidateItem,
    *,
    model_id: str,
) -> GenerationMetadata:
    return GenerationMetadata(
        model_id=model_id,
        prompt_version=item.prompt_version,
        constraint_snapshot={
            "domain_id": item.domain_id,
            "facet_id": item.facet_id,
            "anchor_ids": list(item.anchor_ids),
        },
    )


@pytest.fixture(autouse=True)
def isolated_app_workspace(tmp_path, monkeypatch) -> Path:
    workspace = tmp_path / "workspace_data"
    monkeypatch.setattr(v2_config, "WORKSPACE_ROOT", workspace)
    return workspace


def _run_app(page: str | None = None) -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    if page is not None:
        app.session_state["v2_active_page"] = page
    return app.run()


def _markdown(app: AppTest) -> str:
    return "\n".join(element.value for element in app.markdown)


def _header_markup(app: AppTest) -> str:
    return next(
        element.value
        for element in app.markdown
        if '<header class="top-shell">' in element.value
    )


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def _widget_with_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


def _install_successful_live_pipeline(monkeypatch, candidate) -> None:
    class SuccessfulPipeline:
        def __init__(self, _client) -> None:
            pass

        def generate_candidate(self, _config, _anchor, _context):
            return candidate

    monkeypatch.setattr(
        generation.LiveModelConfig,
        "from_env",
        staticmethod(lambda: object()),
    )
    monkeypatch.setattr(generation, "OpenAICompatibleClient", lambda _config: object())
    monkeypatch.setattr(generation, "GenerationPipeline", SuccessfulPipeline)


def test_app_starts_without_live_model_configuration(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    assert APP_PATH.is_file(), "Task6 app_v2.py must exist"
    app = _run_app()

    assert not app.exception
    markdown = _markdown(app)
    assert "Adolescent Big Five" in markdown
    for hidden_badge in ("CURATED DEMO", "LIVE AVAILABLE", "LIVE UNAVAILABLE"):
        assert hidden_badge not in markdown


def test_project_page_preserves_required_evidence_boundaries() -> None:
    app = _run_app("PROJECT")

    assert not app.exception
    markdown = _markdown(app)
    for expected in PAGES["PROJECT"]:
        assert expected in markdown
    header = _header_markup(app)
    assert markdown.count('<header class="top-shell">') == 1
    assert markdown.count(build_demo_project().config.title) == 1
    assert "project-band" not in markdown
    for expected in (
        "AGE 12-15",
        "LOCALE zh-CN",
        "Mainland Chinese junior-secondary students",
    ):
        assert expected in header
    for hidden_copy in (
        "ACTIVE RESEARCH PROJECT",
        "Candidate item development - empirical validation required",
        "Candidate item development — empirical validation required",
        "CURATED DEMO",
        "2023 EMPIRICAL STUDY -> 2026 RECONSTRUCTION -> "
        "ADOLESCENT BEHAVIORAL PHENOTYPES",
        "ARCHIVED 2023 EVIDENCE",
        "Openness item-total r",
        "Archived slide summary; raw participant data unavailable",
        "not evidence for V2",
    ):
        assert hidden_copy not in markdown
    assert "sample size" not in markdown.lower()

    metrics = {(metric.label, str(metric.value)) for metric in app.metric}
    assert metrics == {
        ("SOURCE ANCHORS", "60"),
        ("FACETS", "15"),
        ("DOMAINS", "5"),
        ("REFERENCE ITEMS", "5"),
        ("VALIDATED ITEMS", "0"),
    }


def test_project_curated_candidate_metric_excludes_live_items() -> None:
    app = AppTest.from_string(
        """
from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.models import GenerationMetadata, GenerationMode
from psychometric_v2.ui.pages.project import render

project = build_demo_project()
base = project.items[project.selected_item_id]
live = base.validated_update(
    item_id="live-project-metric",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-model",
    generation_metadata=GenerationMetadata(
        model_id="fake-model",
        prompt_version=base.prompt_version,
        constraint_snapshot={},
    ),
)
expanded = project.validated_update(
    items={**dict(project.items), live.item_id: live},
    selected_item_id=live.item_id,
)
render(expanded, load_anchor_asset(ANCHOR_ASSET), None)
        """
    ).run()

    assert not app.exception
    metric = next(
        metric
        for metric in app.metric
        if metric.label == "REFERENCE ITEMS"
    )
    assert str(metric.value) == "5"


def test_each_page_can_be_loaded_from_preset_session_state() -> None:
    for page, expected_content in PAGES.items():
        app = _run_app(page)

        assert not app.exception, page
        markdown = _markdown(app)
        assert app.session_state["v2_active_page"] == page
        for expected in expected_content:
            assert expected in markdown, (page, expected)


@pytest.mark.parametrize(
    "page",
    ("CONSTRUCT MAP", "GENERATION STUDIO", "REVIEW", "PARTICIPANT VIEW"),
)
def test_non_project_headers_omit_project_metadata(page: str) -> None:
    app = _run_app(page)

    assert not app.exception
    header = _header_markup(app)
    assert 'class="top-meta"' not in header
    for metadata in (
        "AGE 12-15",
        "LOCALE zh-CN",
        "Mainland Chinese junior-secondary students",
    ):
        assert metadata not in header


def test_project_metadata_uses_compact_weighted_spans() -> None:
    app = _run_app("PROJECT")

    assert not app.exception
    theme_markup = app.markdown[0].value
    assert re.search(
        r"\.top-meta span \{\s*font-size: 13px;\s*font-weight: 650;",
        theme_markup,
    )


def test_project_and_generation_evidence_notes_have_distinct_presentations() -> None:
    project = _run_app("PROJECT")
    generation = AppTest.from_file(str(APP_PATH), default_timeout=10)
    generation.session_state["v2_active_page"] = "GENERATION STUDIO"
    generation.session_state["v2_active_stage"] = "QUALITY CHECKS"
    generation.run()

    assert not project.exception
    assert not generation.exception
    project_note = next(
        element.value
        for element in project.markdown
        if "Historical summary from the 2023 college-student study" in element.value
    )
    generation_note = next(
        element.value
        for element in generation.markdown
        if "Automated checks are advisory; human review is required." in element.value
    )
    assert 'class="project-evidence-footnote"' in project_note
    assert 'class="evidence-note"' in generation_note

    theme_markup = project.markdown[0].value
    project_style = re.search(
        r"\.project-evidence-footnote \{(?P<body>.*?)\}",
        theme_markup,
        re.DOTALL,
    )
    warning_style = re.search(
        r"\.evidence-note \{(?P<body>.*?)\}",
        theme_markup,
        re.DOTALL,
    )
    assert project_style is not None
    assert warning_style is not None
    assert "color: var(--muted);" in project_style.group("body")
    assert "font-size: 13px;" in project_style.group("body")
    assert "margin-top: 10px;" in project_style.group("body")
    assert "border-left: 4px solid var(--orange);" in warning_style.group("body")
    assert "padding: 8px 12px;" in warning_style.group("body")


def test_construct_map_renders_responsive_svg_wheel() -> None:
    app = _run_app("CONSTRUCT MAP")

    assert not app.exception
    wheel_element = next(
        element
        for element in app.markdown
        if "construct-wheel" in element.value
    )
    assert wheel_element.proto.allow_html is True
    wheel_markup = wheel_element.value
    root = ET.fromstring(wheel_markup)
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    assert root.attrib["class"] == "construct-wheel"
    assert root.attrib["viewBox"] == "0 0 600 600"
    assert root.attrib["data-outer-radius"] == "292"
    assert root.attrib["data-domain-radius"] == "123"
    assert len(root.findall("svg:path", namespace)) == 20
    assert len(root.findall(".//svg:title", namespace)) == 20


@pytest.mark.parametrize(
    ("reverse", "expected_class", "expected_label"),
    (
        (True, "status-badge status-flag", "REVERSE KEYED"),
        (False, "status-badge status-review", "FORWARD KEYED"),
    ),
)
def test_construct_map_source_markup_is_continuous_and_escaped(
    reverse: bool,
    expected_class: str,
    expected_label: str,
) -> None:
    anchor = ConstructAnchor.model_construct(
        anchor_id="anchor-<unsafe>",
        item_number=1,
        text_zh="<script>alert('x')</script>",
        legacy_feature="Sociability",
        domain_id="extraversion",
        facet_id="sociability",
        reverse=reverse,
    )

    markup = construct_map._source_list_markup((anchor,))

    assert re.search(r"(?m)^[ \t]{4,}<", markup) is None
    assert markup.count('<div class="source-row">') == 1
    assert "anchor-&lt;unsafe&gt;" in markup
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in markup
    assert f'<span class="{expected_class}">{expected_label}</span>' in markup


def test_construct_map_renders_all_source_anchors_without_code_markup() -> None:
    app = _run_app("CONSTRUCT MAP")

    assert not app.exception
    source_markup = next(
        element.value
        for element in app.markdown
        if '<div class="source-list">' in element.value
    )
    assert re.search(r"(?m)^[ \t]{4,}<", source_markup) is None
    assert source_markup.count('<div class="source-row">') == 4
    for item_number in range(1, 5):
        assert f"bfi2-sociability-{item_number:02d}" in source_markup


def test_navigation_survives_reruns_and_writes_active_page() -> None:
    app = _run_app("PROJECT")
    navigation = app.get("button_group")[0]

    assert not app.exception
    assert navigation.key == "v2_navigation"
    assert app.session_state["v2_active_page"] == "PROJECT"

    app.run()
    assert not app.exception
    assert app.session_state["v2_active_page"] == "PROJECT"

    app.get("button_group")[0].set_value(["REVIEW"]).run()
    assert not app.exception
    assert app.session_state["v2_active_page"] == "REVIEW"
    assert "REVIEW QUEUE" in _markdown(app)

    app.run()
    assert not app.exception
    assert app.session_state["v2_active_page"] == "REVIEW"


def test_review_queue_and_participant_view_keep_roles_separate() -> None:
    review = _run_app("REVIEW")
    assert len(review.dataframe) == 1
    assert len(review.dataframe[0].value) == 5

    participant = _run_app("PARTICIPANT VIEW")
    assert len(participant.radio) == 1
    assert len(participant.radio[0].options) == 4
    participant_text = _markdown(participant).lower()
    for hidden_term in ("score", "trait", "anchor", "provenance", "profile"):
        assert hidden_term not in participant_text


def test_participant_preview_collects_only_option_ids_across_five_items() -> None:
    project = build_demo_project()
    items = tuple(project.items.values())
    app = _run_app("PARTICIPANT VIEW")

    for index, item in enumerate(items):
        assert not app.exception
        assert f"{index + 1} / {len(items)}" in _markdown(app)
        assert item.instruction_zh in _markdown(app)
        assert item.stem_zh in _markdown(app)
        assert len(app.radio) == 1
        ordered_options = tuple(
            sorted(item.options, key=lambda option: option.display_order)
        )
        assert tuple(app.radio[0].options) == tuple(
            option.text_zh for option in ordered_options
        )

        selected = ordered_options[index % len(ordered_options)]
        app.radio[0].set_value(selected.option_id).run()
        responses = dict(app.session_state["v2_participant_responses"])
        assert responses[item.item_id] == selected.option_id
        assert all(isinstance(option_id, str) for option_id in responses.values())
        assert all(
            option_id in {
                option.option_id
                for candidate in items
                for option in candidate.options
            }
            for option_id in responses.values()
        )

        next_button = _button(app, "→")
        assert next_button.help == "Next item"
        next_button.click().run()

    assert not app.exception
    assert "Preview complete" in _markdown(app)
    assert "Responses remain in this session only" in _markdown(app)
    assert len(app.radio) == 0
    assert len(app.get("download_button")) == 0

    back_button = _button(app, "←")
    assert back_button.help == "Previous item"
    back_button.click().run()
    assert f"{len(items)} / {len(items)}" in _markdown(app)


def test_participant_preview_never_renders_research_metadata() -> None:
    app = _run_app("PARTICIPANT VIEW")
    rendered = _markdown(app)
    rendered += "\n" + "\n".join(
        str(option) for radio in app.radio for option in radio.options
    )

    for hidden_term in (
        "anchor_ids",
        "trait_level",
        "score",
        "Extraversion",
        "VALIDATED",
    ):
        assert hidden_term not in rendered


def test_participant_header_hides_selected_item_generation_mode() -> None:
    app = AppTest.from_string(
        """
import streamlit as st

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMetadata, GenerationMode
from psychometric_v2.ui.components import render_header
from psychometric_v2.ui.pages.participant import render
from psychometric_v2.ui.state import init_state

seed = build_demo_project()
curated = seed.items[seed.selected_item_id]
live = curated.validated_update(
    item_id="live-selected-before-participant",
    stem_zh="LIVE STEM MUST NOT BE SHOWN",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-model",
    generation_metadata=GenerationMetadata(
        model_id="fake-model",
        prompt_version=curated.prompt_version,
        constraint_snapshot={},
    ),
)
project = seed.validated_update(
    items={**dict(seed.items), live.item_id: live},
    selected_item_id=live.item_id,
)
init_state()
st.session_state["v2_active_page"] = "PARTICIPANT VIEW"
st.session_state["v2_selected_item"] = live.item_id
render_header(project)
render(project, {}, None)
        """
    ).run()

    assert not app.exception
    markdown = _markdown(app)
    header = _header_markup(app)
    assert "CURATED DEMO" not in header
    assert "LIVE GENERATION" not in header
    assert "LIVE STEM MUST NOT BE SHOWN" not in markdown
    assert "新学期社团第一次活动" in markdown


def test_participant_uses_edited_project_from_isolated_workspace(
    isolated_app_workspace,
) -> None:
    repository = JsonProjectRepository(isolated_app_workspace / "v2" / "projects")
    project = repository.ensure_seed(build_demo_project())
    item = project.items[project.selected_item_id]
    edited_options = tuple(
        option.validated_update(
            text_zh=(
                "隔离项目中的已编辑选项"
                if option.display_order == 1
                else option.text_zh
            )
        )
        for option in item.options
    )
    WorkbenchService(repository).review_item(
        project.config.project_id,
        item.item_id,
        "隔离项目中的已编辑题干",
        edited_options,
        "smoke-test-reviewer",
        ReviewAction.EDIT,
        "prove smoke tests do not read the runtime workspace",
        expected_version=len(item.review_versions),
    )

    app = _run_app("PARTICIPANT VIEW")

    assert not app.exception
    markdown = _markdown(app)
    assert "隔离项目中的已编辑题干" in markdown
    assert "隔离项目中的已编辑选项" in app.radio[0].options
    assert "1 / 5" in markdown


def test_participant_reports_unavailable_when_project_has_no_curated_items() -> None:
    app = AppTest.from_string(
        """
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMetadata, GenerationMode
from psychometric_v2.ui.pages.participant import render
from psychometric_v2.ui.state import init_state

seed = build_demo_project()
base = seed.items[seed.selected_item_id]
live = base.validated_update(
    item_id="live-only-item",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-model",
    generation_metadata=GenerationMetadata(
        model_id="fake-model",
        prompt_version=base.prompt_version,
        constraint_snapshot={},
    ),
)
project = seed.validated_update(
    items={live.item_id: live},
    selected_item_id=live.item_id,
)
init_state()
render(project, {}, None)
        """
    ).run()

    assert not app.exception
    assert len(app.info) == 1
    assert app.info[0].value == "Preview unavailable"
    assert "Preview complete" not in _markdown(app)


def test_research_downloads_are_review_only_and_exclude_preview_responses(
    monkeypatch,
) -> None:
    captured: dict[str, tuple[bytes, str]] = {}

    def capture_download(
        label,
        data,
        *,
        file_name,
        mime,
        **_kwargs,
    ):
        captured[file_name] = (bytes(data), mime)
        return False

    monkeypatch.setattr(review.st, "download_button", capture_download)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "REVIEW"
    app.session_state["v2_participant_responses"] = {
        "demo-extraversion-sociability": "__session_only_response__"
    }
    app.run()

    assert not app.exception
    assert set(captured) == {
        "adolescent_big_five_demo.json",
        "adolescent_big_five_items.csv",
    }
    json_bytes, json_mime = captured["adolescent_big_five_demo.json"]
    csv_bytes, csv_mime = captured["adolescent_big_five_items.csv"]
    assert json_mime == "application/json"
    assert csv_mime == "text/csv"

    payload = json.loads(json_bytes.decode("utf-8"))
    first_item = next(iter(payload["items"].values()))
    assert first_item["anchor_ids"]
    assert first_item["construct_spec"]["anchor_ids"] == first_item["anchor_ids"]
    assert first_item["scenario_blueprint"]
    assert first_item["quality_checks"]
    assert "participant" not in json_bytes.decode("utf-8").lower()
    assert "__session_only_response__" not in json_bytes.decode("utf-8")

    csv_rows = list(
        csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""))
    )
    assert len(csv_rows) == 20
    assert "participant" not in csv_bytes.decode("utf-8-sig").lower()

    participant = _run_app("PARTICIPANT VIEW")
    assert len(participant.get("download_button")) == 0


def test_research_download_projection_remains_a_five_item_demo() -> None:
    project = build_demo_project()
    base = project.items[project.selected_item_id]
    live = base.validated_update(
        item_id="live-item-not-in-demo-export",
        generation_mode=GenerationMode.LIVE,
        model_id="fake-model",
        generation_metadata=_generation_metadata(
            base,
            model_id="fake-model",
        ),
    )
    expanded = project.validated_update(
        items={**dict(project.items), live.item_id: live},
        selected_item_id=live.item_id,
    )

    exported = review.demo_export_project(expanded)

    assert len(exported.items) == 5
    assert live.item_id not in exported.items
    assert exported.selected_item_id in exported.items
    csv_rows = list(
        csv.DictReader(
            io.StringIO(
                review.project_csv_bytes(exported).decode("utf-8-sig"),
                newline="",
            )
        )
    )
    assert len(csv_rows) == 20


def test_v2_launcher_and_readme_document_the_stable_demo_contract() -> None:
    launcher = ROOT / "run_v2.ps1"
    readme = ROOT / "README_V2.md"

    assert launcher.read_text(encoding="utf-8").splitlines() == [
        '$ErrorActionPreference = "Stop"',
        "$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path",
        "Set-Location -LiteralPath $repoRoot",
        "python -m streamlit run app_v2.py --server.port 8501 --server.headless true",
    ]

    documentation = readme.read_text(encoding="utf-8")
    for expected in (
        "python -m pip install -r requirements-v2.txt",
        "powershell -ExecutionPolicy Bypass -File .\\run_v2.ps1",
        "python -m pytest",
        "OPENAI_API_KEY",
        "LLM_MODEL",
        "OPENAI_BASE_URL",
        "CURATED DEMO",
        "2023 research lineage",
        "12-15",
        "scenario blueprint",
        "behavioral options",
        "provenance",
        "quality flags",
        "human edit",
        "participant preview",
        "construct-module roadmap",
        "research/demo workbench",
        "psychometric validation",
        "diagnosis",
        "individual personality inference",
    ):
        assert expected in documentation


def test_status_palette_and_responsive_breakpoints_are_exposed() -> None:
    review = _run_app("REVIEW")
    status_markup = [
        element.value
        for element in review.markdown
        if "<span" in element.value and "status-badge" in element.value
    ]
    assert any("status-model-draft" in value for value in status_markup)

    theme_markup = review.markdown[0].value
    expected_status_colors = {
        "status-model-draft": "#24A8D8",
        "status-needs-revision": "#F28C28",
        "status-human-reviewed": "#D81B78",
        "status-pilot-candidate": "#40358C",
    }
    for class_name, color in expected_status_colors.items():
        assert f".{class_name} {{ background: {color};" in theme_markup
    assert "@media (max-width: 1280px)" in theme_markup
    assert "@media (max-width: 600px)" in theme_markup


def test_theme_stacks_source_rows_at_narrow_viewports() -> None:
    app = _run_app("CONSTRUCT MAP")

    assert not app.exception
    theme_markup = app.markdown[0].value
    narrow_source_rule = """@media (max-width: 900px) {
    .source-row { grid-template-columns: 1fr; gap: 4px; }
}"""
    assert narrow_source_rule in theme_markup


def test_theme_hides_streamlit_chrome_without_reserving_top_space() -> None:
    app = _run_app("PARTICIPANT VIEW")

    assert not app.exception
    theme_markup = app.markdown[0].value
    chrome_rule = """[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"],
#MainMenu {
    display: none !important;
}"""
    assert chrome_rule in theme_markup
    desktop_container_rule = """[data-testid="stMainBlockContainer"] {
    max-width: 1480px;
    padding: 0 2rem 3rem;
}"""
    assert desktop_container_rule in theme_markup
    assert (
        '[data-testid="stMainBlockContainer"] { '
        'padding-right: 1.25rem; padding-left: 1.25rem; }'
    ) in theme_markup
    assert (
        '[data-testid="stMainBlockContainer"] { padding: 0 .9rem 2rem; }'
    ) in theme_markup
    assert ".main .block-container" not in theme_markup


def test_provenance_renders_taxonomy_all_anchors_and_evidence_status() -> None:
    app = AppTest.from_string(
        """
from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.ui.components import render_provenance

project = build_demo_project()
base = project.items[project.selected_item_id]
anchor_ids = ("bfi2-sociability-01", "bfi2-sociability-02")
spec = base.construct_spec.validated_update(anchor_ids=anchor_ids)
item = base.validated_update(anchor_ids=anchor_ids, construct_spec=spec)
render_provenance(item=item, anchors=load_anchor_asset(ANCHOR_ASSET))
        """
    ).run()

    assert not app.exception
    markdown = _markdown(app)
    assert "extraversion" in markdown
    assert "sociability" in markdown
    assert "bfi2-sociability-01" in markdown
    assert "我是一个性格外向，喜欢交际的人。" in markdown
    assert "FORWARD KEYED" in markdown
    assert "bfi2-sociability-02" in markdown
    assert "我是一个比较安静的人。" in markdown
    assert "REVERSE KEYED" in markdown
    assert "v2.0-demo" in markdown
    assert "CURATED SEED" in markdown
    assert any(
        "status-model-draft" in element.value and "MODEL_DRAFT" in element.value
        for element in app.markdown
    )


def test_provenance_html_has_no_indented_markdown_code_blocks() -> None:
    app = AppTest.from_string(
        """
from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.ui.components import render_provenance

project = build_demo_project()
base = project.items[project.selected_item_id]
anchor_ids = ("bfi2-sociability-01", "bfi2-sociability-02")
spec = base.construct_spec.validated_update(anchor_ids=anchor_ids)
item = base.validated_update(anchor_ids=anchor_ids, construct_spec=spec)
render_provenance(item=item, anchors=load_anchor_asset(ANCHOR_ASSET))
        """
    ).run()

    assert not app.exception
    trace_markup = next(
        element.value for element in app.markdown if "trace-record" in element.value
    )
    source_markup = next(
        element.value for element in app.markdown if "source-list" in element.value
    )
    for markup in (trace_markup, source_markup):
        assert re.search(r"(?m)^[ \t]{4,}<", markup) is None
    assert trace_markup.count('<div class="trace-cell">') == 4
    assert source_markup.count('<div class="source-row">') == 2
    for anchor_id in ("bfi2-sociability-01", "bfi2-sociability-02"):
        assert anchor_id in source_markup


def test_generation_uses_compact_provenance_while_review_stays_standard() -> None:
    generation_app = _run_app("GENERATION STUDIO")

    assert not generation_app.exception
    generation_markup = _markdown(generation_app)
    theme_markup = generation_app.markdown[0].value
    assert 'class="trace-grid trace-grid--compact"' in generation_markup
    assert 'class="source-list source-list--compact"' in generation_markup
    assert """.trace-grid.trace-grid--compact {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}""" in theme_markup
    assert """.source-list.source-list--compact .source-row {
    grid-template-columns: 1fr;
    gap: 4px;
}""" in theme_markup

    review_app = _run_app("REVIEW")

    assert not review_app.exception
    review_markup = _markdown(review_app)
    assert 'class="trace-grid trace-grid--compact"' not in review_markup
    assert 'class="source-list source-list--compact"' not in review_markup
    assert 'class="trace-grid"' in review_markup
    assert 'class="source-list"' in review_markup
    assert "grid-template-columns: 150px minmax(0, 1fr) 120px;" in theme_markup


def test_v2_ui_actions_do_not_depend_on_material_icon_tokens() -> None:
    app = _run_app("GENERATION STUDIO")

    assert not app.exception
    for label in ("GENERATE", "LOAD CURATED EXAMPLE"):
        button = _button(app, label)
        assert not button.proto.icon
        assert ":material/" not in str(button.proto)

    ui_root = ROOT / "psychometric_v2" / "ui"
    material_tokens = {
        str(path.relative_to(ui_root)): source.count(":material/")
        for path in sorted(ui_root.rglob("*.py"))
        if ":material/" in (source := path.read_text(encoding="utf-8"))
    }
    assert material_tokens == {}


def test_provenance_shows_safe_fallback_for_missing_anchor() -> None:
    app = AppTest.from_string(
        """
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.ui.components import render_provenance

project = build_demo_project()
base = project.items[project.selected_item_id]
anchor_ids = ("missing-source-anchor",)
spec = base.construct_spec.validated_update(anchor_ids=anchor_ids)
item = base.validated_update(anchor_ids=anchor_ids, construct_spec=spec)
render_provenance(item=item, anchors={})
        """
    ).run()

    assert not app.exception
    markdown = _markdown(app)
    assert "missing-source-anchor" in markdown
    assert "SOURCE ANCHOR UNAVAILABLE" in markdown


def test_generation_studio_exposes_stages_and_safe_curated_fallback(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    def forbidden_live_initialization(*_args, **_kwargs):
        raise AssertionError("disabled generation must not initialize a live client")

    monkeypatch.setattr(
        generation.LiveModelConfig,
        "from_env",
        staticmethod(forbidden_live_initialization),
    )
    monkeypatch.setattr(
        generation,
        "OpenAICompatibleClient",
        forbidden_live_initialization,
    )
    app = _run_app("GENERATION STUDIO")

    assert not app.exception
    text = _markdown(app)
    for stage in (
        "CONSTRUCT SPECIFICATION",
        "SCENARIO BLUEPRINT",
        "RESPONSE OPTIONS",
        "QUALITY CHECKS",
    ):
        assert stage in text
    assert _button(app, "GENERATE").disabled is True
    assert _button(app, "LOAD CURATED EXAMPLE").disabled is False
    assert _widget_with_key(app.selectbox, "v2_context_domain").value == "club"
    assert _widget_with_key(app.selectbox, "v2_selected_anchor").value == (
        "bfi2-sociability-01"
    )
    assert all(
        widget.key.startswith("v2_")
        for widgets in (app.selectbox, app.button)
        for widget in widgets
    )

    app.run()
    app.run()
    assert not app.exception
    assert _button(app, "GENERATE").disabled is True
    assert "PROVENANCE" in _markdown(app)

    _button(app, "LOAD CURATED EXAMPLE").click().run()
    assert not app.exception
    assert app.session_state["v2_generation_mode"] == "CURATED DEMO"
    assert app.session_state["v2_construct_spec"].facet_id == "sociability"
    assert app.session_state["v2_scenario_blueprint"].context_domain == "club"
    assert app.session_state["v2_candidate_item"].item_id == (
        "demo-extraversion-sociability"
    )
    assert app.session_state["v2_selected_item"] == "demo-extraversion-sociability"


def test_curated_example_requires_exact_anchor_and_context_match() -> None:
    seed = build_demo_project().items["demo-extraversion-sociability"]
    app = _run_app("GENERATION STUDIO")

    assert seed.construct_spec.definition_zh in _markdown(app)
    _widget_with_key(app.selectbox, "v2_selected_anchor").set_value(
        "bfi2-sociability-02"
    ).run()

    assert not app.exception
    assert _button(app, "LOAD CURATED EXAMPLE").disabled is True
    assert seed.construct_spec.definition_zh not in _markdown(app)

    _widget_with_key(app.selectbox, "v2_selected_anchor").set_value(
        "bfi2-sociability-01"
    ).run()
    _widget_with_key(app.selectbox, "v2_context_domain").set_value(
        "classroom"
    ).run()

    assert not app.exception
    assert _button(app, "LOAD CURATED EXAMPLE").disabled is True
    assert seed.construct_spec.definition_zh not in _markdown(app)


def test_generation_provenance_inspector_lists_all_options_and_checks() -> None:
    seed = build_demo_project().items["demo-extraversion-sociability"]
    app = _run_app("GENERATION STUDIO")
    markdown = _markdown(app)

    assert not app.exception
    for option in seed.options:
        assert option.option_id in markdown
        assert option.text_zh in markdown
        assert option.rationale in markdown
    for check in seed.quality_checks:
        assert check.check_id in markdown
        assert check.label in markdown
        assert check.outcome.value in markdown
        assert check.severity.value in markdown
        assert check.evidence in markdown
        assert (check.recommendation or "No change recommended.") in markdown


def test_live_success_commits_session_only_after_persistence(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    seed = build_demo_project().items["demo-extraversion-sociability"]
    generated = seed.validated_update(
        item_id="live-sociability-saved",
        generation_mode=GenerationMode.LIVE,
        model_id="fake-app-test-model",
        generation_metadata=_generation_metadata(
            seed,
            model_id="fake-app-test-model",
        ),
    )
    _install_successful_live_pipeline(monkeypatch, generated)
    observed: dict[str, object] = {}

    def successful_save(_service, _project_id, _candidate):
        observed["candidate"] = generation.st.session_state.get("v2_candidate_item")
        observed["selected"] = generation.st.session_state.get("v2_selected_item")
        observed["statuses"] = dict(
            generation.st.session_state.get("v2_stage_status", {})
        )

    monkeypatch.setattr(
        generation.WorkbenchService,
        "save_generated_item",
        successful_save,
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "GENERATION STUDIO"
    app.session_state["v2_generation_mode"] = "LIVE GENERATION"
    app.session_state["v2_candidate_item"] = seed
    app.session_state["v2_selected_item"] = seed.item_id
    app.session_state["v2_stage_status"] = {
        stage: "CURATED"
        for stage in (
            "CONSTRUCT SPECIFICATION",
            "SCENARIO BLUEPRINT",
            "RESPONSE OPTIONS",
            "QUALITY CHECKS",
        )
    }
    app.run()

    _button(app, "GENERATE").click().run()

    assert not app.exception
    assert observed["candidate"] is None
    assert observed["selected"] == seed.item_id
    assert set(observed["statuses"].values()) == {"CURATED"}
    assert app.session_state["v2_candidate_item"].item_id == generated.item_id
    assert app.session_state["v2_selected_item"] == generated.item_id
    assert set(app.session_state["v2_stage_status"].values()) == {"COMPLETE"}


@pytest.mark.parametrize("persistence_error", (ValueError, KeyError, OSError))
def test_live_persistence_failure_restores_session_and_is_public(
    monkeypatch,
    persistence_error,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    seed = build_demo_project().items["demo-extraversion-sociability"]
    generated = seed.validated_update(
        item_id="live-sociability-not-saved",
        generation_mode=GenerationMode.LIVE,
        model_id="fake-app-test-model",
        generation_metadata=_generation_metadata(
            seed,
            model_id="fake-app-test-model",
        ),
    )
    _install_successful_live_pipeline(monkeypatch, generated)

    def failed_save(_service, _project_id, _candidate):
        raise persistence_error("SECRET C:\\private\\project.json")

    monkeypatch.setattr(
        generation.WorkbenchService,
        "save_generated_item",
        failed_save,
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "GENERATION STUDIO"
    app.session_state["v2_generation_mode"] = "LIVE GENERATION"
    app.session_state["v2_candidate_item"] = seed
    app.session_state["v2_selected_item"] = seed.item_id
    app.session_state["v2_stage_status"] = {
        stage: "CURATED"
        for stage in (
            "CONSTRUCT SPECIFICATION",
            "SCENARIO BLUEPRINT",
            "RESPONSE OPTIONS",
            "QUALITY CHECKS",
        )
    }
    app.run()

    _button(app, "GENERATE").click().run()

    assert not app.exception
    assert app.error[0].value == "Generated item could not be saved."
    assert "SECRET" not in _markdown(app)
    assert "private" not in _markdown(app)
    assert app.session_state["v2_candidate_item"].item_id == seed.item_id
    assert app.session_state["v2_selected_item"] == seed.item_id
    assert app.session_state["v2_generation_options"].item_id == generated.item_id
    assert app.session_state["v2_stage_status"]["QUALITY CHECKS"] == "NOT SAVED"
    assert set(app.session_state["v2_stage_status"].values()) != {"COMPLETE"}

    app.run()
    assert not app.exception
    assert app.error[0].value == "Generated item could not be saved."
    assert app.session_state["v2_candidate_item"].item_id == seed.item_id
    assert app.session_state["v2_selected_item"] == seed.item_id


def test_generation_uses_latest_persisted_curated_item(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
import streamlit as st
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.models import ReviewAction
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.generation import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
service = WorkbenchService(repository)
item = project.items["demo-extraversion-sociability"]
if not item.review_versions:
    options = tuple(
        option.validated_update(
            text_zh="PERSISTED REVIEW OPTION" if index == 0 else option.text_zh
        )
        for index, option in enumerate(item.options)
    )
    project = service.review_item(
        project.config.project_id,
        item.item_id,
        "PERSISTED REVIEW STEM",
        options,
        "reviewer-a",
        ReviewAction.APPROVE,
        "persisted review note",
        expected_version=len(item.review_versions),
    )
init_state()
st.session_state["v2_active_stage"] = "RESPONSE OPTIONS"
render(project, load_anchor_asset(ANCHOR_ASSET), service)
        """,
        default_timeout=10,
    ).run()

    assert not app.exception
    markdown = _markdown(app)
    assert "PERSISTED REVIEW STEM" in markdown
    assert "PERSISTED REVIEW OPTION" in markdown
    assert "HUMAN_REVIEWED" in markdown

    _button(app, "LOAD CURATED EXAMPLE").click().run()
    assert not app.exception
    loaded = app.session_state["v2_candidate_item"]
    assert loaded.stem_zh == "PERSISTED REVIEW STEM"
    assert loaded.options[0].text_zh == "PERSISTED REVIEW OPTION"
    assert loaded.evidence_status.value == "HUMAN_REVIEWED"
    assert len(loaded.review_versions) == 1


def test_construct_failure_does_not_reuse_previous_live_candidate(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    seed = build_demo_project().items["demo-extraversion-sociability"]
    old_live = seed.validated_update(
        item_id="live-sociability-previous",
        generation_mode=GenerationMode.LIVE,
        model_id="previous-live-model",
        generation_metadata=_generation_metadata(
            seed,
            model_id="previous-live-model",
        ),
    )

    class ConstructFailingPipeline:
        def __init__(self, _client) -> None:
            pass

        def generate_candidate(self, _config, _anchor, _context):
            raise GenerationStageError(
                "construct",
                "The construct stage returned invalid structured data.",
                partial_results={},
            )

    monkeypatch.setattr(
        generation.LiveModelConfig,
        "from_env",
        staticmethod(lambda: object()),
    )
    monkeypatch.setattr(generation, "OpenAICompatibleClient", lambda _config: object())
    monkeypatch.setattr(
        generation,
        "GenerationPipeline",
        ConstructFailingPipeline,
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "GENERATION STUDIO"
    app.session_state["v2_generation_mode"] = "LIVE GENERATION"
    app.session_state["v2_active_stage"] = "RESPONSE OPTIONS"
    app.session_state["v2_construct_spec"] = old_live.construct_spec
    app.session_state["v2_scenario_blueprint"] = old_live.scenario_blueprint
    app.session_state["v2_generation_options"] = old_live
    app.session_state["v2_candidate_item"] = old_live
    app.session_state["v2_selected_item"] = old_live.item_id
    app.run()

    assert old_live.stem_zh in _markdown(app)
    _button(app, "GENERATE").click().run()

    assert not app.exception
    assert app.error[0].value == (
        "The construct stage returned invalid structured data."
    )
    assert app.session_state["v2_candidate_item"] is None
    assert app.session_state["v2_stage_status"]["CONSTRUCT SPECIFICATION"] == (
        "ERROR"
    )
    assert app.session_state["v2_stage_status"]["SCENARIO BLUEPRINT"] == "NOT RUN"
    assert app.session_state["v2_stage_status"]["RESPONSE OPTIONS"] == "NOT RUN"
    assert app.session_state["v2_stage_status"]["QUALITY CHECKS"] == "NOT RUN"
    assert old_live.stem_zh not in _markdown(app)
    for option in old_live.options:
        assert option.text_zh not in _markdown(app)

    app.run()
    assert not app.exception
    assert app.session_state["v2_candidate_item"] is None
    assert old_live.stem_zh not in _markdown(app)


def test_live_failure_preserves_partial_stages_and_curated_fallback(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    seed = build_demo_project().items["demo-extraversion-sociability"]
    partial_candidate = seed.validated_update(
        item_id="live-sociability-partial",
        generation_mode=GenerationMode.LIVE,
        model_id="fake-app-test-model",
        generation_metadata=_generation_metadata(
            seed,
            model_id="fake-app-test-model",
        ),
    )
    calls: list[str] = []

    def fake_config():
        calls.append("config")
        return object()

    def fake_client(_config):
        calls.append("client")
        return object()

    class FailingPipeline:
        def __init__(self, _client) -> None:
            calls.append("pipeline")

        def generate_candidate(self, _config, _anchor, _context):
            calls.append("generate_candidate")
            raise GenerationStageError(
                "quality",
                "The quality stage returned invalid structured data.",
                partial_results={
                    "construct": partial_candidate.construct_spec,
                    "blueprint": partial_candidate.scenario_blueprint,
                    "candidate": partial_candidate,
                    "options": partial_candidate,
                    "raw": "SECRET RAW RESPONSE",
                },
            )

    monkeypatch.setattr(
        generation.LiveModelConfig,
        "from_env",
        staticmethod(fake_config),
    )
    monkeypatch.setattr(generation, "OpenAICompatibleClient", fake_client)
    monkeypatch.setattr(generation, "GenerationPipeline", FailingPipeline)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    app.session_state["v2_active_page"] = "GENERATION STUDIO"
    app.session_state["v2_generation_mode"] = "LIVE GENERATION"
    app.run()

    assert not app.exception
    assert _button(app, "GENERATE").disabled is False
    assert calls == []
    _button(app, "GENERATE").click().run()

    assert not app.exception
    assert calls == ["config", "client", "pipeline", "generate_candidate"]
    assert app.error[0].value == (
        "The quality stage returned invalid structured data."
    )
    assert "SECRET RAW RESPONSE" not in _markdown(app)
    assert app.session_state["v2_construct_spec"].facet_id == "sociability"
    assert app.session_state["v2_scenario_blueprint"].context_domain == "club"
    assert app.session_state["v2_candidate_item"].item_id == (
        "live-sociability-partial"
    )
    assert app.session_state["v2_generation_options"].item_id == (
        "live-sociability-partial"
    )
    assert app.session_state["v2_stage_status"]["QUALITY CHECKS"] == "ERROR"

    _button(app, "LOAD CURATED EXAMPLE").click().run()
    assert not app.exception
    assert app.session_state["v2_generation_mode"] == "CURATED DEMO"
    assert "CURATED DEMO" not in _header_markup(app)
    assert "LIVE GENERATION" not in _header_markup(app)
    assert app.session_state["v2_candidate_item"].generation_mode is GenerationMode.CURATED
    assert app.session_state["v2_candidate_item"].item_id == (
        "demo-extraversion-sociability"
    )


def test_review_queue_editor_actions_and_reruns_are_stable() -> None:
    app = _run_app("REVIEW")

    assert not app.exception
    queue = app.dataframe[0].value
    assert len(queue) == 5
    assert list(queue.columns) == [
        "ITEM ID",
        "DOMAIN",
        "FACET",
        "CONTEXT",
        "ERRORS",
        "WARNINGS",
        "STATUS",
        "VERSIONS",
    ]
    assert _widget_with_key(app.selectbox, "v2_review_item")
    assert len(app.text_area) == 1
    assert len(
        [widget for widget in app.text_input if widget.key.startswith("v2_review_option_")]
    ) == 4
    assert any(expander.label == "RESEARCH METADATA" for expander in app.expander)
    for label in (
        "SAVE REVISION",
        "RETURN",
        "APPROVE CONTENT",
        "PROMOTE TO PILOT",
    ):
        assert _button(app, label)
    assert _button(app, "PROMOTE TO PILOT").disabled is True

    app.run()
    app.run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 5
    assert _button(app, "PROMOTE TO PILOT").disabled is True


def test_review_requires_note_before_creating_a_version() -> None:
    app = _run_app("REVIEW")
    before = app.dataframe[0].value.copy()
    _widget_with_key(app.text_input, "v2_review_reviewer").set_value("reviewer-a")

    _button(app, "SAVE REVISION").click().run()

    assert not app.exception
    assert app.error
    assert "Reviewer and note are required." in app.error[0].value
    assert app.dataframe[0].value.equals(before)


def test_review_actions_persist_through_isolated_service(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.review import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
init_state()
render(project, load_anchor_asset(ANCHOR_ASSET), WorkbenchService(repository))
        """,
        default_timeout=10,
    ).run()
    _widget_with_key(app.text_input, "v2_review_reviewer").set_value("reviewer-a")
    _widget_with_key(app.text_input, "v2_review_note").set_value("content approved")

    _button(app, "APPROVE CONTENT").click().run()

    assert not app.exception
    queue = app.dataframe[0].value
    selected_id = app.session_state["v2_review_item"]
    selected = queue.loc[queue["ITEM ID"] == selected_id].iloc[0]
    assert selected["STATUS"] == "HUMAN_REVIEWED"
    assert selected["VERSIONS"] == 1
    assert _button(app, "PROMOTE TO PILOT").disabled is False


def test_review_passively_conflicts_when_external_review_keeps_options(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.review import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
init_state()
render(project, load_anchor_asset(ANCHOR_ASSET), WorkbenchService(repository))
        """,
        default_timeout=10,
    ).run()
    selected_id = app.session_state["v2_review_item"]
    stale_stem = "Unsaved editor stem"
    _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).set_value(stale_stem)

    repository = JsonProjectRepository(repository_root)
    persisted = repository.load(build_demo_project().config.project_id)
    item = persisted.items[selected_id]
    external_stem = "Externally approved stem"
    externally_updated = WorkbenchService(repository).review_item(
        persisted.config.project_id,
        selected_id,
        external_stem,
        item.options,
        "reviewer-b",
        ReviewAction.APPROVE,
        "external approval",
        expected_version=0,
    )
    external_item = externally_updated.items[selected_id]

    app.run()

    assert not app.exception
    assert [error.value for error in app.error] == [
        "This item has a newer saved version. "
        "Reload the current version before continuing."
    ]
    assert app.session_state["v2_review_base_version"] == 0
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == stale_stem
    for option in item.options:
        assert _widget_with_key(
            app.text_input,
            f"v2_review_option_{selected_id}_{option.option_id}",
        ).value == option.text_zh
    for label in (
        "SAVE REVISION",
        "RETURN",
        "APPROVE CONTENT",
        "PROMOTE TO PILOT",
    ):
        assert _button(app, label).disabled is True
    selected = app.dataframe[0].value.loc[
        lambda queue: queue["ITEM ID"] == selected_id
    ].iloc[0]
    assert selected["STATUS"] == "HUMAN_REVIEWED"
    assert selected["VERSIONS"] == 1
    assert "VERSION 1 / APPROVE" in _markdown(app)
    after_conflict = repository.load(persisted.config.project_id).items[selected_id]
    assert after_conflict == external_item

    _button(app, "RELOAD CURRENT VERSION").click().run()

    assert not app.exception
    assert not app.error
    assert app.session_state["v2_review_base_version"] == 1
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == external_stem
    for label in (
        "SAVE REVISION",
        "RETURN",
        "APPROVE CONTENT",
        "PROMOTE TO PILOT",
    ):
        assert _button(app, label).disabled is False
    after_reload = repository.load(persisted.config.project_id).items[selected_id]
    assert after_reload == after_conflict


def test_review_rejects_stale_editor_and_reloads_current_version(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.review import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
init_state()
render(project, load_anchor_asset(ANCHOR_ASSET), WorkbenchService(repository))
        """,
        default_timeout=10,
    ).run()
    selected_id = app.session_state["v2_review_item"]
    stale_stem = "Stale editor revision"
    external_stem = "Externally persisted revision"
    _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).set_value(stale_stem)
    _widget_with_key(app.text_input, "v2_review_reviewer").set_value("reviewer-a")
    _widget_with_key(app.text_input, "v2_review_note").set_value("stale save")

    repository = JsonProjectRepository(repository_root)
    persisted = repository.load(build_demo_project().config.project_id)
    item = persisted.items[selected_id]
    WorkbenchService(repository).review_item(
        persisted.config.project_id,
        selected_id,
        external_stem,
        item.options,
        "reviewer-b",
        ReviewAction.EDIT,
        "external save",
        expected_version=0,
    )

    _button(app, "SAVE REVISION").click().run()

    assert not app.exception
    assert app.error
    assert app.error[0].value == (
        "This item has a newer saved version. "
        "Reload the current version before continuing."
    )
    assert app.session_state["v2_review_base_version"] == 0
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == stale_stem
    after_conflict = repository.load(persisted.config.project_id).items[selected_id]
    assert len(after_conflict.review_versions) == 1
    assert after_conflict.stem_zh == external_stem
    assert after_conflict.review_versions[0].note == "external save"

    _button(app, "RELOAD CURRENT VERSION").click().run()

    assert not app.exception
    assert not app.error
    assert app.session_state["v2_review_hydrated_item"] == selected_id
    assert app.session_state["v2_review_base_version"] == 1
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == external_stem
    after_reload = repository.load(persisted.config.project_id).items[selected_id]
    assert after_reload == after_conflict


def test_review_rejects_stale_editor_when_external_options_change(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.review import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
init_state()
render(project, load_anchor_asset(ANCHOR_ASSET), WorkbenchService(repository))
        """,
        default_timeout=10,
    ).run()
    selected_id = app.session_state["v2_review_item"]
    stale_stem = "Stale editor revision"
    _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).set_value(stale_stem)
    _widget_with_key(app.text_input, "v2_review_reviewer").set_value("reviewer-a")
    _widget_with_key(app.text_input, "v2_review_note").set_value("stale save")

    repository = JsonProjectRepository(repository_root)
    persisted = repository.load(build_demo_project().config.project_id)
    item = persisted.items[selected_id]
    external_stem = "Externally persisted stem and options"
    external_options = tuple(
        option.validated_update(
            option_id=f"external-choice-{option.score}",
            text_zh=f"External option {option.score}",
            display_order=5 - option.display_order,
        )
        for option in item.options
    )
    externally_updated = WorkbenchService(repository).review_item(
        persisted.config.project_id,
        selected_id,
        external_stem,
        external_options,
        "reviewer-b",
        ReviewAction.EDIT,
        "external save",
        expected_version=0,
    )
    external_item = externally_updated.items[selected_id]

    _button(app, "SAVE REVISION").click().run()

    assert not app.exception
    assert [error.value for error in app.error] == [
        "This item has a newer saved version. "
        "Reload the current version before continuing."
    ]
    assert app.session_state["v2_review_base_version"] == 0
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == stale_stem
    for option in item.options:
        assert _widget_with_key(
            app.text_input,
            f"v2_review_option_{selected_id}_{option.option_id}",
        ).value == option.text_zh

    after_conflict = repository.load(persisted.config.project_id).items[selected_id]
    assert len(after_conflict.review_versions) == 1
    assert after_conflict.stem_zh == external_stem
    assert after_conflict.options == external_options
    assert after_conflict.review_versions[0].note == "external save"
    assert after_conflict == external_item

    _button(app, "RELOAD CURRENT VERSION").click().run()

    assert not app.exception
    assert not app.error
    assert app.session_state["v2_review_base_version"] == 1
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == external_stem
    rendered_options = [
        option
        for option in app.text_input
        if option.key.startswith(f"v2_review_option_{selected_id}_")
    ]
    expected_options = sorted(external_options, key=lambda option: option.display_order)
    assert [option.key for option in rendered_options] == [
        f"v2_review_option_{selected_id}_{option.option_id}"
        for option in expected_options
    ]
    assert [option.value for option in rendered_options] == [
        option.text_zh for option in expected_options
    ]
    after_reload = repository.load(persisted.config.project_id).items[selected_id]
    assert after_reload == after_conflict


def test_review_repeated_stale_save_keeps_single_conflict_control(tmp_path) -> None:
    repository_root = tmp_path / "projects"
    app = AppTest.from_string(
        f"""
from pathlib import Path

from psychometric_v2.config import ANCHOR_ASSET
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
from psychometric_v2.ui.pages.review import render
from psychometric_v2.ui.state import init_state
from psychometric_v2.workbench import WorkbenchService

repository = JsonProjectRepository(Path({str(repository_root)!r}))
project = repository.ensure_seed(build_demo_project())
init_state()
render(project, load_anchor_asset(ANCHOR_ASSET), WorkbenchService(repository))
        """,
        default_timeout=10,
    ).run()
    selected_id = app.session_state["v2_review_item"]
    stale_stem = "Stale editor revision"
    external_stem = "Externally persisted revision"
    _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).set_value(stale_stem)
    _widget_with_key(app.text_input, "v2_review_reviewer").set_value("reviewer-a")
    _widget_with_key(app.text_input, "v2_review_note").set_value("stale save")

    repository = JsonProjectRepository(repository_root)
    persisted = repository.load(build_demo_project().config.project_id)
    item = persisted.items[selected_id]
    WorkbenchService(repository).review_item(
        persisted.config.project_id,
        selected_id,
        external_stem,
        item.options,
        "reviewer-b",
        ReviewAction.EDIT,
        "external save",
        expected_version=0,
    )

    _button(app, "SAVE REVISION").click().run()
    _button(app, "SAVE REVISION").click().run()

    assert not app.exception
    assert [error.value for error in app.error] == [
        "This item has a newer saved version. "
        "Reload the current version before continuing."
    ]
    assert len(
        [button for button in app.button if button.key == "v2_review_reload_current"]
    ) == 1
    assert app.session_state["v2_review_base_version"] == 0
    assert _widget_with_key(
        app.text_area,
        f"v2_review_stem_{selected_id}",
    ).value == stale_stem
    after_conflict = repository.load(persisted.config.project_id).items[selected_id]
    assert len(after_conflict.review_versions) == 1
    assert after_conflict.stem_zh == external_stem
    assert after_conflict.review_versions[0].note == "external save"


def test_review_header_never_exposes_selected_item_generation_mode() -> None:
    app = AppTest.from_string(
        """
import streamlit as st

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMetadata, GenerationMode
from psychometric_v2.ui.components import render_header
from psychometric_v2.ui.pages.review import render, sync_selected_item_from_review
from psychometric_v2.ui.state import init_state

seed = build_demo_project()
curated = seed.items[seed.selected_item_id]
live = curated.validated_update(
    item_id="live-review-selection",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-live-model",
    generation_metadata=GenerationMetadata(
        model_id="fake-live-model",
        prompt_version=curated.prompt_version,
        constraint_snapshot={},
    ),
)
project = seed.validated_update(
    items={curated.item_id: curated, live.item_id: live},
    selected_item_id=curated.item_id,
)
init_state()
st.session_state["v2_active_page"] = "REVIEW"
sync_selected_item_from_review(project)
render_header(project)
render(project, {}, None)
        """,
        default_timeout=10,
    ).run()

    assert not app.exception
    assert "CURATED DEMO" not in _header_markup(app)
    assert "LIVE GENERATION" not in _header_markup(app)
    _widget_with_key(app.selectbox, "v2_review_item").set_value(
        "live-review-selection"
    ).run()

    assert not app.exception
    assert "CURATED DEMO" not in _header_markup(app)
    assert "LIVE GENERATION" not in _header_markup(app)

    _widget_with_key(app.selectbox, "v2_review_item").set_value(
        "demo-extraversion-sociability"
    ).run()
    assert not app.exception
    assert "CURATED DEMO" not in _header_markup(app)
    assert "LIVE GENERATION" not in _header_markup(app)


def test_header_never_exposes_live_generation_mode() -> None:
    app = AppTest.from_string(
        """
import streamlit as st

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMetadata, GenerationMode
from psychometric_v2.ui.components import render_header

project = build_demo_project()
base = project.items[project.selected_item_id]
live_item = base.validated_update(
    item_id="live-review-candidate",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-live-model",
    generation_metadata=GenerationMetadata(
        model_id="fake-live-model",
        prompt_version=base.prompt_version,
        constraint_snapshot={},
    ),
)
live_project = project.validated_update(
    items={**dict(project.items), live_item.item_id: live_item},
    selected_item_id=live_item.item_id,
)
st.session_state["v2_active_page"] = "REVIEW"
render_header(live_project)
        """
    ).run()

    assert not app.exception
    header = _header_markup(app)
    assert "LIVE GENERATION" not in header
    assert "CURATED DEMO" not in header
