from __future__ import annotations

import html

import streamlit as st

from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    GenerationMode,
    ResearchProject,
)
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _preview_items(project: ResearchProject) -> tuple[CandidateItem, ...]:
    return tuple(
        item
        for item in project.items.values()
        if item.generation_mode is GenerationMode.CURATED
    )[:5]


def _go_to(index: int) -> None:
    st.session_state["v2_participant_index"] = index
    st.rerun()


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    del anchors, service
    items = _preview_items(project)
    item_count = len(items)
    raw_index = st.session_state.get("v2_participant_index", 0)
    index = raw_index if isinstance(raw_index, int) else 0
    index = min(max(index, 0), item_count)
    st.session_state["v2_participant_index"] = index

    valid_options = {
        item.item_id: {option.option_id for option in item.options}
        for item in items
    }
    saved_responses = st.session_state.get("v2_participant_responses", {})
    responses = {
        item_id: option_id
        for item_id, option_id in (
            dict(saved_responses).items()
            if isinstance(saved_responses, dict)
            else ()
        )
        if item_id in valid_options and option_id in valid_options[item_id]
    }
    st.session_state["v2_participant_responses"] = responses

    st.markdown(
        '<div class="page-kicker">ASSESSMENT PREVIEW</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="workspace-heading">PARTICIPANT VIEW</div>',
        unsafe_allow_html=True,
    )

    if index == item_count:
        st.markdown(
            """
            <section class="assessment-shell">
              <div class="assessment-instruction">Preview complete</div>
              <div class="assessment-stem">Responses remain in this session only</div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        if item_count and st.button(
            "←",
            key="v2_participant_previous_complete",
            help="Previous item",
            type="tertiary",
        ):
            _go_to(item_count - 1)
        return

    if not items:
        st.info("Preview unavailable")
        return

    item = items[index]
    ordered_options = tuple(
        sorted(item.options, key=lambda option: option.display_order)
    )
    option_text = {option.option_id: option.text_zh for option in ordered_options}
    option_ids = tuple(option_text)
    saved_option_id = responses.get(item.item_id)
    st.markdown(
        f"""
        <section class="assessment-shell">
          <div class="assessment-index">{index + 1} / {item_count}</div>
          <div class="assessment-instruction zh-content">{_e(item.instruction_zh)}</div>
          <div class="assessment-stem zh-content">{_e(item.stem_zh)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    selected_option_id = st.radio(
        "请选择一个最符合你的选项",
        options=option_ids,
        index=(option_ids.index(saved_option_id) if saved_option_id else None),
        format_func=option_text.__getitem__,
        key=f"v2_participant_answer_{item.item_id}",
        label_visibility="collapsed",
    )
    if selected_option_id is not None and selected_option_id != saved_option_id:
        st.session_state["v2_participant_responses"] = {
            **responses,
            item.item_id: selected_option_id,
        }

    previous, next_, _spacer = st.columns([1, 1, 6], gap="small")
    with previous:
        if st.button(
            "←",
            key=f"v2_participant_previous_{index}",
            help="Previous item",
            disabled=index == 0,
            type="tertiary",
            use_container_width=True,
        ):
            _go_to(index - 1)
    with next_:
        if st.button(
            "→",
            key=f"v2_participant_next_{index}",
            help="Next item",
            disabled=selected_option_id is None,
            type="primary",
            use_container_width=True,
        ):
            _go_to(index + 1)
