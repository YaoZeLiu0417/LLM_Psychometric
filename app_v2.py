import streamlit as st

from psychometric_v2.config import ANCHOR_ASSET, ROOT, LiveModelConfig, ModelUnavailable
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

repository = JsonProjectRepository(ROOT / "workspace_data" / "v2" / "projects")
research_project = repository.ensure_seed(build_demo_project())
construct_anchors = load_anchor_asset(ANCHOR_ASSET)
workbench = WorkbenchService(repository)

try:
    LiveModelConfig.from_env()
except ModelUnavailable:
    live_available = False
else:
    live_available = True

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
