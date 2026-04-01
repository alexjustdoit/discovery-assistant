import os
import streamlit as st


_DA_BRANDING_HTML = """
<div style="min-height: 130px;">
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
  <p style="font-size: 1.75rem; font-weight: 700; line-height: 1.2; margin: 0 0 0.2rem 0;">Discovery Assistant</p>
  <p style="font-size: 0.875rem; opacity: 0.6; margin: 0; line-height: 1.4;">AI-Powered Discovery for SAs and TAMs</p>
</div>
"""

_SIDEBAR_CSS = """<style>
/* Hide the default Streamlit auto-discovered nav regardless of position= timing */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"] {
    display: none !important;
}
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
[data-testid="stSidebarContent"] {
    display: flex !important;
    flex-direction: column !important;
    min-height: 100vh !important;
}
[data-testid="stSidebarUserContent"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
    padding-top: 0.5rem !important;
}
[data-testid="stSidebarUserContent"] > div:first-child {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}
[data-testid="stSidebarUserContent"] > div:first-child > [data-testid="stVerticalBlock"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}
.element-container:has(.sidebar-footer-spacer) {
    flex: 1 !important;
    min-height: 0 !important;
}
</style>"""

_RESET_BTN_CSS = """<style>
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border: 1px solid #e74c3c !important;
    letter-spacing: 0.01em;
}
</style>"""


def render_sidebar_header() -> None:
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_DA_BRANDING_HTML, unsafe_allow_html=True)
        st.divider()


def render_sidebar_footer(dev_pages=None) -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-footer-spacer"></div>', unsafe_allow_html=True)
        st.divider()
        scc_mode = str(st.secrets.get("SCC_MODE", os.getenv("SCC_MODE", "false"))).lower() == "true"

        st.subheader("LLM Provider")
        if scc_mode:
            st.toggle(
                "Use Local LLM (Ollama)",
                value=False,
                disabled=True,
                help="Local Ollama is not available on the hosted demo — the app uses OpenAI (standard tasks) and Anthropic Claude (quality tasks) automatically.",
            )
            st.caption("Demo uses OpenAI + Anthropic · Local Ollama available when self-hosted")
        else:
            use_local = st.toggle(
                "Use Local LLM (Ollama)",
                value=os.getenv("USE_LOCAL_LLM", "true").lower() == "true",
                help="Toggle between free local Ollama and API providers",
            )
            os.environ["USE_LOCAL_LLM"] = "true" if use_local else "false"

            if use_local:
                st.caption("Local mode · Free · requires Ollama")
            else:
                has_openai = bool(os.getenv("OPENAI_API_KEY"))
                has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
                if has_openai:
                    st.caption("✅ OpenAI key set")
                else:
                    st.warning("Set OPENAI_API_KEY in .env")
                if has_anthropic:
                    st.caption("✅ Anthropic key set")

        if dev_pages:
            with st.expander("Developers"):
                for page in dev_pages:
                    st.page_link(page)

        if scc_mode:
            st.divider()
            st.markdown(_RESET_BTN_CSS, unsafe_allow_html=True)
            if st.button("↺\u2002Reset Demo", use_container_width=True, help="Clear your session and start fresh"):
                if "token" in st.query_params:
                    del st.query_params["token"]
                st.session_state.clear()
