"""Tests for question generation feature (mocked LLM)."""
from unittest.mock import MagicMock, patch

import pytest

from data.models import DiscoveryMode, Session, SessionContext
from features.question_generation import (
    POST_SALES_CATEGORIES,
    PRE_SALES_CATEGORIES,
    QUESTIONS_PER_CATEGORY,
    _QuestionBank,
    _GeneratedQuestion,
    generate_questions,
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
