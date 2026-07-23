from __future__ import annotations

import pandas as pd
import streamlit as st

from psychometric_v2.models import ConstructAnchor, GenerationMode, ResearchProject
from psychometric_v2.workbench import WorkbenchService


_ARCHIVED_EVIDENCE = (
    ("Conscientiousness", ".750", ".87"),
    ("Openness", ".702", ".79"),
    ("Neuroticism", ".789", ".85"),
    ("Extraversion", ".887", ".84"),
    ("Agreeableness", ".875", ".82"),
)
def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del service
    metrics = (
        ("SOURCE ANCHORS", len(anchors)),
        ("FACETS", len({anchor.facet_id for anchor in anchors.values()})),
        ("DOMAINS", len({anchor.domain_id for anchor in anchors.values()})),
        (
            "REFERENCE ITEMS",
            sum(
                item.generation_mode is GenerationMode.CURATED
                for item in project.items.values()
            ),
        ),
        ("VALIDATED ITEMS", 0),
    )
    columns = st.columns(5)
    for column, (label, value) in zip(columns, metrics, strict=True):
        column.metric(label, value)

    st.markdown(
        '<div class="lineage-band">2023 COLLEGE STUDENT STUDY -> '
        "2026 ADOLESCENT RECONSTRUCTION -> FUTURE VALIDATION</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-heading">2023 STUDY / COLLEGE STUDENT SAMPLE</div>',
        unsafe_allow_html=True,
    )
    archived = pd.DataFrame(_ARCHIVED_EVIDENCE, columns=("DOMAIN", "ALPHA", "OMEGA"))
    st.dataframe(archived, hide_index=True, use_container_width=True, height=214)
    st.markdown(
        '<div class="project-evidence-footnote">Historical summary from the 2023 college-student study; raw response data are no longer available.</div>',
        unsafe_allow_html=True,
    )
