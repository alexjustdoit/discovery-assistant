import sys
from pathlib import Path

# Guarantee project root is on sys.path regardless of how/when this module is
# imported — page files depend on it to find `config`, `data`, `features`, etc.
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

_PAGES = [
    ("📋 Discovery Playbook", "playbook", "pages/Discovery_Playbook.py"),
    ("🗓️ Touchpoint Log", "touchpoint_log", "pages/Touchpoint_Log.py"),
    ("📄 Discovery Summary", "summary", "pages/Discovery_Summary.py"),
]


def render_engagement_nav(current: str, mode_label: str = "") -> None:
    """
    Inline cross-page nav for the three working pages.
    current: "playbook" | "touchpoint_log" | "summary"
    mode_label: optional mode string shown below the nav, e.g. "Pre-sales (SA)"
    """
    cols = st.columns(len(_PAGES))
    for col, (label, key, path) in zip(cols, _PAGES):
        with col:
            is_current = key == current
            clicked = st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            )
            if clicked and not is_current:
                st.switch_page(path)
    if mode_label:
        st.caption(mode_label)
    st.divider()
