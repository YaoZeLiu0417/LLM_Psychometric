from __future__ import annotations

import pandas as pd
import streamlit as st

from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.ui.components import provenance_values, render_provenance, render_status, selected_item
from psychometric_v2.workbench import WorkbenchService


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del service
    selected = selected_item(project)
    st.markdown('<div class="page-kicker">EVIDENCE-AWARE CURATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">REVIEW QUEUE</div>', unsafe_allow_html=True)
    rows = []
    for item in project.items.values():
        blueprint = item.scenario_blueprint
        rows.append(
            {
                "ITEM": item.item_id,
                "DOMAIN": DOMAINS[item.domain_id].label_en,
                "FACET": FACETS[item.facet_id].label_en,
                "CONTEXT": blueprint.context_domain if blueprint is not None else "—",
                "STATUS": item.evidence_status.value,
                "VERSION": f"v{len(item.review_versions)}",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=248)
    st.markdown('<div class="section-heading">SELECTED CANDIDATE</div>', unsafe_allow_html=True)
    st.markdown(f"**{selected.item_id}** · {FACETS[selected.facet_id].label_en}")
    render_status(selected.evidence_status.value)
    render_provenance(**provenance_values(selected, anchors))
