from pathlib import Path

from streamlit.testing.v1 import AppTest


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


def test_live_button_follows_environment_without_calling_a_model(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    unavailable = _run_app("GENERATION STUDIO")

    assert not unavailable.exception
    assert len(unavailable.button) == 1
    assert unavailable.button[0].key == "v2_live_generation"
    assert unavailable.button[0].disabled is True

    monkeypatch.setenv("OPENAI_API_KEY", "fake-app-test-key")
    monkeypatch.setenv("LLM_MODEL", "fake-app-test-model")
    available = _run_app("GENERATION STUDIO")

    assert not available.exception
    assert len(available.button) == 1
    assert available.button[0].key == "v2_live_generation"
    assert available.button[0].disabled is False

    available.button[0].click().run()
    assert not available.exception
    assert available.session_state["v2_generation_mode"] == "LIVE GENERATION"
    live_text = _markdown(available)
    assert '<span class="mode-badge">LIVE GENERATION</span>' in live_text
    assert "LIVE WORKSPACE READY" in live_text
    assert "CURATED SEED" not in live_text
    assert "新学期社团第一次活动" not in live_text
    assert "主动和附近几位同学打招呼" not in live_text
    assert "PROVENANCE" not in live_text
    assert [button.key for button in available.button] == ["v2_return_curated"]

    available.run()
    assert not available.exception
    assert "CURATED SEED" not in _markdown(available)

    available.get("button_group")[0].set_value(["REVIEW"]).run()
    assert not available.exception
    assert available.session_state["v2_generation_mode"] == "LIVE GENERATION"
    review_text = _markdown(available)
    assert '<span class="mode-badge">CURATED DEMO</span>' in review_text
    assert '<span class="mode-badge">LIVE GENERATION</span>' not in review_text
    assert "CURATED SEED" in review_text
    assert "REVIEW QUEUE" in review_text

    available.get("button_group")[0].set_value(["GENERATION STUDIO"]).run()
    assert not available.exception
    assert available.session_state["v2_generation_mode"] == "LIVE GENERATION"
    resumed_text = _markdown(available)
    assert '<span class="mode-badge">LIVE GENERATION</span>' in resumed_text
    assert "LIVE WORKSPACE READY" in resumed_text
    assert "CURATED SEED" not in resumed_text

    available.button[0].click().run()
    assert not available.exception
    assert available.session_state["v2_generation_mode"] == "CURATED DEMO"
    curated_text = _markdown(available)
    assert '<span class="mode-badge">CURATED DEMO</span>' in curated_text
    assert "CURATED SEED" in curated_text
    assert "PROVENANCE" in curated_text


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
