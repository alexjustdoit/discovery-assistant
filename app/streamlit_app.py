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

# page_config and navigation must be registered before any import that could
# trigger a rerun (e.g. seed_demo_sessions setting st.query_params on cold start).
# Registering position="hidden" here ensures auto-discovery never flashes.
st.set_page_config(
    page_title="Discovery Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_main_pages = [
    st.Page("pages/Home.py", title="Home"),
    st.Page("pages/New_Engagement.py", title="New Engagement"),
    st.Page("pages/Discovery_Playbook.py", title="Discovery Playbook"),
    st.Page("pages/Touchpoint_Log.py", title="Touchpoint Log"),
    st.Page("pages/Discovery_Summary.py", title="Discovery Summary"),
]

_dev_pages = [
    st.Page("pages/Technical_Info.py", title="Technical Info"),
]

pg = st.navigation(_main_pages + _dev_pages, position="hidden")

# Remaining imports and setup after navigation is registered
import config  # noqa: F401 — must be loaded after secrets injection
from app.components.sidebar import render_sidebar_header, render_sidebar_footer
from data.store import seed_demo_sessions

seed_demo_sessions()

render_sidebar_header()

with st.sidebar:
    for page in _main_pages:
        st.page_link(page)

pg.run()
render_sidebar_footer(_dev_pages)
