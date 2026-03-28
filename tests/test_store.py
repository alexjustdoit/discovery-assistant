"""Tests for session persistence (store.py)."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from data.models import DiscoveryMode, Question, Session, SessionContext
from data.store import delete_session, list_sessions, load_session, save_session


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
