import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

import config  # noqa: F401 — loads .env
from data.models import DiscoveryMode, Session, SessionContext
from data.store import save_session
from features.question_generation import generate_questions

st.header("New Engagement")

# Consume template context if coming from "Use as Template"
template = st.session_state.pop("template_context", None)
if template:
    st.info("Pre-filled from existing engagement. Adjust any fields before generating.")

with st.form("new_session_form"):
    mode = st.radio(
        "Discovery mode",
        options=[DiscoveryMode.PRE_SALES, DiscoveryMode.POST_SALES],
        format_func=lambda m: "Pre-sales (SA)" if m == DiscoveryMode.PRE_SALES else "Post-sales (TAM)",
        horizontal=True,
    )

    st.subheader("Context")
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company name", value=template["company"] if template else "", placeholder="Acme Corp")
        industry = st.text_input("Industry", value=template["industry"] if template else "", placeholder="FinTech, Healthcare, E-commerce...")
        stage = st.text_input(
            "Stage",
            value=template["stage"] if template else "",
            placeholder="Discovery / POC / Renewal Q3 / At-risk...",
        )
    with col2:
        use_case = st.text_area("Use case / challenge", value=template["use_case"] if template else "", placeholder="What are they trying to solve?", height=100)
        tech_stack = st.text_area("Tech stack", value=template["tech_stack"] if template else "", placeholder="Salesforce, AWS, Snowflake, Python...", height=100)

    notes = st.text_area("Additional context (optional)", value=template["notes"] if template else "", placeholder="Anything else relevant — deal size, incumbent, stakeholders...", height=80)

    submitted = st.form_submit_button("Generate Questions", type="primary", use_container_width=True)

if submitted:
    if not company or not use_case:
        st.error("Company name and use case are required.")
    else:
        context = SessionContext(
            company=company,
            industry=industry,
            use_case=use_case,
            tech_stack=tech_stack,
            stage=stage,
            notes=notes,
        )
        session = Session(mode=mode, context=context)

        with st.spinner("Generating discovery questions... stay on this page until complete."):
            try:
                questions = generate_questions(session)
                session.questions = questions
                save_session(session)
                st.session_state["active_session_id"] = session.id
                st.success(f"Generated {len(questions)} questions. Head to **Discovery Playbook** to start your engagement.")
                st.info(f"Engagement ID: `{session.id}`")
            except Exception as e:
                st.error(f"Failed to generate questions: {e}")
