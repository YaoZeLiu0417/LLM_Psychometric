from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from psychometric_v2.config import LiveModelConfig, ModelUnavailable
from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.ui.components import (
    render_generation_stepper,
    render_provenance,
    selected_item,
)
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del service
    item = selected_item(project)
    spec = item.construct_spec
    blueprint = item.scenario_blueprint
    facet = FACETS[item.facet_id]
    domain = DOMAINS[item.domain_id]

    st.markdown('<div class="page-kicker">READ-ONLY CURATED PIPELINE</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">GENERATION STUDIO</div>', unsafe_allow_html=True)
    try:
        LiveModelConfig.from_env()
    except ModelUnavailable:
        live_available = False
    else:
        live_available = True
    if st.button(
        "ENTER LIVE MODE",
        key="v2_live_generation",
        icon=":material/bolt:",
        disabled=not live_available,
    ):
        st.session_state["v2_generation_mode"] = "LIVE GENERATION"
    st.markdown(
        '<div class="lineage-band">SOURCE ANCHOR -&gt; FACET -&gt; SPEC -&gt; BLUEPRINT -&gt; OPTIONS -&gt; CHECKS -&gt; REVIEW</div>',
        unsafe_allow_html=True,
    )
    render_generation_stepper()

    st.markdown('<div class="section-heading">CONSTRUCT SPECIFICATION</div>', unsafe_allow_html=True)
    if spec is not None:
        st.markdown(
            f"""
            <div class="detail-grid">
              <div class="detail-cell"><div class="field-label">DOMAIN</div><div class="detail-value">{_e(domain.label_en)} / {_e(domain.label_zh)}</div></div>
              <div class="detail-cell"><div class="field-label">FACET</div><div class="detail-value">{_e(facet.label_en)} / {_e(facet.label_zh)}</div></div>
              <div class="detail-cell"><div class="field-label">ANCHOR ID</div><div class="detail-value">{_e(', '.join(spec.anchor_ids))}</div></div>
            </div>
            <div class="tool-band"><div class="field-label">DEFINITION</div><div class="detail-value zh-content">{_e(spec.definition_zh)}</div></div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-heading">SCENARIO BLUEPRINT</div>', unsafe_allow_html=True)
    if blueprint is not None:
        fields = (
            ("SETTING", blueprint.setting),
            ("ACTORS", " / ".join(blueprint.actors)),
            ("RELATIONSHIP", blueprint.relationship),
            ("GOAL", blueprint.goal),
            ("TRIGGER EVENT", blueprint.trigger_event),
            ("DECISION POINT", blueprint.decision_point),
        )
        cells = "".join(
            f'<div class="detail-cell"><div class="field-label">{_e(label)}</div><div class="detail-value zh-content">{_e(value)}</div></div>'
            for label, value in fields
        )
        st.markdown(f'<div class="detail-grid">{cells}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">RESPONSE OPTIONS</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="assessment-instruction zh-content">{_e(item.instruction_zh)}</div>'
        f'<div class="assessment-stem zh-content">{_e(item.stem_zh)}</div>',
        unsafe_allow_html=True,
    )
    for option in sorted(item.options, key=lambda value: value.display_order):
        st.markdown(
            f'<div class="option-row zh-content"><strong>{_e(option.display_order)}.</strong> {_e(option.text_zh)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-heading">QUALITY CHECKS</div>', unsafe_allow_html=True)
    checks = pd.DataFrame(
        (
            {
                "CHECK": check.label,
                "OUTCOME": check.outcome.value,
                "SEVERITY": check.severity.value,
                "EVIDENCE": check.evidence,
            }
            for check in item.quality_checks
        )
    )
    st.dataframe(checks, hide_index=True, use_container_width=True, height=252)
    render_provenance(item=item, anchors=anchors)
