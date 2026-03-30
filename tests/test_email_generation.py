"""Tests for email generation feature (mocked LLM)."""
from unittest.mock import MagicMock, patch

import pytest

from data.models import DiscoveryMode, DiscoverySummary, Question, Session, SessionContext
from features.email_generation import _EmailDraft, generate_followup_email


def make_session(mode=DiscoveryMode.PRE_SALES) -> Session:
    session = Session(
        mode=mode,
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
            text="What does your current workflow look like?",
            asked=True,
            answer="We use Excel, takes 3 days per quarter.",
        ),
    ]
    session.summary = DiscoverySummary(
        key_findings=["Excel-based process is slow", "Strong Snowflake fit"],
        technical_requirements=["Native Snowflake connector", "Oracle legacy integration"],
        risks_and_concerns=["Oracle may complicate integration"],
        recommended_next_steps=["Schedule technical deep-dive", "Send Snowflake connector docs"],
        raw_text="They are a strong fit with clear pain around manual reporting.",
    )
    return session


MOCK_EMAIL_DRAFT = _EmailDraft(
    subject="Acme Corp — Discovery Follow-up",
    body="Hi Marcus,\n\nThanks for the time today. Key takeaways: ...\n\nNext steps: ...",
)


@patch("features.email_generation.router")
def test_generate_followup_email_returns_formatted_string(mock_router):
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (MOCK_EMAIL_DRAFT, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    result = generate_followup_email(session)

    assert isinstance(result, str)
    assert result.startswith("Subject:")
    assert MOCK_EMAIL_DRAFT.subject in result
    assert MOCK_EMAIL_DRAFT.body in result


@patch("features.email_generation.router")
def test_generate_followup_email_uses_quality_provider(mock_router):
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (MOCK_EMAIL_DRAFT, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    generate_followup_email(session)

    mock_router.get_provider.assert_called_once_with(quality_required=True)


def test_generate_followup_email_requires_summary():
    session = make_session()
    session.summary = None

    with pytest.raises(ValueError, match="summary"):
        generate_followup_email(session)


@patch("features.email_generation.router")
def test_generate_followup_email_pre_sales_system_prompt(mock_router):
    session = make_session(mode=DiscoveryMode.PRE_SALES)
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (MOCK_EMAIL_DRAFT, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    generate_followup_email(session)

    system_prompt = mock_provider.complete_structured.call_args[0][0]
    assert "Solutions Architect" in system_prompt


@patch("features.email_generation.router")
def test_generate_followup_email_post_sales_system_prompt(mock_router):
    session = make_session(mode=DiscoveryMode.POST_SALES)
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (MOCK_EMAIL_DRAFT, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    generate_followup_email(session)

    system_prompt = mock_provider.complete_structured.call_args[0][0]
    assert "Technical Account Manager" in system_prompt


@patch("features.email_generation.router")
def test_generate_followup_email_includes_session_context_in_prompt(mock_router):
    """Company name, next steps, and findings should appear in the user prompt."""
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (MOCK_EMAIL_DRAFT, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    generate_followup_email(session)

    user_prompt = mock_provider.complete_structured.call_args[0][1]
    assert "Acme Corp" in user_prompt
    assert "Schedule technical deep-dive" in user_prompt
    assert "Excel-based process is slow" in user_prompt
