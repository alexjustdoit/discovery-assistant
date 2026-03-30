import streamlit as st

import config  # noqa: F401
from data.store import delete_session, list_sessions

st.header("Saved Sessions")

sessions = list_sessions()

if not sessions:
    st.info("No sessions yet. Create one in **New Session**.")
    st.stop()

for session in sessions:
    asked, total = session.progress()
    has_summary = session.summary is not None
    mode_label = "Pre-sales" if session.mode.value == "pre_sales" else "Post-sales"
    summary_badge = "Summary ready" if has_summary else f"{asked}/{total} answered"

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{session.context.company}**")
            st.caption(f"{mode_label} · {session.context.stage} · {session.context.industry}")
            st.caption(f"{summary_badge} · Updated {session.updated_at.strftime('%b %d, %Y')}")
        with col2:
            if st.button("Open", key=f"open_{session.id}", use_container_width=True):
                st.session_state["active_session_id"] = session.id
                st.switch_page("pages/Question_Bank.py")
        with col3:
            if st.button("Delete", key=f"delete_{session.id}", use_container_width=True, type="secondary"):
                delete_session(session.id)
                st.rerun()
