from __future__ import annotations

import html
from collections.abc import Mapping

import streamlit as st

from psychometric_v2.models import CandidateItem, ResearchProject


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


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_header(project: ResearchProject, *, live_available: bool) -> None:
    mode = _e(st.session_state.get("v2_generation_mode", "CURATED DEMO"))
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
    selected = st.segmented_control(
        "Workspace page",
        options=PAGES,
        key="v2_active_page",
        label_visibility="collapsed",
    )
    return selected if selected in PAGES else "PROJECT"


def _status_class(status: str) -> str:
    normalized = status.upper()
    evidence_classes = {
        "MODEL_DRAFT": "status-model-draft",
        "NEEDS_REVISION": "status-needs-revision",
        "HUMAN_REVIEWED": "status-human-reviewed",
        "PILOT_CANDIDATE": "status-pilot-candidate",
    }
    if normalized in evidence_classes:
        return evidence_classes[normalized]
    if normalized == "PASS":
        return "status-pass"
    if normalized in {"FLAG", "NEEDS_REVISION", "ERROR"}:
        return "status-flag"
    if normalized in {"HUMAN_REVIEWED", "REVIEW"}:
        return "status-review"
    return "status-model-draft"


def render_status(status: str) -> None:
    st.markdown(
        f'<span class="status-badge {_status_class(status)}">{_e(status)}</span>',
        unsafe_allow_html=True,
    )


def render_provenance(
    *,
    anchor_text: str,
    direction: str,
    prompt_version: str,
    model_id: str,
    status: str,
) -> None:
    values = (
        ("SOURCE ANCHOR", anchor_text, "zh-content"),
        ("DIRECTION", direction, ""),
        ("PROMPT", prompt_version, ""),
        ("MODEL", model_id, ""),
        ("STATUS", status, ""),
    )
    cells = "".join(
        f"""
        <div class="trace-cell">
          <div class="field-label">{_e(label)}</div>
          <div class="trace-value {_e(extra_class)}">{_e(value)}</div>
        </div>
        """
        for label, value, extra_class in values
    )
    st.markdown('<div class="section-heading">PROVENANCE</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="trace-record"><div class="trace-grid">{cells}</div></div>',
        unsafe_allow_html=True,
    )


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


def provenance_values(
    item: CandidateItem,
    anchors: Mapping[str, object],
) -> dict[str, str]:
    anchor = anchors[item.anchor_ids[0]]
    return {
        "anchor_text": str(getattr(anchor, "text_zh")),
        "direction": "REVERSE KEYED" if bool(getattr(anchor, "reverse")) else "FORWARD KEYED",
        "prompt_version": item.prompt_version,
        "model_id": item.model_id or "CURATED SEED",
        "status": item.evidence_status.value,
    }
