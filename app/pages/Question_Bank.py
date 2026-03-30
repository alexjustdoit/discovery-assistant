import streamlit as st

import config  # noqa: F401
from data.models import Question
from data.store import list_sessions, load_session, save_session
from features.question_generation import generate_additional_questions

st.header("Question Bank")

# Session picker
sessions = list_sessions()
if not sessions:
    st.info("No sessions yet. Create one in **New Session**.")
    st.stop()

session_options = {f"{s.context.company} — {s.mode.value.replace('_', '-')} — {s.created_at.strftime('%b %d')}": s.id for s in sessions}
default_index = 0

active_id = st.session_state.get("active_session_id")
if active_id:
    ids = list(session_options.values())
    if active_id in ids:
        default_index = ids.index(active_id)

selected_label = st.selectbox("Session", options=list(session_options.keys()), index=default_index)
session_id = session_options[selected_label]

# Reset new-question tracking when switching sessions
if st.session_state.get("_qb_session_id") != session_id:
    st.session_state["new_question_ids"] = set()
    st.session_state["_qb_session_id"] = session_id

session = load_session(session_id)
st.session_state["active_session_id"] = session_id

new_ids: set[str] = st.session_state.get("new_question_ids", set())

asked, total = session.progress()
st.caption(f"{asked}/{total} questions asked")
if total > 0:
    st.progress(asked / total)

# ── Edit session context ──────────────────────────────────────────────────────
with st.expander("Edit session context", expanded=False):
    with st.form("edit_context_form"):
        col1, col2 = st.columns(2)
        with col1:
            edit_company = st.text_input("Company name", value=session.context.company)
            edit_industry = st.text_input("Industry", value=session.context.industry)
            edit_stage = st.text_input("Stage", value=session.context.stage)
        with col2:
            edit_use_case = st.text_area("Use case / challenge", value=session.context.use_case, height=100)
            edit_tech_stack = st.text_area("Tech stack", value=session.context.tech_stack, height=100)
        edit_notes = st.text_area("Additional context", value=session.context.notes, height=80)

        if st.form_submit_button("Save Changes", type="primary"):
            session.context.company = edit_company
            session.context.industry = edit_industry
            session.context.stage = edit_stage
            session.context.use_case = edit_use_case
            session.context.tech_stack = edit_tech_stack
            session.context.notes = edit_notes
            save_session(session)
            st.success("Session context updated.")
            st.rerun()

# ── Refresh questions ─────────────────────────────────────────────────────────
if st.button("Refresh Questions", help="Generate additional questions based on the current session context. Existing answered questions are never changed."):
    with st.spinner("Generating additional questions..."):
        try:
            new_questions = generate_additional_questions(session)
            session.questions.extend(new_questions)
            save_session(session)
            added_ids = {q.id for q in new_questions}
            st.session_state["new_question_ids"] = new_ids | added_ids
            st.rerun()
        except Exception as e:
            st.error(f"Failed to generate questions: {e}")

st.divider()

# ── Question bank ─────────────────────────────────────────────────────────────
categories: dict[str, list] = {}
for q in session.questions:
    categories.setdefault(q.category, []).append(q)

changed = False
for category, questions in categories.items():
    asked_in_cat = sum(1 for q in questions if q.asked)
    new_in_cat = sum(1 for q in questions if q.id in new_ids)
    cat_label = f"{category} ({asked_in_cat}/{len(questions)})"
    if new_in_cat:
        cat_label += f" · {new_in_cat} new"

    with st.expander(cat_label, expanded=not all(q.asked for q in questions)):
        for q in questions:
            is_new = q.id in new_ids
            wrapper = st.container(border=True) if is_new else st.container()
            with wrapper:
                if is_new:
                    st.caption("✦ New")
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

        # Per-category add question
        with st.form(f"add_q_{category}", border=False):
            col_input, col_btn = st.columns([0.85, 0.15])
            with col_input:
                new_q_text = st.text_input(
                    "add",
                    key=f"new_q_text_{category}",
                    placeholder=f"Add a question to {category}...",
                    label_visibility="collapsed",
                )
            with col_btn:
                add_submitted = st.form_submit_button("Add", use_container_width=True)

            if add_submitted and new_q_text.strip():
                new_q = Question(category=category, text=new_q_text.strip())
                session.questions.append(new_q)
                save_session(session)
                st.session_state["new_question_ids"] = new_ids | {new_q.id}
                st.rerun()

if changed:
    save_session(session)

st.divider()
if st.button("Generate Summary →", type="primary", disabled=len(session.answered_questions()) == 0):
    st.switch_page("pages/Discovery_Summary.py")
