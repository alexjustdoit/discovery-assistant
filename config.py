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
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# API keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Model names
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# Session storage
SESSIONS_DIR: Path = Path(__file__).parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
