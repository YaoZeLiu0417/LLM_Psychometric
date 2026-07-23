from __future__ import annotations

import html
import os

import streamlit as st

from psychometric_v2.config import LiveModelConfig, ModelUnavailable
from psychometric_v2.model_client import OpenAICompatibleClient
from psychometric_v2.models import (
    CandidateItem,
    ConstructAnchor,
    ConstructSpecification,
    GenerationMode,
    ResearchProject,
    ScenarioBlueprint,
)
from psychometric_v2.pipeline import GenerationPipeline, GenerationStageError
from psychometric_v2.taxonomy import DOMAINS, FACETS
from psychometric_v2.ui.components import STAGES, render_provenance
from psychometric_v2.workbench import WorkbenchService


_STAGE_KEYS = {
    "CONSTRUCT SPECIFICATION": "construct",
    "SCENARIO BLUEPRINT": "blueprint",
    "RESPONSE OPTIONS": "options",
    "QUALITY CHECKS": "quality",
}


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _live_environment_present() -> bool:
    return bool(
        os.getenv("OPENAI_API_KEY", "").strip()
        and os.getenv("LLM_MODEL", "").strip()
    )


def _facet_seed(
    project: ResearchProject,
    domain_id: str,
    facet_id: str,
) -> CandidateItem | None:
    for item in project.items.values():
        if (
            item.generation_mode is GenerationMode.CURATED
            and item.domain_id == domain_id
            and item.facet_id == facet_id
        ):
            return item
    return None


def _matching_seed(
    project: ResearchProject,
    domain_id: str,
    facet_id: str,
    anchor_id: str,
    context_domain: str,
) -> CandidateItem | None:
    item = _facet_seed(project, domain_id, facet_id)
    if item is None or item.scenario_blueprint is None:
        return None
    if item.anchor_ids != (anchor_id,):
        return None
    if item.scenario_blueprint.context_domain != context_domain:
        return None
    return item


def _load_curated(item: CandidateItem) -> None:
    st.session_state["v2_pending_generation_mode"] = GenerationMode.CURATED.value
    st.session_state["v2_construct_spec"] = item.construct_spec
    st.session_state["v2_scenario_blueprint"] = item.scenario_blueprint
    st.session_state["v2_generation_options"] = item
    st.session_state["v2_candidate_item"] = item
    st.session_state["v2_selected_item"] = item.item_id
    st.session_state["v2_generation_error"] = None
    st.session_state["v2_stage_status"] = {
        stage: "CURATED" for stage in STAGES
    }


def _store_partial_results(error: GenerationStageError) -> None:
    partial = error.partial_results
    construct = partial.get("construct")
    blueprint = partial.get("blueprint")
    options = partial.get("options")
    candidate = partial.get("candidate") or options
    if isinstance(construct, ConstructSpecification):
        st.session_state["v2_construct_spec"] = construct
    if isinstance(blueprint, ScenarioBlueprint):
        st.session_state["v2_scenario_blueprint"] = blueprint
    if isinstance(options, CandidateItem):
        st.session_state["v2_generation_options"] = options
    if isinstance(candidate, CandidateItem):
        st.session_state["v2_candidate_item"] = candidate

    completed = {
        "CONSTRUCT SPECIFICATION": isinstance(construct, ConstructSpecification),
        "SCENARIO BLUEPRINT": isinstance(blueprint, ScenarioBlueprint),
        "RESPONSE OPTIONS": isinstance(candidate, CandidateItem),
        "QUALITY CHECKS": False,
    }
    failed_stage = {
        "construct": "CONSTRUCT SPECIFICATION",
        "blueprint": "SCENARIO BLUEPRINT",
        "options": "RESPONSE OPTIONS",
        "quality": "QUALITY CHECKS",
    }.get(error.stage)
    statuses = {
        stage: "COMPLETE" if completed[stage] else "NOT RUN" for stage in STAGES
    }
    if failed_stage is not None:
        statuses[failed_stage] = "ERROR"
    st.session_state["v2_stage_status"] = statuses
    st.session_state["v2_generation_error"] = error.public_message


def _render_construct(spec: ConstructSpecification | None) -> None:
    st.markdown(
        '<div class="section-heading">CONSTRUCT SPECIFICATION</div>',
        unsafe_allow_html=True,
    )
    if spec is None:
        st.info("This stage has not produced a validated construct specification.")
        return
    domain = DOMAINS[spec.domain_id]
    facet = FACETS[spec.facet_id]
    indicators = "".join(f"<li>{_e(value)}</li>" for value in spec.behavioral_indicators)
    exclusions = "".join(f"<li>{_e(value)}</li>" for value in spec.exclusions)
    confounds = "".join(f"<li>{_e(value)}</li>" for value in spec.potential_confounds)
    st.markdown(
        f"""
        <div class="detail-grid">
          <div class="detail-cell"><div class="field-label">DOMAIN</div><div class="detail-value">{_e(domain.label_en)} / {_e(domain.label_zh)}</div></div>
          <div class="detail-cell"><div class="field-label">FACET</div><div class="detail-value">{_e(facet.label_en)} / {_e(facet.label_zh)}</div></div>
          <div class="detail-cell"><div class="field-label">ANCHORS</div><div class="detail-value">{_e(', '.join(spec.anchor_ids))}</div></div>
        </div>
        <div class="tool-band"><div class="field-label">DEFINITION</div><div class="detail-value zh-content">{_e(spec.definition_zh)}</div></div>
        <div class="detail-grid">
          <div class="detail-cell"><div class="field-label">BEHAVIORAL INDICATORS</div><ul class="zh-content">{indicators}</ul></div>
          <div class="detail-cell"><div class="field-label">EXCLUSIONS</div><ul class="zh-content">{exclusions}</ul></div>
          <div class="detail-cell"><div class="field-label">POTENTIAL CONFOUNDS</div><ul class="zh-content">{confounds}</ul></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_blueprint(blueprint: ScenarioBlueprint | None) -> None:
    st.markdown(
        '<div class="section-heading">SCENARIO BLUEPRINT</div>',
        unsafe_allow_html=True,
    )
    if blueprint is None:
        st.info("This stage has not produced a validated scenario blueprint.")
        return
    fields = (
        ("SETTING", blueprint.setting),
        ("ACTORS", " / ".join(blueprint.actors)),
        ("RELATIONSHIP", blueprint.relationship),
        ("GOAL", blueprint.goal),
        ("TRIGGER EVENT", blueprint.trigger_event),
        ("DECISION POINT", blueprint.decision_point),
        ("CONTEXT DOMAIN", blueprint.context_domain),
    )
    cells = "".join(
        f'<div class="detail-cell"><div class="field-label">{_e(label)}</div>'
        f'<div class="detail-value zh-content">{_e(value)}</div></div>'
        for label, value in fields
    )
    st.markdown(f'<div class="detail-grid">{cells}</div>', unsafe_allow_html=True)


def _render_options(item: CandidateItem | None) -> None:
    st.markdown(
        '<div class="section-heading">RESPONSE OPTIONS</div>',
        unsafe_allow_html=True,
    )
    if item is None:
        st.info("This stage has not produced a validated candidate item.")
        return
    st.markdown(
        f'<div class="assessment-instruction zh-content">{_e(item.instruction_zh)}</div>'
        f'<div class="assessment-stem zh-content">{_e(item.stem_zh)}</div>',
        unsafe_allow_html=True,
    )
    ordered = sorted(item.options, key=lambda option: option.display_order)
    for option in ordered:
        st.markdown(
            f'<div class="option-row zh-content"><strong>{option.display_order}.</strong> '
            f'{_e(option.text_zh)}</div>',
            unsafe_allow_html=True,
        )
    with st.expander("RESEARCH METADATA", expanded=False):
        for option in ordered:
            st.markdown(
                f"**{option.display_order}. {option.option_id}**  "
                f"Score {option.score} / Trait {option.trait_level}  \n"
                f"{option.rationale}  \n{option.desirability_note}"
            )


def _render_quality(item: CandidateItem | None) -> None:
    st.markdown(
        '<div class="section-heading">QUALITY CHECKS</div>',
        unsafe_allow_html=True,
    )
    if item is None or not item.quality_checks:
        st.info("This stage has not produced quality-check results.")
    else:
        rows = []
        for check in item.quality_checks:
            if check.outcome.value == "PASS":
                color = "#24A8D8"
            elif check.severity.value == "ERROR":
                color = "#D81B78"
            else:
                color = "#F28C28"
            rows.append(
                f"""
                <div style="border-bottom:1px solid #D9D9D5;padding:10px 0">
                  <div><span class="status-badge" style="background:{color};color:#0B0B0D">{_e(check.outcome.value)}</span>
                  <strong>{_e(check.label)}</strong> / {_e(check.severity.value)}</div>
                  <div class="field-label">EVIDENCE</div><div class="zh-content">{_e(check.evidence)}</div>
                  <div class="field-label">RECOMMENDATION</div><div class="zh-content">{_e(check.recommendation or 'No change recommended.')}</div>
                </div>
                """
            )
        st.markdown("".join(rows), unsafe_allow_html=True)
    st.markdown(
        '<div class="evidence-note">Automated checks are advisory; human review is required.</div>',
        unsafe_allow_html=True,
    )


def _render_stage(
    active_stage: str,
    spec: ConstructSpecification | None,
    blueprint: ScenarioBlueprint | None,
    item: CandidateItem | None,
) -> None:
    if active_stage == "CONSTRUCT SPECIFICATION":
        _render_construct(spec)
    elif active_stage == "SCENARIO BLUEPRINT":
        _render_blueprint(blueprint)
    elif active_stage == "RESPONSE OPTIONS":
        _render_options(item)
    else:
        _render_quality(item)


def _render_trace_summary(item: CandidateItem) -> None:
    passed = sum(check.outcome.value == "PASS" for check in item.quality_checks)
    flagged = len(item.quality_checks) - passed
    option_rows = "".join(
        f"""
        <div style="border-bottom:1px solid #D9D9D5;padding:9px 0">
          <div class="field-label">{_e(option.option_id)} / OPTION {_e(option.display_order)}</div>
          <div class="zh-content">{_e(option.text_zh)}</div>
          <div class="field-label">RATIONALE</div>
          <div class="zh-content">{_e(option.rationale)}</div>
        </div>
        """
        for option in sorted(item.options, key=lambda value: value.display_order)
    )
    check_rows = "".join(
        f"""
        <div style="border-bottom:1px solid #D9D9D5;padding:9px 0">
          <div class="field-label">{_e(check.check_id)}</div>
          <div><strong>{_e(check.label)}</strong> / {_e(check.outcome.value)} / {_e(check.severity.value)}</div>
          <div class="field-label">EVIDENCE</div>
          <div class="zh-content">{_e(check.evidence)}</div>
          <div class="field-label">RECOMMENDATION</div>
          <div class="zh-content">{_e(check.recommendation or 'No change recommended.')}</div>
        </div>
        """
        for check in item.quality_checks
    )
    st.markdown(
        f"""
        <div class="tool-band">
          <div class="field-label">GENERATION TIMESTAMP</div><div class="detail-value">{_e(item.created_at)}</div>
          <div class="field-label">CHECKS</div><div class="detail-value">{_e(passed)} PASS / {_e(flagged)} FLAG</div>
        </div>
        <div class="section-heading">OBSERVABLE OPTION RATIONALES</div>
        {option_rows}
        <div class="section-heading">QUALITY CHECK RECORD</div>
        {check_rows}
        """,
        unsafe_allow_html=True,
    )


def render(
    project: ResearchProject,
    anchors: dict[str, ConstructAnchor],
    service: WorkbenchService,
) -> None:
    pending_mode = st.session_state.pop("v2_pending_generation_mode", None)
    if pending_mode in (GenerationMode.CURATED.value, GenerationMode.LIVE.value):
        st.session_state["v2_generation_mode"] = pending_mode
    st.markdown('<div class="page-kicker">STAGED ITEM DEVELOPMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace-heading">GENERATION STUDIO</div>', unsafe_allow_html=True)

    domain_ids = tuple(DOMAINS)
    if st.session_state.get("v2_selected_domain") not in domain_ids:
        st.session_state["v2_selected_domain"] = domain_ids[0]
    controls = st.columns(5, gap="small")
    with controls[0]:
        mode = st.selectbox(
            "GENERATION MODE",
            (GenerationMode.CURATED.value, GenerationMode.LIVE.value),
            key="v2_generation_mode",
        )
    with controls[1]:
        domain_id = st.selectbox(
            "DOMAIN",
            domain_ids,
            format_func=lambda value: DOMAINS[value].label_en,
            key="v2_selected_domain",
        )
    facet_ids = tuple(
        facet_id for facet_id, facet in FACETS.items() if facet.domain_id == domain_id
    )
    if st.session_state.get("v2_selected_facet") not in facet_ids:
        st.session_state["v2_selected_facet"] = facet_ids[0]
    with controls[2]:
        facet_id = st.selectbox(
            "FACET",
            facet_ids,
            format_func=lambda value: FACETS[value].label_en,
            key="v2_selected_facet",
        )
    taxonomy_selection = (domain_id, facet_id)
    taxonomy_changed = (
        st.session_state.get("v2_generation_taxonomy_selection")
        != taxonomy_selection
    )
    st.session_state["v2_generation_taxonomy_selection"] = taxonomy_selection
    default_curated = _facet_seed(project, domain_id, facet_id)
    context_domains = tuple(project.config.context_domains)
    if (
        taxonomy_changed
        and default_curated is not None
        and default_curated.scenario_blueprint is not None
    ):
        st.session_state["v2_context_domain"] = (
            default_curated.scenario_blueprint.context_domain
        )
    elif st.session_state.get("v2_context_domain") not in context_domains:
        st.session_state["v2_context_domain"] = context_domains[0]
    with controls[3]:
        context_domain = st.selectbox(
            "CONTEXT DOMAIN",
            context_domains,
            key="v2_context_domain",
        )
    anchor_ids = tuple(
        sorted(
            anchor_id
            for anchor_id, anchor in anchors.items()
            if anchor.domain_id == domain_id and anchor.facet_id == facet_id
        )
    )
    if (
        taxonomy_changed
        and default_curated is not None
        and default_curated.anchor_ids[0] in anchor_ids
    ):
        st.session_state["v2_selected_anchor"] = default_curated.anchor_ids[0]
    elif st.session_state.get("v2_selected_anchor") not in anchor_ids:
        st.session_state["v2_selected_anchor"] = anchor_ids[0]
    with controls[4]:
        anchor_id = st.selectbox(
            "ANCHOR",
            anchor_ids,
            format_func=lambda value: f"{value} / {anchors[value].text_zh}",
            key="v2_selected_anchor",
        )

    curated = _matching_seed(
        project,
        domain_id,
        facet_id,
        anchor_id,
        context_domain,
    )
    live_ready = _live_environment_present()
    action_columns = st.columns(2, gap="small")
    with action_columns[0]:
        generate = st.button(
            "GENERATE",
            key="v2_generate",
            disabled=mode != GenerationMode.LIVE.value or not live_ready,
            use_container_width=True,
        )
    with action_columns[1]:
        load_curated = st.button(
            "LOAD CURATED EXAMPLE",
            key="v2_load_curated",
            disabled=curated is None,
            use_container_width=True,
        )

    if mode == GenerationMode.LIVE.value and not live_ready:
        st.info("Live generation requires OPENAI_API_KEY and LLM_MODEL configuration.")
    if curated is None:
        st.info(
            "No curated example matches the selected domain, facet, anchor, and context."
        )

    if load_curated and curated is not None:
        _load_curated(curated)
        st.rerun()

    if generate:
        previous_candidate = st.session_state.get("v2_candidate_item")
        previous_selected = st.session_state.get("v2_selected_item")
        st.session_state["v2_candidate_item"] = None
        st.session_state["v2_construct_spec"] = None
        st.session_state["v2_scenario_blueprint"] = None
        st.session_state["v2_generation_options"] = None
        st.session_state["v2_generation_error"] = None
        try:
            config = LiveModelConfig.from_env()
            client = OpenAICompatibleClient(config)
            pipeline = GenerationPipeline(client)
            generated = pipeline.generate_candidate(
                project.config,
                anchors[anchor_id],
                context_domain,
            )
            try:
                service.save_generated_item(project.config.project_id, generated)
            except (KeyError, OSError, ValueError):
                st.session_state["v2_construct_spec"] = generated.construct_spec
                st.session_state["v2_scenario_blueprint"] = (
                    generated.scenario_blueprint
                )
                st.session_state["v2_generation_options"] = generated
                st.session_state["v2_candidate_item"] = previous_candidate
                st.session_state["v2_selected_item"] = previous_selected
                st.session_state["v2_stage_status"] = {
                    "CONSTRUCT SPECIFICATION": "COMPLETE",
                    "SCENARIO BLUEPRINT": "COMPLETE",
                    "RESPONSE OPTIONS": "COMPLETE",
                    "QUALITY CHECKS": "NOT SAVED",
                }
                st.session_state["v2_generation_error"] = (
                    "Generated item could not be saved."
                )
            else:
                st.session_state["v2_construct_spec"] = generated.construct_spec
                st.session_state["v2_scenario_blueprint"] = (
                    generated.scenario_blueprint
                )
                st.session_state["v2_generation_options"] = generated
                st.session_state["v2_candidate_item"] = generated
                st.session_state["v2_selected_item"] = generated.item_id
                st.session_state["v2_stage_status"] = {
                    stage: "COMPLETE" for stage in STAGES
                }
                st.rerun()
        except GenerationStageError as error:
            _store_partial_results(error)
        except ModelUnavailable:
            st.session_state["v2_generation_error"] = (
                "Live model configuration is unavailable."
            )
        except (KeyError, ValueError):
            st.session_state["v2_generation_error"] = (
                "Live generation could not be completed."
            )

    error_message = st.session_state.get("v2_generation_error")
    if error_message:
        st.error(str(error_message))

    if mode == GenerationMode.CURATED.value:
        display_item = curated
        spec = curated.construct_spec if curated is not None else None
        blueprint = curated.scenario_blueprint if curated is not None else None
        statuses = {stage: "CURATED" for stage in STAGES}
    else:
        candidate_state = st.session_state.get("v2_candidate_item")
        display_item = (
            candidate_state
            if isinstance(candidate_state, CandidateItem)
            and candidate_state.generation_mode is GenerationMode.LIVE
            and candidate_state.domain_id == domain_id
            and candidate_state.facet_id == facet_id
            else None
        )
        spec_state = st.session_state.get("v2_construct_spec")
        spec = (
            spec_state
            if isinstance(spec_state, ConstructSpecification)
            and spec_state.domain_id == domain_id
            and spec_state.facet_id == facet_id
            else None
        )
        blueprint_state = st.session_state.get("v2_scenario_blueprint")
        blueprint = (
            blueprint_state
            if isinstance(blueprint_state, ScenarioBlueprint) and spec is not None
            else None
        )
        statuses = st.session_state.get("v2_stage_status", {})

    stage_item = display_item
    if mode == GenerationMode.LIVE.value and stage_item is None:
        options_state = st.session_state.get("v2_generation_options")
        if (
            isinstance(options_state, CandidateItem)
            and options_state.generation_mode is GenerationMode.LIVE
            and options_state.domain_id == domain_id
            and options_state.facet_id == facet_id
        ):
            stage_item = options_state

    active_stage = st.session_state.get("v2_active_stage", STAGES[0])
    if active_stage not in STAGES:
        active_stage = STAGES[0]
        st.session_state["v2_active_stage"] = active_stage
    rail, central, provenance = st.columns([0.8, 2.15, 1.25], gap="large")
    with rail:
        st.markdown('<div class="section-heading">WORKFLOW</div>', unsafe_allow_html=True)
        for index, stage in enumerate(STAGES, start=1):
            st.markdown(
                f'<div class="field-label">{index:02d} / {_e(stage)}</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                stage,
                key=f"v2_stage_{_STAGE_KEYS[stage]}",
                use_container_width=True,
                type="primary" if stage == active_stage else "secondary",
            ):
                st.session_state["v2_active_stage"] = stage
                st.rerun()
            st.caption(str(statuses.get(stage, "NOT RUN")))
    with central:
        _render_stage(active_stage, spec, blueprint, stage_item)
    with provenance:
        if display_item is None:
            st.markdown('<div class="section-heading">PROVENANCE</div>', unsafe_allow_html=True)
            st.info("Provenance becomes available after a candidate is validated.")
        else:
            render_provenance(item=display_item, anchors=anchors, compact=True)
            _render_trace_summary(display_item)
