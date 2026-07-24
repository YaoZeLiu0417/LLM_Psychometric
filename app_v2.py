import streamlit as st

from psychometric_v2.config import ANCHOR_ASSET, WORKSPACE_ROOT
from psychometric_v2.deployment import DeploymentSettings
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.live_access import researcher_access_granted
from psychometric_v2.session_runtime import repository_for_session
from psychometric_v2.ui.components import render_header, render_navigation
from psychometric_v2.ui.pages import construct_map, generation, participant, project, review
from psychometric_v2.ui.state import init_state
from psychometric_v2.ui.theme import apply_theme
from psychometric_v2.workbench import WorkbenchService


st.set_page_config(
    page_title="Adolescent Big Five Workbench",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()
init_state()
pending_generation_mode = st.session_state.pop("v2_pending_generation_mode", None)
if pending_generation_mode in ("CURATED DEMO", "LIVE GENERATION"):
    st.session_state["v2_generation_mode"] = pending_generation_mode

try:
    deployment = DeploymentSettings.from_env()
except ValueError:
    st.error("Workbench deployment configuration is invalid.")
    st.stop()

try:
    repository = repository_for_session(
        st.session_state,
        deployment,
        WORKSPACE_ROOT,
    )
except OSError:
    st.error("This workbench session is temporarily unavailable.")
    st.stop()

research_project = repository.load("adolescent-big-five-demo")
construct_anchors = load_anchor_asset(ANCHOR_ASSET)
workbench = WorkbenchService(
    repository,
    mutation_authorized=researcher_access_granted(st.session_state),
)
review.sync_selected_item_from_review(research_project)

render_header(research_project)
active_page = render_navigation()
page_renderers = {
    "PROJECT": project.render,
    "CONSTRUCT MAP": construct_map.render,
    "GENERATION STUDIO": generation.render,
    "REVIEW": review.render,
    "PARTICIPANT VIEW": participant.render,
}
if active_page == "GENERATION STUDIO":
    generation.render(
        research_project,
        construct_anchors,
        workbench,
        deployment,
    )
else:
    page_renderers[active_page](research_project, construct_anchors, workbench)
