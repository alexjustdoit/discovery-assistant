"""
Generate discovery questions from session context.
Uses gpt-5.4-nano (cheap) — high volume, structured output.
"""
from __future__ import annotations

from pydantic import BaseModel

from data.models import DiscoveryMode, Question, Session, SessionContext
from llm.router import router

# Categories per mode
PRE_SALES_CATEGORIES = [
    "Technical Fit",
    "Integrations & Architecture",
    "Security & Compliance",
    "Stakeholder Mapping",
    "POC Scoping",
    "Competitive",
]

POST_SALES_CATEGORIES = [
    "Expansion Signals",
    "Health & Risk",
    "Adoption Gaps",
    "Renewal Readiness",
    "Stakeholder Changes",
]

QUESTIONS_PER_CATEGORY = 4
REFRESH_QUESTIONS_PER_CATEGORY = 2


class _GeneratedQuestion(BaseModel):
    category: str
    text: str
    follow_ups: list[str] = []


class _QuestionBank(BaseModel):
    questions: list[_GeneratedQuestion]


def _build_system(mode: DiscoveryMode) -> str:
    if mode == DiscoveryMode.PRE_SALES:
        return (
            "You are an expert Solutions Architect helping prepare for a pre-sales discovery call. "
            "Generate targeted, open-ended discovery questions that uncover technical requirements, "
            "integration complexity, buying process, and competitive landscape. "
            "Questions should feel natural in a conversation, not like an audit."
        )
    return (
        "You are an expert Technical Account Manager preparing for a customer discovery conversation. "
        "Generate targeted, open-ended questions that uncover expansion opportunities, adoption gaps, "
        "health signals, renewal risks, and stakeholder changes. "
        "Questions should feel consultative, not like a check-in checklist."
    )


def _build_user(context: SessionContext, mode: DiscoveryMode, per_category: int, existing_texts: list[str] | None = None) -> str:
    categories = PRE_SALES_CATEGORIES if mode == DiscoveryMode.PRE_SALES else POST_SALES_CATEGORIES
    existing_block = ""
    if existing_texts:
        formatted = "\n".join(f"- {t}" for t in existing_texts)
        existing_block = f"\nDo not duplicate or closely restate any of these existing questions:\n{formatted}\n"
    return f"""
Generate exactly {per_category} discovery questions for each of these categories:
{", ".join(categories)}

Customer/Prospect context:
- Company: {context.company}
- Industry: {context.industry}
- Use case: {context.use_case}
- Tech stack: {context.tech_stack}
- Stage: {context.stage}
{f"- Additional context: {context.notes}" if context.notes else ""}
{existing_block}
For each question, also provide 1-2 follow-up probes (shorter questions to dig deeper if the answer is vague).
Return all questions across all categories.
""".strip()


def generate_questions(session: Session) -> list[Question]:
    """Generate the initial question bank for a session (does not mutate session)."""
    provider = router.get_provider(quality_required=False)
    system = _build_system(session.mode)
    user = _build_user(session.context, session.mode, per_category=QUESTIONS_PER_CATEGORY)

    bank, _ = provider.complete_structured(system, user, _QuestionBank)

    return [
        Question(category=q.category, text=q.text, follow_ups=q.follow_ups)
        for q in bank.questions
    ]


def generate_additional_questions(session: Session) -> list[Question]:
    """Generate supplementary questions that avoid duplicating existing ones (does not mutate session)."""
    provider = router.get_provider(quality_required=False)
    system = _build_system(session.mode)
    existing_texts = [q.text for q in session.questions]
    user = _build_user(
        session.context,
        session.mode,
        per_category=REFRESH_QUESTIONS_PER_CATEGORY,
        existing_texts=existing_texts,
    )

    bank, _ = provider.complete_structured(system, user, _QuestionBank)

    return [
        Question(category=q.category, text=q.text, follow_ups=q.follow_ups)
        for q in bank.questions
    ]
