import streamlit as st

import config  # noqa: F401
from data.store import list_sessions, load_session, save_session
from features.summary_generation import generate_summary

st.header("Discovery Summary")

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
session = load_session(session_id)

answered = session.answered_questions()
if not answered:
    st.warning("No answered questions yet. Go to **Question Bank** to capture notes first.")
    st.stop()

st.caption(f"{len(answered)} answered questions · {session.context.company} · {session.context.stage}")

# Generate or show existing summary
if session.summary is None:
    if st.button("Generate Summary", type="primary"):
        with st.spinner("Synthesizing discovery notes..."):
            try:
                summary = generate_summary(session)
                session.summary = summary
                save_session(session)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate summary: {e}")
else:
    summary = session.summary

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Regenerate", type="secondary"):
            with st.spinner("Regenerating..."):
                try:
                    summary = generate_summary(session)
                    session.summary = summary
                    save_session(session)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    with col2:
        export_text = _build_export(session)
        st.download_button("Export as Markdown", data=export_text, file_name=f"{session.context.company.lower().replace(' ', '_')}_discovery.md", mime="text/markdown")

    st.divider()

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


def _build_export(session) -> str:
    s = session.summary
    lines = [
        f"# Discovery Summary — {session.context.company}",
        f"**Mode:** {session.mode.value.replace('_', '-')}  ",
        f"**Industry:** {session.context.industry}  ",
        f"**Stage:** {session.context.stage}  ",
        f"**Use case:** {session.context.use_case}",
        "",
        "## Key Findings",
        *[f"- {x}" for x in s.key_findings],
        "",
        "## Technical Requirements",
        *[f"- {x}" for x in s.technical_requirements],
        "",
        "## Risks & Concerns",
        *[f"- {x}" for x in s.risks_and_concerns],
        "",
        "## Recommended Next Steps",
        *[f"- {x}" for x in s.recommended_next_steps],
        "",
        "## Full Summary",
        s.raw_text,
        "",
        "---",
        "## Q&A Notes",
    ]
    for q in session.answered_questions():
        lines += [f"**[{q.category}]** {q.text}", f"> {q.answer}", ""]
    return "\n".join(lines)
