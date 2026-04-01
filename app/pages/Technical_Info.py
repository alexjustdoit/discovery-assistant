import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import pydantic
import streamlit as st

import config  # noqa: F401
from data.store import list_sessions
from llm.router import LLMRouter

st.title("Technical Info")
st.caption("Developer reference — provider config, routing rules, environment, and data stats.")

router = LLMRouter()
use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"

# ── LLM Provider Architecture ──────────────────────────────────────────────────

st.subheader("LLM Provider Architecture")

provider_data = {
    "Provider": ["Ollama (local)", "GPT-5.4-nano", "Claude Haiku 4.5"],
    "Cost": ["Free", "~$0.001/call", "~$0.003/call"],
    "Speed": ["Varies by GPU", "~1.5s", "~1.5s"],
    "Use Case": ["Development / demo", "Question generation", "Summaries and email drafts"],
}
st.dataframe(pd.DataFrame(provider_data), use_container_width=True, hide_index=True)

st.divider()

# ── Active Provider Config ─────────────────────────────────────────────────────

st.subheader("Active Provider Config")

col1, col2, col3 = st.columns(3)
with col1:
    mode = "Local (Ollama)" if use_local else "API"
    st.metric("Mode", mode)
with col2:
    if use_local:
        st.metric("Standard Tasks", router.DEFAULT_LOCAL_MODEL)
    else:
        st.metric("Standard Tasks", router.DEFAULT_CHEAP_API)
with col3:
    if use_local:
        st.metric("Quality Tasks", router.DEFAULT_LOCAL_MODEL)
    elif os.getenv("ANTHROPIC_API_KEY"):
        st.metric("Quality Tasks", router.DEFAULT_QUALITY_API)
    else:
        st.metric("Quality Tasks", f"{router.DEFAULT_CHEAP_API} (fallback — no Anthropic key)")

# ── Ollama Status ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("Ollama")

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Base URL", ollama_url)
with col2:
    st.metric("Model", router.DEFAULT_LOCAL_MODEL)

try:
    import httpx
    resp = httpx.get(f"{ollama_url}/api/tags", timeout=3.0)
    if resp.status_code == 200:
        tags = resp.json().get("models", [])
        pulled = [m["name"] for m in tags]
        if any(router.DEFAULT_LOCAL_MODEL in m for m in pulled):
            st.success(f"Ollama reachable · {router.DEFAULT_LOCAL_MODEL} is available")
        else:
            st.warning(
                f"Ollama reachable but **{router.DEFAULT_LOCAL_MODEL}** is not pulled. "
                f"Run: `ollama pull {router.DEFAULT_LOCAL_MODEL}`"
            )
        if pulled:
            with st.expander(f"All pulled models ({len(pulled)})"):
                st.write("  \n".join(f"• {m}" for m in pulled))
    else:
        st.error(f"Ollama responded with HTTP {resp.status_code}")
except Exception:
    st.error(f"Ollama not reachable at `{ollama_url}` — start Ollama or set OLLAMA_BASE_URL in .env")

# ── Environment Variables ──────────────────────────────────────────────────────

st.divider()
st.subheader("Environment Variables")


def _mask(val: str | None) -> str:
    if not val:
        return "—"
    if len(val) <= 8:
        return "***"
    return val[:4] + "***" + val[-4:]


env_rows = [
    {
        "Variable": "USE_LOCAL_LLM",
        "Current Value": os.getenv("USE_LOCAL_LLM", "true"),
        "Default": "true",
        "Description": "true → Ollama (free); false → OpenAI + Claude",
    },
    {
        "Variable": "OLLAMA_BASE_URL",
        "Current Value": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "Default": "http://localhost:11434",
        "Description": "Ollama API endpoint (override for WSL2 / remote host)",
    },
    {
        "Variable": "OPENAI_API_KEY",
        "Current Value": _mask(os.getenv("OPENAI_API_KEY")),
        "Default": "—",
        "Description": "Required when USE_LOCAL_LLM=false",
    },
    {
        "Variable": "ANTHROPIC_API_KEY",
        "Current Value": _mask(os.getenv("ANTHROPIC_API_KEY")),
        "Default": "—",
        "Description": "Optional — enables Claude Haiku for summaries and email drafts",
    },
    {
        "Variable": "OPENAI_MODEL",
        "Current Value": os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
        "Default": "gpt-5.4-nano",
        "Description": "Override the default OpenAI model",
    },
    {
        "Variable": "SCC_MODE",
        "Current Value": os.getenv("SCC_MODE", "false"),
        "Default": "false",
        "Description": "true → per-session isolation for Streamlit Cloud hosting",
    },
]
st.dataframe(pd.DataFrame(env_rows), use_container_width=True, hide_index=True)

# ── Quality Routing Rules ──────────────────────────────────────────────────────

st.divider()
st.subheader("Quality Routing Rules")
st.caption(
    "When USE_LOCAL_LLM=false, features flagged quality_required=True route to Claude Haiku "
    "if ANTHROPIC_API_KEY is set, otherwise fall back to the OpenAI model."
)

routing_rows = [
    {"Feature": "Question Generation", "quality_required": "False", "Reason": "High-volume structured output — cost-sensitive"},
    {"Feature": "Follow-up Probe Suggestions", "quality_required": "False", "Reason": "Inline generation, speed matters"},
    {"Feature": "Discovery Summary", "quality_required": "True", "Reason": "Synthesized narrative — quality matters"},
    {"Feature": "Follow-up Email Draft", "quality_required": "True", "Reason": "Customer-facing output"},
]
st.dataframe(pd.DataFrame(routing_rows), use_container_width=True, hide_index=True)

# ── Session Data Stats ─────────────────────────────────────────────────────────

st.divider()
st.subheader("Session Data")

try:
    sessions = list_sessions()
    total_sessions = len(sessions)
    total_questions = sum(len(s.questions) for s in sessions)
    answered = sum(sum(1 for q in s.questions if q.asked) for s in sessions)
    total_meetings = sum(len(s.meetings) for s in sessions)
    summaries = sum(1 for s in sessions if s.summary is not None)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Engagements", total_sessions)
    with col2:
        st.metric("Questions", total_questions)
    with col3:
        st.metric("Answered", answered)
    with col4:
        st.metric("Touchpoints", total_meetings)
    with col5:
        st.metric("Summaries", summaries)
except Exception as e:
    st.error(f"Could not load session data: {e}")

# ── Stack Versions ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("Stack")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
with col2:
    st.metric("Streamlit", st.__version__)
with col3:
    st.metric("Pydantic", pydantic.__version__)

# ── Links ──────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Links")
st.markdown("""
- [GitHub Repository](https://github.com/alexjustdoit/discovery-assistant)
- [Streamlit Docs — st.navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation)
- [Ollama Model Library](https://ollama.com/library)
""")
