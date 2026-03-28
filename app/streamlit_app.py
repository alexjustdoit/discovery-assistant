import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

import config  # noqa: F401 — must be first to load .env
from app.components.sidebar import render_sidebar

st.set_page_config(
    page_title="Discovery Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = st.navigation(
    [
        st.Page("pages/New_Session.py", title="New Session", icon="➕"),
        st.Page("pages/Question_Bank.py", title="Question Bank", icon="📋"),
        st.Page("pages/Discovery_Summary.py", title="Discovery Summary", icon="📄"),
        st.Page("pages/Saved_Sessions.py", title="Saved Sessions", icon="💾"),
    ]
)

render_sidebar()
pages.run()
