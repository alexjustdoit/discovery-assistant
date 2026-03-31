"""Tests for question generation feature (mocked LLM)."""
from unittest.mock import MagicMock, patch

import pytest

from data.models import DiscoveryMode, Session, SessionContext
from features.question_generation import (
    POST_SALES_CATEGORIES,
    PRE_SALES_CATEGORIES,
    QUESTIONS_PER_CATEGORY,
    REFRESH_QUESTIONS_PER_CATEGORY,
    _QuestionBank,
    _GeneratedQuestion,
    generate_questions,
    generate_additional_questions,
    regenerate_unanswered_questions,
)


def make_session(mode=DiscoveryMode.PRE_SALES) -> Session:
    return Session(
        mode=mode,
        context=SessionContext(
            company="Acme Corp",
            industry="FinTech",
            use_case="Automate compliance reporting",
            tech_stack="AWS, Snowflake",
            stage="Discovery",
        ),
    )


def _mock_question_bank(categories: list[str]) -> _QuestionBank:
    questions = []
    for cat in categories:
        for i in range(QUESTIONS_PER_CATEGORY):
            questions.append(
                _GeneratedQuestion(
                    category=cat,
                    text=f"Question {i+1} for {cat}?",
                    follow_ups=[f"Can you elaborate on {cat}?"],
                )
            )
    return _QuestionBank(questions=questions)


@patch("features.question_generation.router")
def test_generate_questions_pre_sales(mock_router):
    session = make_session(DiscoveryMode.PRE_SALES)
    expected_bank = _mock_question_bank(PRE_SALES_CATEGORIES)

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (expected_bank, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    questions = generate_questions(session)

    mock_router.get_provider.assert_called_once_with(quality_required=False)
    assert len(questions) == len(PRE_SALES_CATEGORIES) * QUESTIONS_PER_CATEGORY
    categories_seen = {q.category for q in questions}
    assert categories_seen == set(PRE_SALES_CATEGORIES)


@patch("features.question_generation.router")
def test_generate_questions_post_sales(mock_router):
    session = make_session(DiscoveryMode.POST_SALES)
    expected_bank = _mock_question_bank(POST_SALES_CATEGORIES)

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (expected_bank, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    questions = generate_questions(session)

    assert len(questions) == len(POST_SALES_CATEGORIES) * QUESTIONS_PER_CATEGORY
    categories_seen = {q.category for q in questions}
    assert categories_seen == set(POST_SALES_CATEGORIES)


@patch("features.question_generation.router")
def test_questions_have_follow_ups(mock_router):
    session = make_session()
    expected_bank = _mock_question_bank(PRE_SALES_CATEGORIES)

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (expected_bank, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    questions = generate_questions(session)
    assert all(len(q.follow_ups) > 0 for q in questions)


@patch("features.question_generation.router")
def test_questions_not_mutated_into_session(mock_router):
    """generate_questions should return questions, not mutate session.questions."""
    session = make_session()
    expected_bank = _mock_question_bank(PRE_SALES_CATEGORIES)

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (expected_bank, MagicMock())
    mock_router.get_provider.return_value = mock_provider

    assert session.questions == []
    generate_questions(session)
    assert session.questions == []


# ── generate_additional_questions ────────────────────────────────────────────

def _mock_refresh_bank(categories: list[str]) -> _QuestionBank:
    questions = []
    for cat in categories:
        for i in range(REFRESH_QUESTIONS_PER_CATEGORY):
            questions.append(
                _GeneratedQuestion(
                    category=cat,
                    text=f"Refresh question {i+1} for {cat}?",
                    follow_ups=[],
                )
            )
    return _QuestionBank(questions=questions)


@patch("features.question_generation.router")
def test_generate_additional_questions_returns_fewer_per_category(mock_router):
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_refresh_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    questions = generate_additional_questions(session)

    assert len(questions) == len(PRE_SALES_CATEGORIES) * REFRESH_QUESTIONS_PER_CATEGORY
    assert REFRESH_QUESTIONS_PER_CATEGORY < QUESTIONS_PER_CATEGORY


@patch("features.question_generation.router")
def test_generate_additional_questions_does_not_mutate_session(mock_router):
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_refresh_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    assert session.questions == []
    generate_additional_questions(session)
    assert session.questions == []


@patch("features.question_generation.router")
def test_generate_additional_questions_passes_existing_to_prompt(mock_router):
    """Existing question texts should appear in the user prompt sent to the LLM."""
    from data.models import Question
    session = make_session()
    session.questions = [
        Question(category="Technical Fit", text="What is your current solution?", asked=True, answer="We use Excel."),
        Question(category="Technical Fit", text="How long does reporting take?", asked=False),
    ]
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_refresh_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    generate_additional_questions(session)

    _, user_prompt, _ = mock_provider.complete_structured.call_args[0]
    assert "What is your current solution?" in user_prompt
    assert "How long does reporting take?" in user_prompt


# ── regenerate_unanswered_questions ──────────────────────────────────────────

@patch("features.question_generation.router")
def test_regenerate_preserves_answered_questions(mock_router):
    """Answered questions (asked=True or with notes) must not be dropped."""
    from data.models import Question
    session = make_session()
    answered_q = Question(category="Technical Fit", text="Current solution?", asked=True, answer="Excel.")
    noted_q = Question(category="Technical Fit", text="Pain points?", asked=False, answer="Month-end is slow.")
    unanswered_q = Question(category="Technical Fit", text="Future state?", asked=False)
    session.questions = [answered_q, noted_q, unanswered_q]

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_question_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    result = regenerate_unanswered_questions(session)

    result_ids = {q.id for q in result}
    assert answered_q.id in result_ids
    assert noted_q.id in result_ids


@patch("features.question_generation.router")
def test_regenerate_does_not_mutate_session(mock_router):
    """regenerate_unanswered_questions should return questions, not mutate session."""
    session = make_session()
    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_question_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    original_questions = list(session.questions)
    regenerate_unanswered_questions(session)
    assert session.questions == original_questions


@patch("features.question_generation.router")
def test_regenerate_excludes_answered_from_prompt(mock_router):
    """Answered question texts should appear in the existing_texts block to avoid duplication."""
    from data.models import Question
    session = make_session()
    answered_q = Question(category="Technical Fit", text="What is your current solution?", asked=True, answer="Excel.")
    session.questions = [answered_q]

    mock_provider = MagicMock()
    mock_provider.complete_structured.return_value = (_mock_question_bank(PRE_SALES_CATEGORIES), MagicMock())
    mock_router.get_provider.return_value = mock_provider

    regenerate_unanswered_questions(session)

    _, user_prompt, _ = mock_provider.complete_structured.call_args[0]
    assert "What is your current solution?" in user_prompt
