import streamlit as st

import config  # noqa: F401
from data.models import Question
from data.store import list_sessions, load_session, save_session
from features.question_generation import (
    generate_additional_questions,
    regenerate_unanswered_questions,
)

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
    st.session_state.pop("context_updated_for", None)

session = load_session(session_id)
st.session_state["active_session_id"] = session_id

new_ids: set[str] = st.session_state.get("new_question_ids", set())

# ── Sidebar save button ───────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    save_clicked = st.button(
        "Save Notes",
        use_container_width=True,
        help="Save any pending notes before navigating away",
    )

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
            st.session_state["context_updated_for"] = session_id
            st.rerun()

# ── Post-context-save question update prompt ──────────────────────────────────
if st.session_state.get("context_updated_for") == session_id:
    unanswered_count = sum(1 for q in session.questions if not q.asked and not q.answer.strip())
    with st.info("Session context updated.", icon="✅"):
        pass
    if unanswered_count > 0:
        st.markdown(f"**{unanswered_count} unanswered questions** may no longer fit the updated context. What would you like to do?")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Update unanswered questions", type="primary", use_container_width=True,
                         help="Regenerate all unanswered questions for the new context. Answered questions are preserved."):
                with st.spinner("Regenerating questions... stay on this page until complete."):
                    try:
                        updated = regenerate_unanswered_questions(session)
                        old_ids = {q.id for q in session.questions}
                        session.questions = updated
                        save_session(session)
                        added_ids = {q.id for q in updated if q.id not in old_ids}
                        st.session_state["new_question_ids"] = new_ids | added_ids
                        st.session_state.pop("context_updated_for", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to regenerate questions: {e}")
        with col_b:
            if st.button("Add net-new questions", use_container_width=True,
                         help="Keep all existing questions and append additional ones for the new context."):
                with st.spinner("Generating additional questions... stay on this page until complete."):
                    try:
                        new_questions = generate_additional_questions(session)
                        session.questions.extend(new_questions)
                        save_session(session)
                        added_ids = {q.id for q in new_questions}
                        st.session_state["new_question_ids"] = new_ids | added_ids
                        st.session_state.pop("context_updated_for", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate questions: {e}")
        with col_c:
            if st.button("Keep as-is", use_container_width=True):
                st.session_state.pop("context_updated_for", None)
                st.rerun()
    else:
        if st.button("Dismiss", use_container_width=False):
            st.session_state.pop("context_updated_for", None)
            st.rerun()

# ── Refresh questions ─────────────────────────────────────────────────────────
if st.button("Refresh Questions", help="Generate additional questions based on the current session context. Existing answered questions are never changed."):
    with st.spinner("Generating additional questions... stay on this page until complete."):
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
                    # Question text + inline edit popover
                    q_col, edit_col = st.columns([0.93, 0.07])
                    with q_col:
                        st.markdown(f"**{q.text}**")
                    with edit_col:
                        with st.popover("✏", help="Edit question text"):
                            edited_text = st.text_area(
                                "Edit question",
                                value=q.text,
                                key=f"edit_text_{q.id}",
                                height=80,
                            )
                            if st.button("Save", key=f"edit_save_{q.id}", type="primary"):
                                if edited_text.strip() and edited_text.strip() != q.text:
                                    q.text = edited_text.strip()
                                    save_session(session)
                                    st.rerun()

                    if q.follow_ups:
                        with st.expander("Follow-ups", expanded=False):
                            for fu in q.follow_ups:
                                fu_col, add_col = st.columns([0.9, 0.1])
                                with fu_col:
                                    st.caption(f"→ {fu}")
                                with add_col:
                                    if st.button("＋", key=f"promote_{q.id}_{fu[:20]}", help="Add to question bank"):
                                        new_q = Question(category=q.category, text=fu)
                                        session.questions.append(new_q)
                                        save_session(session)
                                        st.session_state["new_question_ids"] = new_ids | {new_q.id}
                                        st.rerun()

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

if save_clicked:
    if not changed:
        save_session(session)
    st.toast("Notes saved.")

st.divider()
if st.button("Generate Summary →", type="primary", disabled=len(session.answered_questions()) == 0):
    st.switch_page("pages/Discovery_Summary.py")
