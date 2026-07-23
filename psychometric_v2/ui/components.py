from __future__ import annotations

import html
from collections.abc import Mapping

import streamlit as st

from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    EvidenceStatus,
    ResearchProject,
)
from psychometric_v2.taxonomy import DOMAINS, FACETS


PAGES = (
    "PROJECT",
    "CONSTRUCT MAP",
    "GENERATION STUDIO",
    "REVIEW",
    "PARTICIPANT VIEW",
)
STAGES = (
    "CONSTRUCT SPECIFICATION",
    "SCENARIO BLUEPRINT",
    "RESPONSE OPTIONS",
    "QUALITY CHECKS",
)


class _NavigationPage(str):
    # Streamlit 1.45 AppTest serializes button-group values as iterables.
    def __iter__(self):
        return iter((str(self),))


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _effective_page() -> str:
    navigation = st.session_state.get("v2_navigation")
    if isinstance(navigation, (list, tuple)):
        navigation = navigation[-1] if navigation else None
    if navigation in PAGES:
        return str(navigation)
    active_page = st.session_state.get("v2_active_page", PAGES[0])
    return str(active_page) if active_page in PAGES else PAGES[0]


def _effective_mode(project: ResearchProject, page: str) -> str:
    if page == "GENERATION STUDIO":
        return str(st.session_state.get("v2_generation_mode", "CURATED DEMO"))
    if page == "REVIEW":
        return selected_item(project).generation_mode.value
    return "CURATED DEMO"


def render_header(project: ResearchProject, *, live_available: bool) -> None:
    mode = _e(_effective_mode(project, _effective_page()))
    availability = "LIVE AVAILABLE" if live_available else "LIVE UNAVAILABLE"
    st.markdown(
        f"""
        <header class="top-shell">
          <div class="top-eyebrow">PSYCHOMETRIC RESEARCH WORKBENCH</div>
          <div class="top-row">
            <div>
              <div class="top-title">Adolescent Big Five</div>
              <div class="top-subtitle">{_e(project.config.title)}</div>
            </div>
            <div class="top-badges">
              <span class="mode-badge">{mode}</span>
              <span class="availability-badge">{_e(availability)}</span>
            </div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> str:
    active_page = st.session_state.get("v2_active_page", PAGES[0])
    if active_page not in PAGES:
        active_page = PAGES[0]
    options = tuple(_NavigationPage(page) for page in PAGES)
    selected = st.segmented_control(
        "Workspace page",
        options=options,
        default=active_page,
        key="v2_navigation",
        label_visibility="collapsed",
    )
    if selected in PAGES:
        selected_page = str(selected)
        st.session_state["v2_active_page"] = selected_page
        if selected_page != active_page:
            st.rerun()
        return selected_page
    return active_page


def _status_presentation(status: str | EvidenceStatus) -> tuple[str, str, str, str]:
    label = status.value if isinstance(status, EvidenceStatus) else str(status)
    normalized = label.upper()
    evidence_styles = {
        "MODEL_DRAFT": ("status-model-draft", "#24A8D8", "#0B0B0D"),
        "NEEDS_REVISION": ("status-needs-revision", "#F28C28", "#0B0B0D"),
        "HUMAN_REVIEWED": ("status-human-reviewed", "#D81B78", "#FFFFFF"),
        "PILOT_CANDIDATE": ("status-pilot-candidate", "#40358C", "#FFFFFF"),
    }
    if normalized in evidence_styles:
        class_name, background, foreground = evidence_styles[normalized]
        return label, class_name, background, foreground
    if normalized == "PASS":
        return label, "status-pass", "#DFF2E8", "#155E3D"
    if normalized in {"FLAG", "ERROR"}:
        return label, "status-flag", "#FCE5E9", "#9D1D35"
    if normalized == "REVIEW":
        return label, "status-review", "#E3F3F8", "#11617C"
    return label, "status-model-draft", "#24A8D8", "#0B0B0D"


def render_status(status: str | EvidenceStatus) -> None:
    label, class_name, background, foreground = _status_presentation(status)
    st.markdown(
        f'<span class="status-badge {_e(class_name)}" '
        f'style="background: {_e(background)}; color: {_e(foreground)}">'
        f'{_e(label)}</span>',
        unsafe_allow_html=True,
    )


def render_provenance(
    *,
    item: CandidateItem,
    anchors: Mapping[str, ConstructAnchor],
    compact: bool = False,
) -> None:
    domain = DOMAINS[item.domain_id]
    facet = FACETS[item.facet_id]
    values = (
        ("DOMAIN", f"{item.domain_id} · {domain.label_en} / {domain.label_zh}"),
        ("FACET", f"{item.facet_id} · {facet.label_en} / {facet.label_zh}"),
        ("PROMPT", item.prompt_version),
        ("MODEL", item.model_id or "CURATED SEED"),
    )
    trace_grid_class = "trace-grid trace-grid--compact" if compact else "trace-grid"
    source_list_class = (
        "source-list source-list--compact" if compact else "source-list"
    )
    cells = "".join(
        f'<div class="trace-cell">'
        f'<div class="field-label">{_e(label)}</div>'
        f'<div class="trace-value">{_e(value)}</div>'
        f'</div>'
        for label, value in values
    )
    source_rows = []
    for anchor_id in item.anchor_ids:
        anchor = anchors.get(anchor_id)
        if anchor is None:
            source_rows.append(
                f'<div class="source-row">'
                f'<div class="source-id">{_e(anchor_id)}</div>'
                f'<div class="source-text">SOURCE ANCHOR UNAVAILABLE</div>'
                f'<div><span class="status-badge status-flag">'
                f'DIRECTION UNAVAILABLE</span></div>'
                f'</div>'
            )
            continue
        direction = "REVERSE KEYED" if anchor.reverse else "FORWARD KEYED"
        direction_class = "status-flag" if anchor.reverse else "status-review"
        source_rows.append(
            f'<div class="source-row">'
            f'<div class="source-id">{_e(anchor.anchor_id)}</div>'
            f'<div class="source-text zh-content">{_e(anchor.text_zh)}</div>'
            f'<div><span class="status-badge {_e(direction_class)}">'
            f'{_e(direction)}</span></div>'
            f'</div>'
        )
    st.markdown('<div class="section-heading">PROVENANCE</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="trace-record"><div class="{trace_grid_class}">'
        f'{cells}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="{source_list_class}">{"".join(source_rows)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="field-label">STATUS</div>', unsafe_allow_html=True)
    render_status(item.evidence_status)


def render_generation_stepper(active_stage: str | None = None) -> None:
    current = active_stage or st.session_state.get("v2_active_stage", STAGES[0])
    steps = "".join(
        f"""
        <div class="stage-step{' is-active' if stage == current else ''}">
          <div class="stage-number">{index:02d}</div>
          <div class="stage-name">{_e(stage)}</div>
        </div>
        """
        for index, stage in enumerate(STAGES, start=1)
    )
    st.markdown(f'<div class="stage-grid">{steps}</div>', unsafe_allow_html=True)


def selected_item(project: ResearchProject) -> CandidateItem:
    requested = st.session_state.get("v2_selected_item")
    if isinstance(requested, str) and requested in project.items:
        return project.items[requested]
    if project.selected_item_id is not None:
        return project.items[project.selected_item_id]
    return next(iter(project.items.values()))
