"""Tests for session persistence (store.py)."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from data.models import DiscoveryMode, Question, Session, SessionContext
from data.store import archive_session, delete_session, list_sessions, load_session, restore_session, save_session, seed_demo_sessions


def make_session() -> Session:
    return Session(
        mode=DiscoveryMode.PRE_SALES,
        context=SessionContext(
            company="Test Co",
            industry="SaaS",
            use_case="Test use case",
            tech_stack="Python",
            stage="Discovery",
        ),
    )


@pytest.fixture
def tmp_sessions_dir(tmp_path, monkeypatch):
    """Redirect SESSIONS_DIR to a temp dir for isolation."""
    monkeypatch.setattr("data.store._sessions_dir", lambda: tmp_path)
    return tmp_path


def test_save_and_load(tmp_sessions_dir):
    session = make_session()
    save_session(session)
    loaded = load_session(session.id)
    assert loaded.id == session.id
    assert loaded.context.company == "Test Co"


def test_load_nonexistent(tmp_sessions_dir):
    with pytest.raises(FileNotFoundError):
        load_session("does-not-exist")


def test_list_sessions_empty(tmp_sessions_dir):
    assert list_sessions() == []


def test_list_sessions_multiple(tmp_sessions_dir):
    s1 = make_session()
    s2 = make_session()
    save_session(s1)
    save_session(s2)
    sessions = list_sessions()
    assert len(sessions) == 2
    ids = {s.id for s in sessions}
    assert s1.id in ids
    assert s2.id in ids


def test_delete_session(tmp_sessions_dir):
    session = make_session()
    save_session(session)
    delete_session(session.id)
    with pytest.raises(FileNotFoundError):
        load_session(session.id)


def test_delete_nonexistent_is_noop(tmp_sessions_dir):
    delete_session("does-not-exist")  # should not raise


def test_save_updates_updated_at(tmp_sessions_dir):
    session = make_session()
    original_updated_at = session.updated_at
    save_session(session)
    loaded = load_session(session.id)
    assert loaded.updated_at >= original_updated_at


# ── seed_demo_sessions ────────────────────────────────────────────────────────

@pytest.fixture
def demo_sessions_dir(tmp_path):
    """A temp dir acting as DEMO_SESSIONS_DIR with one sample session JSON."""
    demo_dir = tmp_path / "demo_sessions"
    demo_dir.mkdir()
    session = make_session()
    (demo_dir / f"{session.id}.json").write_text(session.model_dump_json())
    return demo_dir, session


def test_seed_demo_sessions_copies_to_sessions_dir(tmp_sessions_dir, demo_sessions_dir, monkeypatch):
    demo_dir, demo_session = demo_sessions_dir
    monkeypatch.setattr("data.store._sessions_dir", lambda: tmp_sessions_dir)
    with patch("data.store.DEMO_SESSIONS_DIR" if False else "config.DEMO_SESSIONS_DIR", demo_dir, create=True):
        # Patch the import inside seed_demo_sessions
        with patch("data.store.seed_demo_sessions.__globals__", {}) if False else patch("config.DEMO_SESSIONS_DIR", demo_dir):
            pass

    # Directly call with monkeypatched DEMO_SESSIONS_DIR via the import inside the function
    import config
    original = config.DEMO_SESSIONS_DIR
    config.DEMO_SESSIONS_DIR = demo_dir
    try:
        seed_demo_sessions()
        loaded = load_session(demo_session.id)
        assert loaded.id == demo_session.id
    finally:
        config.DEMO_SESSIONS_DIR = original


def test_seed_demo_sessions_is_idempotent(tmp_sessions_dir, demo_sessions_dir, monkeypatch):
    demo_dir, demo_session = demo_sessions_dir
    monkeypatch.setattr("data.store._sessions_dir", lambda: tmp_sessions_dir)
    import config
    original = config.DEMO_SESSIONS_DIR
    config.DEMO_SESSIONS_DIR = demo_dir
    try:
        seed_demo_sessions()
        seed_demo_sessions()
        assert len(list(tmp_sessions_dir.glob("*.json"))) == 1
    finally:
        config.DEMO_SESSIONS_DIR = original


def test_seed_demo_sessions_does_not_overwrite_existing(tmp_sessions_dir, demo_sessions_dir, monkeypatch):
    demo_dir, demo_session = demo_sessions_dir
    monkeypatch.setattr("data.store._sessions_dir", lambda: tmp_sessions_dir)

    # Pre-write a modified version of the demo session
    modified = demo_session.model_copy()
    modified.context.company = "User Modified Co"
    (tmp_sessions_dir / f"{demo_session.id}.json").write_text(modified.model_dump_json())

    import config
    original = config.DEMO_SESSIONS_DIR
    config.DEMO_SESSIONS_DIR = demo_dir
    try:
        seed_demo_sessions()
        loaded = load_session(demo_session.id)
        assert loaded.context.company == "User Modified Co"
    finally:
        config.DEMO_SESSIONS_DIR = original


def test_seed_demo_sessions_missing_dir_is_noop(tmp_sessions_dir, monkeypatch, tmp_path):
    monkeypatch.setattr("data.store._sessions_dir", lambda: tmp_sessions_dir)
    import config
    original = config.DEMO_SESSIONS_DIR
    config.DEMO_SESSIONS_DIR = tmp_path / "nonexistent"
    try:
        seed_demo_sessions()  # should not raise
        assert list_sessions() == []
    finally:
        config.DEMO_SESSIONS_DIR = original


# ── archive / restore ─────────────────────────────────────────────────────────

def test_archive_session(tmp_sessions_dir):
    session = make_session()
    save_session(session)
    archive_session(session.id)
    loaded = load_session(session.id)
    assert loaded.archived is True


def test_restore_session(tmp_sessions_dir):
    session = make_session()
    session.archived = True
    save_session(session)
    restore_session(session.id)
    loaded = load_session(session.id)
    assert loaded.archived is False


def test_archive_does_not_delete_session(tmp_sessions_dir):
    session = make_session()
    save_session(session)
    archive_session(session.id)
    assert load_session(session.id) is not None


def test_list_sessions_includes_archived(tmp_sessions_dir):
    active = make_session()
    archived = make_session()
    save_session(active)
    save_session(archived)
    archive_session(archived.id)
    sessions = list_sessions()
    assert len(sessions) == 2
    archived_ids = [s.id for s in sessions if s.archived]
    assert archived.id in archived_ids
