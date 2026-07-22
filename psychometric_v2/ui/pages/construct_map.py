from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _taxonomy_figure() -> go.Figure:
    domain_ids = list(DOMAINS)
    facet_ids = list(FACETS)
    ids = [*domain_ids, *facet_ids]
    labels = [
        *(domain.label_en for domain in DOMAINS.values()),
        *(facet.label_en for facet in FACETS.values()),
    ]
    parents = [*("" for _ in domain_ids), *(facet.domain_id for facet in FACETS.values())]
    values = [*(3 for _ in domain_ids), *(1 for _ in facet_ids)]
    colors = [
        *(domain.color for domain in DOMAINS.values()),
        *(DOMAINS[facet.domain_id].color for facet in FACETS.values()),
    ]
    customdata = [
        *((domain.label_en, domain.label_zh) for domain in DOMAINS.values()),
        *((facet.label_en, facet.label_zh) for facet in FACETS.values()),
    ]
    figure = go.Figure(
        go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker={"colors": colors, "line": {"color": "#F7F7F5", "width": 2}},
            customdata=customdata,
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
            insidetextorientation="radial",
            sort=False,
        )
    )
    figure.update_layout(
        autosize=True,
        height=520,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="#F7F7F5",
        plot_bgcolor="#F7F7F5",
        font={"family": "Source Sans 3", "color": "#0B0B0D", "size": 14},
        uniformtext={"minsize": 11, "mode": "hide"},
    )
    return figure


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
        st.plotly_chart(
            _taxonomy_figure(),
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
            key="v2_construct_sunburst",
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
        rows = "".join(
            f"""
            <div class="source-row">
              <div class="source-id">{_e(anchor.anchor_id)}</div>
              <div class="source-text zh-content">{_e(anchor.text_zh)}</div>
              <div><span class="status-badge {'status-flag' if anchor.reverse else 'status-review'}">{'REVERSE KEYED' if anchor.reverse else 'FORWARD KEYED'}</span></div>
            </div>
            """
            for anchor in facet_anchors
        )
        st.markdown(f'<div class="source-list">{rows}</div>', unsafe_allow_html=True)
