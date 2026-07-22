from __future__ import annotations

import html

import streamlit as st

from psychometric_v2.models import ConstructAnchor, ResearchProject
from psychometric_v2.ui.components import selected_item
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del anchors, service
    item = selected_item(project)
    ordered_options = tuple(
        option.text_zh for option in sorted(item.options, key=lambda value: value.display_order)
    )
    st.markdown('<div class="page-kicker">ASSESSMENT PREVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">PARTICIPANT VIEW</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="assessment-shell">
          <div class="assessment-index">第 1 题 / 共 {_e(len(project.items))} 题</div>
          <div class="assessment-instruction zh-content">{_e(item.instruction_zh)}</div>
          <div class="assessment-stem zh-content">{_e(item.stem_zh)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.radio(
        "请选择一个最符合你的选项",
        options=ordered_options,
        index=None,
        key="v2_participant_answer_0",
        disabled=True,
        label_visibility="collapsed",
    )
