import os
import streamlit as st


_DA_ICON_SVG = """
<div style="display:flex; justify-content:center; padding: 0.75rem 0 0.5rem 0;">
<svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="22" cy="22" r="19" stroke="#1ABC9C" stroke-width="2.5"/>
  <polygon points="22,7 18,22 22,19.5 26,22" fill="#1ABC9C"/>
  <polygon points="22,37 26,22 22,24.5 18,22" fill="#1ABC9C" opacity="0.35"/>
  <circle cx="22" cy="22" r="2.5" fill="#1ABC9C"/>
  <line x1="3" y1="22" x2="7" y2="22" stroke="#1ABC9C" stroke-width="2" stroke-linecap="round"/>
  <line x1="37" y1="22" x2="41" y2="22" stroke="#1ABC9C" stroke-width="2" stroke-linecap="round"/>
</svg>
</div>
"""

_SIDEBAR_CSS = """<style>
section[data-testid="stSidebar"] [data-testid="stLogoSpacer"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: auto !important;
    padding: 0 !important;
}
</style>"""


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_DA_ICON_SVG, unsafe_allow_html=True)
        st.title("Discovery Assistant")
        st.caption("Customer engagement intelligence for SAs and TAMs.")
        st.divider()

        use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        if use_local:
            st.info("LLM: Ollama (local)", icon="🏠")
        else:
            has_claude = bool(os.getenv("ANTHROPIC_API_KEY"))
            st.success(f"LLM: OpenAI + {'Claude' if has_claude else 'OpenAI only'}", icon="☁️")

        if str(st.secrets.get("SCC_MODE", os.getenv("SCC_MODE", "false"))).lower() == "true":
            st.divider()
            if st.button("🔄 Reset Demo", use_container_width=True, help="Clear your session and start fresh"):
                if "token" in st.query_params:
                    del st.query_params["token"]
                st.session_state.clear()
