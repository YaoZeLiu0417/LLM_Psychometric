from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.workbench import WorkbenchService


_ARCHIVED_EVIDENCE = (
    ("Conscientiousness", ".750", ".87"),
    ("Openness", ".702", ".79"),
    ("Neuroticism", ".789", ".85"),
    ("Extraversion", ".887", ".84"),
    ("Agreeableness", ".875", ".82"),
)


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del service
    config = project.config
    st.markdown(
        f"""
        <section class="project-band">
          <div class="page-kicker">ACTIVE RESEARCH PROJECT</div>
          <h2>{_e(config.title)}</h2>
          <div class="project-meta">
            <span>AGE {_e(config.age_min)}–{_e(config.age_max)}</span>
            <span>LOCALE {_e(config.locale)}</span>
            <span>{_e(config.population)}</span>
            <span class="mode-badge">CURATED DEMO</span>
          </div>
          <div class="project-boundary">Candidate item development — empirical validation required</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    metrics = (
        ("SOURCE ANCHORS", len(anchors)),
        ("FACETS", len({anchor.facet_id for anchor in anchors.values()})),
        ("DOMAINS", len({anchor.domain_id for anchor in anchors.values()})),
        ("CURATED CANDIDATES", len(project.items)),
        ("VALIDATED ITEMS", 0),
    )
    columns = st.columns(5)
    for column, (label, value) in zip(columns, metrics, strict=True):
        column.metric(label, value)

    st.markdown(
        '<div class="lineage-band">2023 EMPIRICAL STUDY -> '
        "2026 RECONSTRUCTION -> ADOLESCENT BEHAVIORAL PHENOTYPES</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-heading">ARCHIVED 2023 EVIDENCE</div>', unsafe_allow_html=True)
    archived = pd.DataFrame(_ARCHIVED_EVIDENCE, columns=("DOMAIN", "ALPHA", "OMEGA"))
    st.dataframe(archived, hide_index=True, use_container_width=True, height=214)
    st.markdown("**Openness item-total r: .455-.664**")
    st.markdown(
        '<div class="evidence-note">Archived slide summary; raw participant data unavailable; not evidence for V2.</div>',
        unsafe_allow_html=True,
    )
