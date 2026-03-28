from __future__ import annotations

import uuid
from datetime import datetime, timezone
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
    summary: Optional[DiscoverySummary] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def answered_questions(self) -> list[Question]:
        return [q for q in self.questions if q.asked and q.answer.strip()]

    def progress(self) -> tuple[int, int]:
        """Returns (asked, total)."""
        asked = sum(1 for q in self.questions if q.asked)
        return asked, len(self.questions)
