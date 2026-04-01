import streamlit as st

from app.components.engagement_nav import render_engagement_nav  # also ensures sys.path
import config  # noqa: F401
from data.store import list_sessions, load_session, save_session
from features.email_generation import generate_followup_email
from features.summary_generation import generate_summary


def _build_export(session) -> str:
    s = session.summary
    lines = [
        f"# Discovery Summary — {session.context.company}",
        f"**Mode:** {session.mode.value.replace('_', '-')}  ",
        f"**Industry:** {session.context.industry}  ",
        f"**Stage:** {session.context.stage}  ",
        f"**Use case:** {session.context.use_case}",
        "",
        s.raw_text,
        "",
        "---",
        "## Q&A Notes",
    ]
    for q in session.answered_questions():
        lines += [f"**[{q.category}]** {q.text}", f"> {q.answer}", ""]
    return "\n".join(lines)


def _parse_bullets(text: str) -> list[str]:
    return [line.strip().lstrip("- ").strip() for line in text.splitlines() if line.strip()]


# ── Page ──────────────────────────────────────────────────────────────────────

st.header("Discovery Summary")

sessions = list_sessions()
if not sessions:
    st.info("No engagements yet. Create one in **New Engagement**.")
    st.stop()

session_options = {f"{s.context.company} — {s.mode.value.replace('_', '-')} — {s.created_at.strftime('%b %d')}": s.id for s in sessions}
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

render_engagement_nav("summary", mode_label="Pre-sales (SA)" if session.mode.value == "pre_sales" else "Post-sales (TAM)")

answered = session.answered_questions()
if not answered:
    st.warning("No answered questions yet. Go to **Discovery Playbook** to capture notes first.")
    st.stop()

st.caption(f"{len(answered)} answered questions · {session.context.company} · {session.context.stage}")

# ── Generate or display summary ───────────────────────────────────────────────
if session.summary is None:
    if st.button("Generate Summary", type="primary"):
        with st.spinner("Synthesizing discovery notes..."):
            try:
                session.summary = generate_summary(session)
                save_session(session)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate summary: {e}")
    st.stop()

summary = session.summary

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Regenerate", type="secondary"):
        with st.spinner("Regenerating..."):
            try:
                session.summary = generate_summary(session)
                save_session(session)
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
with col2:
    export_text = _build_export(session)
    st.download_button(
        "Export as Markdown",
        data=export_text,
        file_name=f"{session.context.company.lower().replace(' ', '_')}_discovery.md",
        mime="text/markdown",
    )
with col3:
    st.write("")  # spacer

st.divider()

# ── Summary display ───────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Key Findings")
    for item in summary.key_findings:
        st.markdown(f"- {item}")

    st.subheader("Technical Requirements")
    for item in summary.technical_requirements:
        st.markdown(f"- {item}")

with col_b:
    st.subheader("Risks & Concerns")
    for item in summary.risks_and_concerns:
        st.markdown(f"- {item}")

    st.subheader("Recommended Next Steps")
    for item in summary.recommended_next_steps:
        st.markdown(f"- {item}")

st.divider()
st.subheader("Full Summary")
st.markdown(summary.raw_text)

# ── Edit summary ──────────────────────────────────────────────────────────────
st.divider()
with st.expander("Edit summary", expanded=False):
    st.caption("One item per line. Leading dashes are stripped automatically.")
    with st.form("edit_summary_form"):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            edit_findings = st.text_area(
                "Key Findings",
                value="\n".join(summary.key_findings),
                height=160,
            )
            edit_requirements = st.text_area(
                "Technical Requirements",
                value="\n".join(summary.technical_requirements),
                height=160,
            )
        with col_e2:
            edit_risks = st.text_area(
                "Risks & Concerns",
                value="\n".join(summary.risks_and_concerns),
                height=160,
            )
            edit_next_steps = st.text_area(
                "Recommended Next Steps",
                value="\n".join(summary.recommended_next_steps),
                height=160,
            )
        edit_raw = st.text_area("Full Summary Narrative", value=summary.raw_text, height=200)

        if st.form_submit_button("Save Edits", type="primary"):
            session.summary.key_findings = _parse_bullets(edit_findings)
            session.summary.technical_requirements = _parse_bullets(edit_requirements)
            session.summary.risks_and_concerns = _parse_bullets(edit_risks)
            session.summary.recommended_next_steps = _parse_bullets(edit_next_steps)
            session.summary.raw_text = edit_raw.strip()
            # Clear email draft when summary changes so it doesn't go stale
            session.email_draft = None
            save_session(session)
            st.success("Summary updated.")
            st.rerun()

# ── Follow-up email ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Follow-up Email")

if session.email_draft:
    draft_text = st.text_area(
        "Email draft",
        value=session.email_draft,
        height=320,
        label_visibility="collapsed",
    )
    col_save, col_regen, col_clear = st.columns(3)
    with col_save:
        if st.button("Save Draft", type="primary"):
            session.email_draft = draft_text
            save_session(session)
            st.success("Draft saved.")
    with col_regen:
        if st.button("Regenerate"):
            with st.spinner("Regenerating email..."):
                try:
                    session.email_draft = generate_followup_email(session)
                    save_session(session)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    with col_clear:
        if st.button("Clear Draft", type="secondary"):
            session.email_draft = None
            save_session(session)
            st.rerun()
else:
    if st.button("Draft Follow-up Email", type="primary"):
        with st.spinner("Drafting follow-up email..."):
            try:
                session.email_draft = generate_followup_email(session)
                save_session(session)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate email: {e}")
