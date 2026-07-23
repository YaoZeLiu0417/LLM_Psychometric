import os

import streamlit as st

from psychometric_v2.config import ANCHOR_ASSET, WORKSPACE_ROOT
from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.legacy import load_anchor_asset
from psychometric_v2.repository import JsonProjectRepository
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

repository = JsonProjectRepository(WORKSPACE_ROOT / "v2" / "projects")
research_project = repository.ensure_seed(build_demo_project())
construct_anchors = load_anchor_asset(ANCHOR_ASSET)
workbench = WorkbenchService(repository)
review.sync_selected_item_from_review(research_project)

live_available = bool(
    os.getenv("OPENAI_API_KEY", "").strip()
    and os.getenv("LLM_MODEL", "").strip()
)

render_header(research_project, live_available=live_available)
active_page = render_navigation()
page_renderers = {
    "PROJECT": project.render,
    "CONSTRUCT MAP": construct_map.render,
    "GENERATION STUDIO": generation.render,
    "REVIEW": review.render,
    "PARTICIPANT VIEW": participant.render,
}
page_renderers[active_page](research_project, construct_anchors, workbench)
