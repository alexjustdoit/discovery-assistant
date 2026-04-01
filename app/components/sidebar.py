import os
import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Discovery Assistant")
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
