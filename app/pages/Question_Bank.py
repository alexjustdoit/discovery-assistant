import streamlit as st

import config  # noqa: F401
from data.store import list_sessions, load_session, save_session

st.header("Question Bank")

# Session picker
sessions = list_sessions()
if not sessions:
    st.info("No sessions yet. Create one in **New Session**.")
    st.stop()

session_options = {f"{s.context.company} — {s.mode.value.replace('_', '-')} — {s.created_at.strftime('%b %d')}": s.id for s in sessions}
default_index = 0

# Pre-select active session if set
active_id = st.session_state.get("active_session_id")
if active_id:
    ids = list(session_options.values())
    if active_id in ids:
        default_index = ids.index(active_id)

selected_label = st.selectbox("Session", options=list(session_options.keys()), index=default_index)
session_id = session_options[selected_label]
session = load_session(session_id)
st.session_state["active_session_id"] = session_id

asked, total = session.progress()
st.caption(f"{asked}/{total} questions asked")
if total > 0:
    st.progress(asked / total)

st.divider()

# Group questions by category
categories: dict[str, list] = {}
for q in session.questions:
    categories.setdefault(q.category, []).append(q)

changed = False
for category, questions in categories.items():
    asked_in_cat = sum(1 for q in questions if q.asked)
    with st.expander(f"{category} ({asked_in_cat}/{len(questions)})", expanded=not all(q.asked for q in questions)):
        for q in questions:
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                checked = st.checkbox("", value=q.asked, key=f"asked_{q.id}", label_visibility="collapsed")
            with col2:
                st.markdown(f"**{q.text}**")
                if q.follow_ups:
                    with st.expander("Follow-ups", expanded=False):
                        for fu in q.follow_ups:
                            st.caption(f"→ {fu}")
                answer = st.text_area(
                    "Notes / answer",
                    value=q.answer,
                    key=f"answer_{q.id}",
                    height=80,
                    label_visibility="collapsed",
                    placeholder="Notes from the conversation...",
                )

            if checked != q.asked or answer != q.answer:
                q.asked = checked
                q.answer = answer
                changed = True

if changed:
    save_session(session)

st.divider()
if st.button("Generate Summary →", type="primary", disabled=len(session.answered_questions()) == 0):
    st.switch_page("pages/Discovery_Summary.py")
