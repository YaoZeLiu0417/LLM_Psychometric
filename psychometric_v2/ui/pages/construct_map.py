from __future__ import annotations

import html
from collections.abc import Iterable

import streamlit as st

from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.ui.construct_wheel import build_construct_wheel_svg
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _source_list_markup(anchors: Iterable[ConstructAnchor]) -> str:
    rows = "".join(
        f'<div class="source-row"><div class="source-id">{_e(anchor.anchor_id)}</div>'
        f'<div class="source-text zh-content">{_e(anchor.text_zh)}</div>'
        f'<div><span class="status-badge {"status-flag" if anchor.reverse else "status-review"}">'
        f'{"REVERSE KEYED" if anchor.reverse else "FORWARD KEYED"}</span></div></div>'
        for anchor in anchors
    )
    return f'<div class="source-list">{rows}</div>'


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del project, service
    st.markdown('<div class="page-kicker">SOURCE-ANCHORED BLUEPRINT</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">CONSTRUCT TAXONOMY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="unit-statement">Source anchors guide content; the facet is the generation unit.</div>',
        unsafe_allow_html=True,
    )
    chart_column, detail_column = st.columns((1.22, 1), gap="large")
    with chart_column:
        st.markdown(
            build_construct_wheel_svg(DOMAINS, FACETS),
            unsafe_allow_html=True,
        )
    with detail_column:
        facet_id = st.selectbox(
            "FACET",
            options=tuple(FACETS),
            format_func=lambda value: f"{FACETS[value].label_en} / {FACETS[value].label_zh}",
            key="v2_selected_facet",
        )
        facet = FACETS[facet_id]
        domain = DOMAINS[facet.domain_id]
        st.session_state["v2_selected_domain"] = facet.domain_id
        st.markdown(
            f"""
            <div class="detail-grid">
              <div class="detail-cell"><div class="field-label">DOMAIN</div><div class="detail-value">{_e(domain.label_en)} / {_e(domain.label_zh)}</div></div>
              <div class="detail-cell"><div class="field-label">FACET</div><div class="detail-value">{_e(facet.label_en)} / {_e(facet.label_zh)}</div></div>
              <div class="detail-cell"><div class="field-label">SOURCE ANCHORS</div><div class="detail-value">4</div></div>
            </div>
            <div class="tool-band">
              <div class="field-label">DEFINITION</div>
              <div class="detail-value zh-content">{_e(facet.definition_zh)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        facet_anchors = sorted(
            (anchor for anchor in anchors.values() if anchor.facet_id == facet_id),
            key=lambda anchor: anchor.item_number,
        )
        st.markdown(
            _source_list_markup(facet_anchors),
            unsafe_allow_html=True,
        )
