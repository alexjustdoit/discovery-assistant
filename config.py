"""
Central configuration. Reads from .env file if present.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# LLM routing
USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi4")

# API keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Model names
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# Session storage
SESSIONS_DIR: Path = Path(__file__).parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

DEMO_SESSIONS_DIR: Path = Path(__file__).parent / "data" / "demo_sessions"

# When running on Streamlit Community Cloud, isolate each browser session
# to its own subdirectory so concurrent demo users don't see each other's data.
# Set SCC_MODE=true in the SCC secrets dashboard. Never set locally.
def _get_scc_mode() -> bool:
    try:
        import streamlit as st
        return str(st.secrets.get("SCC_MODE", os.getenv("SCC_MODE", "false"))).lower() == "true"
    except Exception:
        return os.getenv("SCC_MODE", "false").lower() == "true"

SCC_MODE: bool = _get_scc_mode()
