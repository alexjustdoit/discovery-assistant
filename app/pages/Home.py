import streamlit as st

import config  # noqa: F401
from data.store import list_sessions, load_session

DEMO_SESSION_IDS = {
    "a1b2c3d4-0001-4000-8000-ef1234567890",
    "b2c3d4e5-0002-4000-8001-f12345678901",
}

st.markdown("## Discovery Assistant")
st.markdown(
    "AI-powered discovery for pre-sales and post-sales teams. "
    "Input customer context, get a tailored question bank, capture notes during the call, "
    "log meeting touchpoints, and synthesize a shareable summary and follow-up email — in one workflow."
)

st.divider()

# ── Demo sessions ─────────────────────────────────────────────────────────────
st.subheader("Explore the demos")
st.caption("Two pre-loaded sessions showing the full SA and TAM workflows.")

demo_sessions = []
for sid in DEMO_SESSION_IDS:
    try:
        demo_sessions.append(load_session(sid))
    except FileNotFoundError:
        pass

# Sort: pre_sales first, then post_sales
demo_sessions.sort(key=lambda s: s.mode.value)

if not demo_sessions:
    st.info("Demo sessions not found. Restart the app to re-seed them.")
else:
    cols = st.columns(len(demo_sessions))
    for col, session in zip(cols, demo_sessions):
        asked, total = session.progress()
        mode_label = "Pre-sales (SA)" if session.mode.value == "pre_sales" else "Post-sales (TAM)"
        has_summary = session.summary is not None
        meeting_count = len(session.meetings)

        with col:
            with st.container(border=True):
                st.markdown(f"**{session.context.company}**")
                st.caption(f"{mode_label} · {session.context.stage}")
                st.markdown(f"_{session.context.industry}_")

                st.write("")
                if has_summary:
                    st.markdown(f"- {asked}/{total} questions answered")
                    st.markdown(f"- Summary ready")
                else:
                    st.markdown(f"- {asked}/{total} questions answered")
                if meeting_count:
                    st.markdown(f"- {meeting_count} meetings logged")

                st.write("")
                if st.button("Open Question Bank", key=f"demo_qb_{session.id}", use_container_width=True, type="primary"):
                    st.session_state["active_session_id"] = session.id
                    st.switch_page("pages/Question_Bank.py")

                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("Meeting Log", key=f"demo_ml_{session.id}", use_container_width=True):
                        st.session_state["active_session_id"] = session.id
                        st.switch_page("pages/Meeting_Log.py")
                with bcol2:
                    if has_summary:
                        if st.button("Summary", key=f"demo_sum_{session.id}", use_container_width=True):
                            st.session_state["active_session_id"] = session.id
                            st.switch_page("pages/Discovery_Summary.py")

st.divider()

# ── User sessions ─────────────────────────────────────────────────────────────
all_sessions = list_sessions()
user_sessions = [s for s in all_sessions if s.id not in DEMO_SESSION_IDS]

st.subheader("Your sessions")

if not user_sessions:
    st.caption("No sessions yet.")
    if st.button("Start a new session", type="primary"):
        st.switch_page("pages/New_Session.py")
else:
    for session in user_sessions[:5]:  # show up to 5 most recent
        asked, total = session.progress()
        mode_label = "Pre-sales" if session.mode.value == "pre_sales" else "Post-sales"
        has_summary = session.summary is not None
        status = "Summary ready" if has_summary else f"{asked}/{total} answered"
        meeting_count = len(session.meetings)
        meeting_str = f" · {meeting_count} meetings" if meeting_count else ""

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{session.context.company}**")
                st.caption(f"{mode_label} · {session.context.stage} · {status}{meeting_str} · Updated {session.updated_at.strftime('%b %d')}")
            with col2:
                if st.button("Open", key=f"user_{session.id}", use_container_width=True, type="primary"):
                    st.session_state["active_session_id"] = session.id
                    st.switch_page("pages/Question_Bank.py")

    if len(user_sessions) > 5:
        st.caption(f"+ {len(user_sessions) - 5} more in Saved Sessions")

    st.write("")
    if st.button("New session", type="secondary"):
        st.switch_page("pages/New_Session.py")
