"""JSON-based session persistence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data.models import Session


def _sessions_dir() -> Path:
    from config import SESSIONS_DIR
    return SESSIONS_DIR


def save_session(session: Session) -> None:
    session.updated_at = datetime.now(timezone.utc)
    path = _sessions_dir() / f"{session.id}.json"
    path.write_text(session.model_dump_json(indent=2))


def load_session(session_id: str) -> Session:
    path = _sessions_dir() / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session {session_id} not found")
    return Session.model_validate_json(path.read_text())


def list_sessions() -> list[Session]:
    sessions = []
    for path in sorted(_sessions_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            sessions.append(Session.model_validate_json(path.read_text()))
        except Exception:
            pass
    return sessions


def delete_session(session_id: str) -> None:
    path = _sessions_dir() / f"{session_id}.json"
    if path.exists():
        path.unlink()
