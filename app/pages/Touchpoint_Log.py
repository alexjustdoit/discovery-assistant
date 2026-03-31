from datetime import date

import streamlit as st

from app.components.engagement_nav import render_engagement_nav  # also ensures sys.path
import config  # noqa: F401
from data.models import Meeting
from data.store import list_sessions, load_session, save_session

st.header("Touchpoint Log")

# ── Engagement picker ─────────────────────────────────────────────────────────
sessions = list_sessions()
if not sessions:
    st.info("No engagements yet. Create one in **New Engagement**.")
    st.stop()

session_options = {
    f"{s.context.company} — {s.mode.value.replace('_', '-')} — {s.created_at.strftime('%b %d')}": s.id
    for s in sessions
}
default_index = 0
active_id = st.session_state.get("active_session_id")
if active_id:
    ids = list(session_options.values())
    if active_id in ids:
        default_index = ids.index(active_id)

selected_label = st.selectbox("Engagement", options=list(session_options.keys()), index=default_index)
session_id = session_options[selected_label]
session = load_session(session_id)
st.session_state["active_session_id"] = session_id

render_engagement_nav("touchpoint_log", mode_label="Pre-sales (SA)" if session.mode.value == "pre_sales" else "Post-sales (TAM)")

meeting_count = len(session.meetings)
st.caption(f"{session.context.company} · {session.context.stage} · {meeting_count} touchpoint{'s' if meeting_count != 1 else ''} logged")

# ── Log a touchpoint ──────────────────────────────────────────────────────────
with st.expander("Log a touchpoint", expanded=meeting_count == 0):
    with st.form("log_meeting_form"):
        col1, col2 = st.columns(2)
        with col1:
            meeting_date = st.date_input("Date", value=date.today())
            meeting_title = st.text_input("Title", placeholder="Intro Discovery Call, Technical Deep-Dive, QBR...")
        with col2:
            meeting_attendees = st.text_input("Attendees", placeholder="Marcus Chen (VP Eng), You (SA)...")
        meeting_notes = st.text_area("Notes", height=160, placeholder="What happened, what you learned, open questions, follow-ups...")

        if st.form_submit_button("Log Touchpoint", type="primary"):
            if not meeting_title.strip():
                st.error("Title is required.")
            else:
                new_meeting = Meeting(
                    date=meeting_date,
                    title=meeting_title.strip(),
                    attendees=meeting_attendees.strip(),
                    notes=meeting_notes.strip(),
                )
                session.meetings.append(new_meeting)
                # Sort newest-first after insert
                session.meetings.sort(key=lambda m: m.date, reverse=True)
                save_session(session)
                st.rerun()

st.divider()

# ── Timeline ──────────────────────────────────────────────────────────────────
if not session.meetings:
    st.info("No meetings logged yet. Use the form above to record your first touchpoint.")
    st.stop()

sorted_meetings = sorted(session.meetings, key=lambda m: m.date, reverse=True)

for meeting in sorted_meetings:
    with st.container(border=True):
        header_col, btn_col = st.columns([5, 1])
        with header_col:
            st.markdown(f"**{meeting.title}**")
            date_str = meeting.date.strftime("%B %d, %Y")
            attendee_str = f" · {meeting.attendees}" if meeting.attendees else ""
            st.caption(f"{date_str}{attendee_str}")
        with btn_col:
            if st.button("Delete", key=f"del_{meeting.id}", type="secondary", use_container_width=True):
                session.meetings = [m for m in session.meetings if m.id != meeting.id]
                save_session(session)
                st.rerun()

        if meeting.notes:
            st.markdown(meeting.notes)

        with st.expander("Edit", expanded=False):
            with st.form(f"edit_meeting_{meeting.id}"):
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    edit_date = st.date_input("Date", value=meeting.date, key=f"edate_{meeting.id}")
                    edit_title = st.text_input("Title", value=meeting.title, key=f"etitle_{meeting.id}")
                with ecol2:
                    edit_attendees = st.text_input("Attendees", value=meeting.attendees, key=f"eatt_{meeting.id}")
                edit_notes = st.text_area("Notes", value=meeting.notes, height=160, key=f"enotes_{meeting.id}")

                if st.form_submit_button("Save", type="primary"):
                    meeting.date = edit_date
                    meeting.title = edit_title.strip()
                    meeting.attendees = edit_attendees.strip()
                    meeting.notes = edit_notes.strip()
                    session.meetings.sort(key=lambda m: m.date, reverse=True)
                    save_session(session)
                    st.rerun()
