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


def archive_session(session_id: str) -> None:
    session = load_session(session_id)
    session.archived = True
    save_session(session)


def restore_session(session_id: str) -> None:
    session = load_session(session_id)
    session.archived = False
    save_session(session)


def delete_session(session_id: str) -> None:
    path = _sessions_dir() / f"{session_id}.json"
    if path.exists():
        path.unlink()


def seed_demo_sessions() -> None:
    """Copy demo session files into sessions dir if not already present.

    Idempotent — skips any demo session whose ID already exists in sessions/.
    This preserves user edits to demo sessions across restarts.
    """
    from config import DEMO_SESSIONS_DIR

    if not DEMO_SESSIONS_DIR.exists():
        return

    sessions_dir = _sessions_dir()
    for demo_path in DEMO_SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(demo_path.read_text())
            session_id = data.get("id", "")
            dest = sessions_dir / f"{session_id}.json"
            if not dest.exists():
                dest.write_text(demo_path.read_text())
        except Exception:
            pass
