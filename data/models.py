from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DiscoveryMode(str, Enum):
    PRE_SALES = "pre_sales"
    POST_SALES = "post_sales"


class QuestionCategory(str, Enum):
    # Pre-sales categories
    TECHNICAL_FIT = "Technical Fit"
    INTEGRATIONS = "Integrations & Architecture"
    SECURITY = "Security & Compliance"
    STAKEHOLDERS = "Stakeholder Mapping"
    POC = "POC Scoping"
    COMPETITIVE = "Competitive"
    # Post-sales categories
    EXPANSION = "Expansion Signals"
    HEALTH_RISK = "Health & Risk"
    ADOPTION = "Adoption Gaps"
    RENEWAL = "Renewal Readiness"
    STAKEHOLDER_CHANGES = "Stakeholder Changes"


class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    text: str
    asked: bool = False
    answer: str = ""
    follow_ups: list[str] = Field(default_factory=list)


class SessionContext(BaseModel):
    company: str
    industry: str
    use_case: str
    tech_stack: str
    stage: str  # e.g. "Discovery", "POC", "Renewal Q2", "At-risk"
    notes: str = ""  # freeform additional context


class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    title: str
    attendees: str = ""
    notes: str = ""


class DiscoverySummary(BaseModel):
    key_findings: list[str]
    technical_requirements: list[str]
    risks_and_concerns: list[str]
    recommended_next_steps: list[str]
    raw_text: str  # full narrative summary


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: DiscoveryMode
    context: SessionContext
    questions: list[Question] = Field(default_factory=list)
    meetings: list[Meeting] = Field(default_factory=list)
    summary: Optional[DiscoverySummary] = None
    email_draft: Optional[str] = None
    archived: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def answered_questions(self) -> list[Question]:
        return [q for q in self.questions if q.asked and q.answer.strip()]

    def progress(self) -> tuple[int, int]:
        """Returns (asked, total)."""
        asked = sum(1 for q in self.questions if q.asked)
        return asked, len(self.questions)

    def discovery_depth(self) -> float:
        """
        Composite 0–1 score: how well-understood this engagement is.
        60% — questions with substantive notes / total questions
        20% — categories with at least one answered question / total categories
        10% — touchpoints logged (caps at 3)
        10% — summary exists
        """
        if not self.questions:
            return 0.0
        notes_score = sum(1 for q in self.questions if q.answer.strip()) / len(self.questions)
        categories = {q.category for q in self.questions}
        covered = {q.category for q in self.questions if q.answer.strip()}
        coverage_score = len(covered) / len(categories) if categories else 0.0
        touchpoint_score = min(len(self.meetings), 3) / 3
        summary_score = 1.0 if self.summary is not None else 0.0
        return (
            0.60 * notes_score
            + 0.20 * coverage_score
            + 0.10 * touchpoint_score
            + 0.10 * summary_score
        )
