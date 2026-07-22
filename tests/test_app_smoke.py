from pathlib import Path

from streamlit.testing.v1 import AppTest

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMode
from psychometric_v2.pipeline import GenerationStageError
from psychometric_v2.ui.pages import generation


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app_v2.py"
PAGES = {
    "PROJECT": (
        "Candidate item development — empirical validation required",
        "2023 EMPIRICAL STUDY -> 2026 RECONSTRUCTION -> ADOLESCENT BEHAVIORAL PHENOTYPES",
        "ARCHIVED 2023 EVIDENCE",
        "Openness item-total r: .455-.664",
        "Archived slide summary; raw participant data unavailable; not evidence for V2.",
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


def _run_app(page: str | None = None) -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10)
    if page is not None:
        app.session_state["v2_active_page"] = page
    return app.run()


def _markdown(app: AppTest) -> str:
    return "\n".join(element.value for element in app.markdown)


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def _widget_with_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


def test_app_starts_without_live_model_configuration(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    assert APP_PATH.is_file(), "Task6 app_v2.py must exist"
    app = _run_app()

    assert not app.exception
    markdown = _markdown(app)
    assert "Adolescent Big Five" in markdown
    assert "CURATED DEMO" in markdown


def test_project_page_preserves_required_evidence_boundaries() -> None:
    app = _run_app("PROJECT")

    assert not app.exception
    markdown = _markdown(app)
    for expected in PAGES["PROJECT"]:
        assert expected in markdown
    assert "VALIDATED" not in markdown
    assert "sample size" not in markdown.lower()

    metrics = {(metric.label, str(metric.value)) for metric in app.metric}
    assert metrics == {
        ("SOURCE ANCHORS", "60"),
        ("FACETS", "15"),
        ("DOMAINS", "5"),
        ("CURATED CANDIDATES", "5"),
        ("VALIDATED ITEMS", "0"),
    }


def test_each_page_can_be_loaded_from_preset_session_state() -> None:
    for page, expected_content in PAGES.items():
        app = _run_app(page)

        assert not app.exception, page
        markdown = _markdown(app)
        assert app.session_state["v2_active_page"] == page
        for expected in expected_content:
            assert expected in markdown, (page, expected)


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


def test_live_failure_preserves_partial_stages_and_curated_fallback(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    seed = build_demo_project().items["demo-extraversion-sociability"]
    partial_candidate = seed.validated_update(
        item_id="live-sociability-partial",
        generation_mode=GenerationMode.LIVE,
        model_id="fake-app-test-model",
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
    assert '<span class="mode-badge">CURATED DEMO</span>' in _markdown(app)
    assert '<span class="mode-badge">LIVE GENERATION</span>' not in _markdown(app)
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


def test_review_selection_updates_header_mode_in_the_same_rerun() -> None:
    app = AppTest.from_string(
        """
import streamlit as st

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMode
from psychometric_v2.ui.components import render_header
from psychometric_v2.ui.pages.review import render, sync_selected_item_from_review
from psychometric_v2.ui.state import init_state

seed = build_demo_project()
curated = seed.items[seed.selected_item_id]
live = curated.validated_update(
    item_id="live-review-selection",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-live-model",
)
project = seed.validated_update(
    items={curated.item_id: curated, live.item_id: live},
    selected_item_id=curated.item_id,
)
init_state()
st.session_state["v2_active_page"] = "REVIEW"
sync_selected_item_from_review(project)
render_header(project, live_available=True)
render(project, {}, None)
        """,
        default_timeout=10,
    ).run()

    assert not app.exception
    assert '<span class="mode-badge">CURATED DEMO</span>' in _markdown(app)
    _widget_with_key(app.selectbox, "v2_review_item").set_value(
        "live-review-selection"
    ).run()

    assert not app.exception
    assert '<span class="mode-badge">LIVE GENERATION</span>' in _markdown(app)
    assert '<span class="mode-badge">CURATED DEMO</span>' not in _markdown(app)

    _widget_with_key(app.selectbox, "v2_review_item").set_value(
        "demo-extraversion-sociability"
    ).run()
    assert not app.exception
    assert '<span class="mode-badge">CURATED DEMO</span>' in _markdown(app)
    assert '<span class="mode-badge">LIVE GENERATION</span>' not in _markdown(app)


def test_review_header_uses_selected_live_item_generation_mode() -> None:
    app = AppTest.from_string(
        """
import streamlit as st

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import GenerationMode
from psychometric_v2.ui.components import render_header

project = build_demo_project()
base = project.items[project.selected_item_id]
live_item = base.validated_update(
    item_id="live-review-candidate",
    generation_mode=GenerationMode.LIVE,
    model_id="fake-live-model",
)
live_project = project.validated_update(
    items={**dict(project.items), live_item.item_id: live_item},
    selected_item_id=live_item.item_id,
)
st.session_state["v2_active_page"] = "REVIEW"
render_header(live_project, live_available=True)
        """
    ).run()

    assert not app.exception
    markdown = _markdown(app)
    assert '<span class="mode-badge">LIVE GENERATION</span>' in markdown
    assert '<span class="mode-badge">CURATED DEMO</span>' not in markdown
