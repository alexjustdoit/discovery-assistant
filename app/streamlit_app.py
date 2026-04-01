import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# Inject Streamlit secrets into os.environ before config.py reads them.
# On Streamlit Cloud there is no .env file — secrets come from the UI.
# Locally, .env takes precedence because load_dotenv won't override existing vars.
try:
    for _key, _val in st.secrets.items():
        if isinstance(_val, str):
            os.environ.setdefault(_key, _val)
except Exception:
    pass

import config  # noqa: F401 — must be loaded after secrets injection
from app.components.sidebar import render_sidebar
from data.store import seed_demo_sessions

seed_demo_sessions()

st.set_page_config(
    page_title="Discovery Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_pages = [
    st.Page("pages/Home.py", title="Home", icon="🏠"),
    st.Page("pages/New_Engagement.py", title="New Engagement", icon="➕"),
    st.Page("pages/Discovery_Playbook.py", title="Discovery Playbook", icon="📋"),
    st.Page("pages/Touchpoint_Log.py", title="Touchpoint Log", icon="🗓️"),
    st.Page("pages/Discovery_Summary.py", title="Discovery Summary", icon="📄"),
]

pg = st.navigation(_pages, position="hidden")

render_sidebar()

with st.sidebar:
    for page in _pages:
        st.page_link(page)

pg.run()
