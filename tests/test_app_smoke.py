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
    assert "@media (max-width: 1280px)" in theme_markup
    assert "@media (max-width: 600px)" in theme_markup
