from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st


_DEFAULTS: dict[str, Any] = {
    "v2_active_page": "PROJECT",
    "v2_generation_mode": "CURATED DEMO",
    "v2_researcher_unlocked": False,
    "v2_researcher_access_error": None,
    "v2_researcher_access_fingerprint": None,
    "v2_selected_domain": "extraversion",
    "v2_selected_facet": "sociability",
    "v2_selected_item": None,
    "v2_active_stage": "CONSTRUCT SPECIFICATION",
    "v2_construct_spec": None,
    "v2_scenario_blueprint": None,
    "v2_candidate_item": None,
    "v2_generation_attempts": 0,
    "v2_participant_index": 0,
    "v2_participant_responses": {},
}


def init_state() -> None:
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(default)
