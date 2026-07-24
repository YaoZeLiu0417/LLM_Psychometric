from __future__ import annotations

import streamlit as st

from psychometric_v2.live_access import (
    live_access_configured,
    researcher_access_granted,
    submit_researcher_access_code,
)


def _submit_researcher_access() -> None:
    submit_researcher_access_code(st.session_state)


def render_researcher_access() -> bool:
    granted = researcher_access_granted(st.session_state)
    if granted:
        st.caption("RESEARCHER ACCESS ENABLED FOR THIS SESSION")
    elif live_access_configured():
        with st.expander("RESEARCHER ACCESS"):
            st.text_input(
                "ACCESS CODE",
                type="password",
                key="v2_researcher_access_input",
            )
            st.button(
                "UNLOCK",
                key="v2_unlock_researcher",
                on_click=_submit_researcher_access,
            )
    else:
        st.info(
            "Researcher Access is not configured; this session is read-only."
        )

    error = st.session_state.get("v2_researcher_access_error")
    if error:
        st.error(str(error))
    return granted
