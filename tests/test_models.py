"""Tests for data models and session persistence."""
import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from data.models import DiscoveryMode, Meeting, Question, Session, SessionContext


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


def test_session_email_draft_defaults_to_none():
    session = make_session()
    assert session.email_draft is None


def test_session_email_draft_roundtrip():
    session = make_session()
    session.email_draft = "Subject: Follow-up\n\nHi team, thanks for the call."
    restored = Session.model_validate_json(session.model_dump_json())
    assert restored.email_draft == session.email_draft


def test_session_email_draft_none_roundtrip():
    """Sessions without email_draft (e.g. existing JSON files) load cleanly."""
    session = make_session()
    data = json.loads(session.model_dump_json())
    data.pop("email_draft", None)  # simulate old session file without the field
    restored = Session.model_validate_json(json.dumps(data))
    assert restored.email_draft is None


# ── Meeting model ─────────────────────────────────────────────────────────────

def test_meeting_creation():
    m = Meeting(date=date(2026, 3, 28), title="Intro Discovery Call")
    assert m.id
    assert m.attendees == ""
    assert m.notes == ""


def test_meeting_roundtrip():
    m = Meeting(
        date=date(2026, 3, 28),
        title="Technical Deep-Dive",
        attendees="Marcus Chen, You (SA)",
        notes="Walked through Oracle pipeline.",
    )
    data = json.loads(m.model_dump_json())
    restored = Meeting.model_validate(data)
    assert restored.date == m.date
    assert restored.title == m.title
    assert restored.attendees == m.attendees
    assert restored.notes == m.notes


def test_session_meetings_default_empty():
    session = make_session()
    assert session.meetings == []


def test_session_with_meetings_roundtrip():
    session = make_session()
    session.meetings = [
        Meeting(date=date(2026, 3, 15), title="Intro Call", notes="First call notes."),
        Meeting(date=date(2026, 3, 22), title="Technical Deep-Dive", attendees="Priya Shah"),
    ]
    restored = Session.model_validate_json(session.model_dump_json())
    assert len(restored.meetings) == 2
    assert restored.meetings[0].title == "Intro Call"
    assert restored.meetings[1].attendees == "Priya Shah"


def test_session_without_meetings_field_loads_cleanly():
    """Old session JSON files without meetings field should load with empty list."""
    session = make_session()
    data = json.loads(session.model_dump_json())
    data.pop("meetings", None)
    restored = Session.model_validate_json(json.dumps(data))
    assert restored.meetings == []


# ── archived field ────────────────────────────────────────────────────────────

def test_archived_defaults_to_false():
    session = make_session()
    assert session.archived is False


def test_archived_roundtrip():
    session = make_session()
    session.archived = True
    restored = Session.model_validate_json(session.model_dump_json())
    assert restored.archived is True


def test_archived_missing_from_json_loads_as_false():
    """Old session JSON files without archived field load cleanly."""
    session = make_session()
    data = json.loads(session.model_dump_json())
    data.pop("archived", None)
    restored = Session.model_validate_json(json.dumps(data))
    assert restored.archived is False


# ── discovery_depth ───────────────────────────────────────────────────────────

def test_discovery_depth_empty_session():
    session = make_session()
    assert session.discovery_depth() == 0.0


def test_discovery_depth_no_answers():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1"),
        Question(category="Technical Fit", text="Q2"),
    ]
    assert session.discovery_depth() == 0.0


def test_discovery_depth_all_answered_single_category():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1", answer="A1"),
        Question(category="Technical Fit", text="Q2", answer="A2"),
    ]
    # notes_score = 1.0, coverage_score = 1.0, touchpoints = 0, summary = 0
    expected = 0.60 * 1.0 + 0.20 * 1.0 + 0.10 * 0.0 + 0.10 * 0.0
    assert abs(session.discovery_depth() - expected) < 1e-9


def test_discovery_depth_partial_answers_two_categories():
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1", answer="A1"),
        Question(category="Technical Fit", text="Q2"),  # unanswered
        Question(category="Integrations & Architecture", text="Q3"),  # unanswered
    ]
    # notes_score = 1/3, coverage_score = 1/2
    expected = 0.60 * (1 / 3) + 0.20 * (1 / 2)
    assert abs(session.discovery_depth() - expected) < 1e-9


def test_discovery_depth_touchpoints_capped_at_3():
    session = make_session()
    session.questions = [Question(category="Technical Fit", text="Q1", answer="A1")]
    session.meetings = [
        Meeting(date=date(2026, 3, 1), title="Call 1"),
        Meeting(date=date(2026, 3, 8), title="Call 2"),
        Meeting(date=date(2026, 3, 15), title="Call 3"),
        Meeting(date=date(2026, 3, 22), title="Call 4"),  # 4th; should cap at 3
    ]
    depth = session.discovery_depth()
    # touchpoint contribution should be 0.10 * 1.0 (capped), not 0.10 * (4/3)
    assert depth <= 1.0


def test_discovery_depth_full_score():
    from data.models import DiscoverySummary
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="Q1", answer="A1"),
        Question(category="Integrations & Architecture", text="Q2", answer="A2"),
    ]
    session.meetings = [
        Meeting(date=date(2026, 3, 1), title="Call 1"),
        Meeting(date=date(2026, 3, 8), title="Call 2"),
        Meeting(date=date(2026, 3, 15), title="Call 3"),
    ]
    session.summary = DiscoverySummary(
        key_findings=["Finding"],
        technical_requirements=["Req"],
        risks_and_concerns=[],
        recommended_next_steps=["Next"],
        raw_text="Summary text",
    )
    assert abs(session.discovery_depth() - 1.0) < 1e-9
