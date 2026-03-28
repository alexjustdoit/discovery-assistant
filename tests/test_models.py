"""Tests for data models and session persistence."""
import json
import tempfile
from pathlib import Path

import pytest

from data.models import DiscoveryMode, Question, Session, SessionContext


def make_session(mode=DiscoveryMode.PRE_SALES) -> Session:
    return Session(
        mode=mode,
        context=SessionContext(
            company="Acme Corp",
            industry="FinTech",
            use_case="Automate compliance reporting",
            tech_stack="AWS, Snowflake, Python",
            stage="Discovery",
        ),
    )


def test_session_creation():
    session = make_session()
    assert session.id
    assert session.mode == DiscoveryMode.PRE_SALES
    assert session.context.company == "Acme Corp"
    assert session.questions == []
    assert session.summary is None


def test_session_progress_empty():
    session = make_session()
    asked, total = session.progress()
    assert asked == 0
    assert total == 0


def test_session_progress_with_questions():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1", asked=True, answer="Yes"),
        Question(category="Technical Fit", text="Q2", asked=False),
        Question(category="Integrations & Architecture", text="Q3", asked=True, answer="We use Kafka"),
    ]
    asked, total = session.progress()
    assert asked == 2
    assert total == 3


def test_answered_questions():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1", asked=True, answer="Some answer"),
        Question(category="Technical Fit", text="Q2", asked=True, answer=""),  # asked but no answer
        Question(category="Technical Fit", text="Q3", asked=False),
    ]
    answered = session.answered_questions()
    assert len(answered) == 1
    assert answered[0].text == "Q1"


def test_session_serialization_roundtrip():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="What is your current solution?", asked=True, answer="We use homegrown scripts")
    ]
    serialized = session.model_dump_json()
    restored = Session.model_validate_json(serialized)

    assert restored.id == session.id
    assert restored.mode == session.mode
    assert restored.context.company == session.context.company
    assert len(restored.questions) == 1
    assert restored.questions[0].answer == "We use homegrown scripts"


def test_post_sales_mode():
    session = make_session(mode=DiscoveryMode.POST_SALES)
    assert session.mode == DiscoveryMode.POST_SALES
    data = json.loads(session.model_dump_json())
    assert data["mode"] == "post_sales"
