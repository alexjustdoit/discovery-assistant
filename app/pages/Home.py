import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import config  # noqa: F401
from data.store import archive_session, delete_session, list_sessions, load_session, restore_session

DEMO_SESSION_IDS = {
    "a1b2c3d4-0001-4000-8000-ef1234567890",
    "b2c3d4e5-0002-4000-8001-f12345678901",
}

DEPTH_FILTERS = {
    "Any": 0.0,
    "20%+": 0.20,
    "40%+": 0.40,
    "70%+": 0.70,
}


def _depth_bar(depth: float) -> str:
    """Return a simple text progress indicator for depth score."""
    pct = int(depth * 100)
    filled = int(depth * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {pct}%"


st.markdown("## Discovery Assistant")
st.markdown(
    "The work that drives deal outcomes and customer health — discovery questions, call notes, "
    "stakeholder maps, follow-up summaries — usually lives across browser tabs, scattered docs, and memory. "
    "Discovery Assistant keeps it in one place, structured around the actual SA and TAM workflow."
)
st.markdown(
    "Start an engagement, get a tailored discovery playbook, work through it on the call, "
    "log touchpoints over the relationship, and generate a shareable summary and follow-up email when you're ready."
)

st.divider()

# ── Demo engagements ──────────────────────────────────────────────────────────
st.subheader("Explore the demos")
st.caption("Two pre-loaded engagements showing the full SA and TAM workflows.")

demo_sessions = []
for sid in DEMO_SESSION_IDS:
    try:
        demo_sessions.append(load_session(sid))
    except FileNotFoundError:
        pass

# Sort: pre_sales first, then post_sales
demo_sessions.sort(key=lambda s: s.mode.value)

if not demo_sessions:
    st.info("Demo engagements not found. Restart the app to re-seed them.")
else:
    cols = st.columns(len(demo_sessions))
    for col, session in zip(cols, demo_sessions):
        asked, total = session.progress()
        depth = session.discovery_depth()
        mode_label = "Pre-sales (SA)" if session.mode.value == "pre_sales" else "Post-sales (TAM)"
        has_summary = session.summary is not None
        meeting_count = len(session.meetings)

        with col:
            with st.container(border=True):
                st.markdown(f"**{session.context.company}**")
                st.caption(f"{mode_label} · {session.context.stage}")
                st.markdown(f"_{session.context.industry}_")

                st.write("")
                st.caption(f"Discovery depth: {_depth_bar(depth)}")
                st.markdown(f"- {asked}/{total} questions answered")
                if has_summary:
                    st.markdown("- Summary ready")
                if meeting_count:
                    st.markdown(f"- {meeting_count} touchpoints logged")

                st.write("")
                if st.button("Open Playbook", key=f"demo_qb_{session.id}", use_container_width=True, type="primary"):
                    st.session_state["active_session_id"] = session.id
                    st.switch_page("pages/Discovery_Playbook.py")

                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("Touchpoint Log", key=f"demo_ml_{session.id}", use_container_width=True):
                        st.session_state["active_session_id"] = session.id
                        st.switch_page("pages/Touchpoint_Log.py")
                with bcol2:
                    if has_summary:
                        if st.button("Summary", key=f"demo_sum_{session.id}", use_container_width=True):
                            st.session_state["active_session_id"] = session.id
                            st.switch_page("pages/Discovery_Summary.py")

st.divider()

# ── User engagements ──────────────────────────────────────────────────────────
all_sessions = list_sessions()
user_sessions = [s for s in all_sessions if s.id not in DEMO_SESSION_IDS]
active_sessions = [s for s in user_sessions if not s.archived]
archived_sessions = [s for s in user_sessions if s.archived]

st.subheader("Your engagements")

# ── Filters ───────────────────────────────────────────────────────────────────
if active_sessions:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        mode_filter = st.selectbox(
            "Mode",
            options=["All", "Pre-sales", "Post-sales"],
            label_visibility="collapsed",
        )
    with fcol2:
        depth_filter_label = st.selectbox(
            "Discovery depth",
            options=list(DEPTH_FILTERS.keys()),
            label_visibility="collapsed",
        )
    depth_min = DEPTH_FILTERS[depth_filter_label]

    filtered_sessions = [
        s for s in active_sessions
        if (mode_filter == "All"
            or (mode_filter == "Pre-sales" and s.mode.value == "pre_sales")
            or (mode_filter == "Post-sales" and s.mode.value == "post_sales"))
        and s.discovery_depth() >= depth_min
    ]
else:
    filtered_sessions = []

if not active_sessions:
    st.caption("No engagements yet.")
    if st.button("Start a new engagement", type="primary"):
        st.switch_page("pages/New_Engagement.py")
elif not filtered_sessions:
    st.caption("No engagements match the current filters.")
    st.write("")
    if st.button("New Engagement", type="secondary"):
        st.switch_page("pages/New_Engagement.py")
else:
    for session in filtered_sessions:
        asked, total = session.progress()
        depth = session.discovery_depth()
        mode_label = "Pre-sales" if session.mode.value == "pre_sales" else "Post-sales"
        has_summary = session.summary is not None
        meeting_count = len(session.meetings)
        meeting_str = f" · {meeting_count} touchpoints" if meeting_count else ""
        status = "Summary ready" if has_summary else f"{asked}/{total} answered"

        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{session.context.company}**")
                st.caption(
                    f"{mode_label} · {session.context.stage} · {status}{meeting_str} · "
                    f"Updated {session.updated_at.strftime('%b %d')}"
                )
                st.caption(f"Discovery depth: {_depth_bar(depth)}")
            with col2:
                if st.button("Open", key=f"open_{session.id}", use_container_width=True, type="primary"):
                    st.session_state["active_session_id"] = session.id
                    st.switch_page("pages/Discovery_Playbook.py")
            with col3:
                with st.popover("⋯", use_container_width=True):
                    if st.button("Use as Template", key=f"tmpl_{session.id}", use_container_width=True):
                        st.session_state["template_context"] = session.context.model_dump()
                        st.switch_page("pages/New_Engagement.py")
                    if st.button("Archive", key=f"arch_{session.id}", use_container_width=True):
                        archive_session(session.id)
                        st.rerun()
                    if st.button("Delete", key=f"del_{session.id}", use_container_width=True, type="secondary"):
                        delete_session(session.id)
                        st.rerun()

    st.write("")
    if st.button("New Engagement", type="secondary"):
        st.switch_page("pages/New_Engagement.py")

# ── Archived engagements ──────────────────────────────────────────────────────
if archived_sessions:
    st.divider()
    with st.expander(f"Archived ({len(archived_sessions)})", expanded=False):
        for session in archived_sessions:
            asked, total = session.progress()
            mode_label = "Pre-sales" if session.mode.value == "pre_sales" else "Post-sales"
            has_summary = session.summary is not None
            status = "Summary ready" if has_summary else f"{asked}/{total} answered"

            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{session.context.company}**")
                    st.caption(f"{mode_label} · {session.context.stage} · {status}")
                with col2:
                    if st.button("Restore", key=f"restore_{session.id}", use_container_width=True):
                        restore_session(session.id)
                        st.rerun()
                with col3:
                    if st.button("Delete", key=f"adel_{session.id}", use_container_width=True, type="secondary"):
                        delete_session(session.id)
                        st.rerun()
