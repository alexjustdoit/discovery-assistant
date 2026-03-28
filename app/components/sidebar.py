import os
import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Discovery Assistant")
        st.caption("Pre-sales & post-sales discovery, powered by AI.")
        st.divider()

        use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        if use_local:
            st.info("LLM: Ollama (local)", icon="🏠")
        else:
            has_claude = bool(os.getenv("ANTHROPIC_API_KEY"))
            st.success(f"LLM: OpenAI + {'Claude' if has_claude else 'OpenAI only'}", icon="☁️")
