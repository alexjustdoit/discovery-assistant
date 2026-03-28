"""Tests for summary generation feature (mocked LLM)."""
from unittest.mock import MagicMock, patch

import pytest

from data.models import DiscoveryMode, Question, Session, SessionContext
from features.summary_generation import generate_summary, _extract_bullets


def make_session_with_answers() -> Session:
    session = Session(
        mode=DiscoveryMode.PRE_SALES,
        context=SessionContext(
            company="Acme Corp",
            industry="FinTech",
            use_case="Automate compliance reporting",
            tech_stack="AWS, Snowflake",
            stage="Discovery",
        ),
    )
    session.questions = [
        Question(
            category="Technical Fit",
            text="What does your current reporting workflow look like?",
            asked=True,
            answer="We use Excel and it takes 3 days each quarter.",
        ),
        Question(
            category="Integrations & Architecture",
            text="What data sources feed your compliance reports?",
            asked=True,
            answer="Snowflake, Salesforce, and a legacy Oracle DB.",
        ),
        Question(
            category="Technical Fit",
            text="What is your timeline for implementation?",
            asked=False,  # not answered — should be excluded
        ),
    ]
    return session


MOCK_SUMMARY_TEXT = """
1. Key Findings
- Excel-based process is slow and error-prone
- Strong Snowflake fit

2. Technical Requirements
- Native Snowflake connector required
- Oracle legacy integration needed

3. Risks & Concerns
- Oracle legacy system may complicate integration
- No clear budget confirmed

4. Recommended Next Steps
- Schedule technical deep-dive
- Send Snowflake connector docs

They are a strong fit with clear pain around manual reporting.
"""


@patch("features.summary_generation.router")
def test_generate_summary(mock_router):
    session = make_session_with_answers()
    mock_provider = MagicMock()
    mock_provider.complete.return_value = MagicMock(content=MOCK_SUMMARY_TEXT)
    mock_router.get_provider.return_value = mock_provider

    summary = generate_summary(session)

    mock_router.get_provider.assert_called_once_with(quality_required=True)
    assert summary.raw_text == MOCK_SUMMARY_TEXT
    assert len(summary.key_findings) > 0
    assert len(summary.recommended_next_steps) > 0


@patch("features.summary_generation.router")
def test_generate_summary_no_answers_raises(mock_router):
    session = make_session_with_answers()
    for q in session.questions:
        q.asked = False
        q.answer = ""

    with pytest.raises(ValueError, match="No answered questions"):
        generate_summary(session)


def test_extract_bullets_finds_items():
    bullets = _extract_bullets(MOCK_SUMMARY_TEXT, "Key Findings")
    assert len(bullets) >= 1
    assert any("Excel" in b for b in bullets)


def test_extract_bullets_missing_section_returns_fallback():
    bullets = _extract_bullets("Some unrelated text", "Key Findings")
    assert bullets == ["(See full summary below)"]
