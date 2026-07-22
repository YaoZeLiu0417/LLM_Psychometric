from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from psychometric_v2.exports import project_csv_bytes, project_json_bytes
from psychometric_v2.models import (
    CandidateItem,
    CheckOutcome,
    CheckSeverity,
    ConstructAnchor,
    EvidenceStatus,
    GenerationMode,
    ResearchProject,
    ResponseOption,
    ReviewAction,
)
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.ui.components import render_provenance, render_status
from psychometric_v2.workbench import WorkbenchService


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def demo_export_project(project: ResearchProject) -> ResearchProject:
    curated_items = dict(
        tuple(
            (item_id, item)
            for item_id, item in project.items.items()
            if item.generation_mode is GenerationMode.CURATED
        )[:5]
    )
    selected_item_id = (
        project.selected_item_id
        if project.selected_item_id in curated_items
        else next(iter(curated_items), None)
    )
    return project.validated_update(
        items=curated_items,
        selected_item_id=selected_item_id,
    )


def sync_selected_item_from_review(project: ResearchProject) -> None:
    requested = st.session_state.get("v2_review_item")
    if isinstance(requested, str) and requested in project.items:
        st.session_state["v2_selected_item"] = requested


def _queue(project: ResearchProject) -> pd.DataFrame:
    rows = []
    for item in project.items.values():
        blueprint = item.scenario_blueprint
        flagged = tuple(
            check
            for check in item.quality_checks
            if check.outcome is CheckOutcome.FLAG
        )
        rows.append(
            {
                "ITEM ID": item.item_id,
                "DOMAIN": DOMAINS[item.domain_id].label_en,
                "FACET": FACETS[item.facet_id].label_en,
                "CONTEXT": blueprint.context_domain if blueprint is not None else "-",
                "ERRORS": sum(
                    check.severity is CheckSeverity.ERROR for check in flagged
                ),
                "WARNINGS": sum(
                    check.severity is CheckSeverity.WARNING for check in flagged
                ),
                "STATUS": item.evidence_status.value,
                "VERSIONS": len(item.review_versions),
            }
        )
    return pd.DataFrame(
        rows,
        columns=(
            "ITEM ID",
            "DOMAIN",
            "FACET",
            "CONTEXT",
            "ERRORS",
            "WARNINGS",
            "STATUS",
            "VERSIONS",
        ),
    )


def _option_snapshots(
    item: CandidateItem,
    edited_text: dict[str, str],
) -> tuple[ResponseOption, ...]:
    return tuple(
        ResponseOption.model_validate(
            {
                **option.model_dump(mode="python"),
                "text_zh": edited_text[option.option_id],
            }
        )
        for option in item.options
    )


def _render_metadata(item: CandidateItem) -> None:
    with st.expander("RESEARCH METADATA", expanded=False):
        for option in sorted(item.options, key=lambda value: value.display_order):
            st.markdown(
                f"**{option.display_order}. {_e(option.option_id)}**  "
                f"Score {option.score} / Trait {option.trait_level}  \n"
                f"Rationale: {_e(option.rationale)}  \n"
                f"Desirability: {_e(option.desirability_note)}"
            )


def _render_check_trace(item: CandidateItem) -> None:
    st.markdown(
        f"""
        <div class="tool-band">
          <div class="field-label">GENERATION TIMESTAMP</div>
          <div class="detail-value">{_e(item.created_at)}</div>
          <div class="field-label">PROMPT / SOURCE</div>
          <div class="detail-value">{_e(item.prompt_version)} / {_e(item.model_id or 'Curated local seed')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-heading">CHECKS</div>', unsafe_allow_html=True)
    for check in item.quality_checks:
        st.markdown(
            f"""
            <div style="border-bottom:1px solid #D9D9D5;padding:8px 0">
              <strong>{_e(check.label)}</strong> / {_e(check.outcome.value)} / {_e(check.severity.value)}<br>
              <span class="zh-content">{_e(check.evidence)}</span><br>
              <span class="zh-content">{_e(check.recommendation or 'No change recommended.')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="section-heading">OPTION RATIONALES</div>',
        unsafe_allow_html=True,
    )
    for option in sorted(item.options, key=lambda value: value.display_order):
        st.markdown(
            f'<div class="tool-band"><div class="field-label">OPTION {option.display_order}</div>'
            f'<div class="zh-content">{_e(option.rationale)}</div></div>',
            unsafe_allow_html=True,
        )


def _options_html(options: tuple[ResponseOption, ...]) -> str:
    return "".join(
        f"<li>{option.display_order}. {_e(option.text_zh)}</li>"
        for option in sorted(options, key=lambda value: value.display_order)
    )


def _render_history(item: CandidateItem) -> None:
    st.markdown(
        '<div class="section-heading">VERSION HISTORY</div>',
        unsafe_allow_html=True,
    )
    if not item.review_versions:
        st.info("No review versions have been recorded for this item.")
        return
    for version in reversed(item.review_versions):
        st.markdown(
            f"""
            <div class="tool-band">
              <div class="field-label">VERSION {version.version} / {_e(version.action.value)}</div>
              <div class="detail-value">{_e(version.reviewer)} / {_e(version.created_at)}</div>
              <div class="field-label">NOTE</div><div>{_e(version.note)}</div>
              <div class="field-label">BEFORE STEM</div><div class="zh-content">{_e(version.before_stem_zh)}</div>
              <ol class="zh-content">{_options_html(version.before_options)}</ol>
              <div class="field-label">AFTER STEM</div><div class="zh-content">{_e(version.after_stem_zh)}</div>
              <ol class="zh-content">{_options_html(version.after_options)}</ol>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    st.markdown('<div class="page-kicker">EVIDENCE-AWARE CURATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">REVIEW QUEUE</div>', unsafe_allow_html=True)
    st.dataframe(
        _queue(project),
        hide_index=True,
        use_container_width=True,
        height=248,
    )

    item_ids = tuple(project.items)
    requested = st.session_state.get("v2_review_item")
    if requested not in item_ids:
        selected_id = st.session_state.get("v2_selected_item")
        st.session_state["v2_review_item"] = (
            selected_id if selected_id in item_ids else project.selected_item_id or item_ids[0]
        )
    item_id = st.selectbox(
        "CANDIDATE ITEM",
        item_ids,
        format_func=lambda value: (
            f"{value} / {FACETS[project.items[value].facet_id].label_en} / "
            f"{project.items[value].evidence_status.value}"
        ),
        key="v2_review_item",
    )
    st.session_state["v2_selected_item"] = item_id
    item = project.items[item_id]

    editor, trace = st.columns([1.8, 1.2], gap="large")
    with editor:
        st.markdown('<div class="section-heading">CONTENT EDITOR</div>', unsafe_allow_html=True)
        st.markdown(f"**{_e(item.item_id)}**")
        render_status(item.evidence_status)
        edited_stem = st.text_area(
            "STEM",
            value=item.stem_zh,
            height=130,
            key=f"v2_review_stem_{item.item_id}",
        )
        edited_options: dict[str, str] = {}
        for option in sorted(item.options, key=lambda value: value.display_order):
            edited_options[option.option_id] = st.text_input(
                f"OPTION {option.display_order}",
                value=option.text_zh,
                key=f"v2_review_option_{item.item_id}_{option.option_id}",
            )
        _render_metadata(item)
        reviewer = st.text_input("REVIEWER", key="v2_review_reviewer")
        note = st.text_input("REVIEW NOTE", key="v2_review_note")

        actions = st.columns(4, gap="small")
        action_clicked: ReviewAction | None = None
        action_specs = (
            ("SAVE REVISION", ReviewAction.EDIT, False),
            ("RETURN", ReviewAction.RETURN, False),
            ("APPROVE CONTENT", ReviewAction.APPROVE, False),
            (
                "PROMOTE TO PILOT",
                ReviewAction.PROMOTE_TO_PILOT,
                item.evidence_status is not EvidenceStatus.HUMAN_REVIEWED,
            ),
        )
        for column, (label, action, disabled) in zip(actions, action_specs):
            with column:
                if st.button(
                    label,
                    key=f"v2_review_{action.value.lower()}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    action_clicked = action

        if action_clicked is not None:
            if not reviewer.strip() or not note.strip():
                st.error("Reviewer and note are required.")
            else:
                try:
                    snapshots = _option_snapshots(item, edited_options)
                    service.review_item(
                        project.config.project_id,
                        item.item_id,
                        edited_stem,
                        snapshots,
                        reviewer,
                        action_clicked,
                        note,
                    )
                except (KeyError, ValueError):
                    st.error(
                        "Review could not be saved. Check the edited fields and current status."
                    )
                else:
                    st.rerun()
        _render_history(item)

    with trace:
        render_provenance(item=item, anchors=anchors)
        _render_check_trace(item)

    export_project = demo_export_project(project)
    st.markdown(
        '<div class="section-heading">RESEARCH EXPORTS</div>',
        unsafe_allow_html=True,
    )
    json_download, csv_download = st.columns(2, gap="small")
    with json_download:
        st.download_button(
            "DOWNLOAD JSON",
            data=project_json_bytes(export_project),
            file_name="adolescent_big_five_demo.json",
            mime="application/json",
            icon=":material/download:",
            on_click="ignore",
            use_container_width=True,
        )
    with csv_download:
        st.download_button(
            "DOWNLOAD CSV",
            data=project_csv_bytes(export_project),
            file_name="adolescent_big_five_items.csv",
            mime="text/csv",
            icon=":material/download:",
            on_click="ignore",
            use_container_width=True,
        )
