"""
Synthesize session notes into a discovery summary.
Uses Claude Haiku (quality_required=True) — customer-facing output needs polish.
"""
from __future__ import annotations

from data.models import DiscoverySummary, Session
from llm.router import router


def _build_system(mode_label: str) -> str:
    return (
        f"You are an expert {mode_label} writing a concise discovery summary after a customer call. "
        "Your output will be shared internally and possibly with the customer. "
        "Be specific, actionable, and professional. Avoid filler language."
    )


def _build_user(session: Session) -> str:
    mode_label = "Solutions Architect" if session.mode.value == "pre_sales" else "Technical Account Manager"
    answered = session.answered_questions()

    if not answered:
        raise ValueError("No answered questions to summarize.")

    qa_block = "\n\n".join(
        f"[{q.category}] {q.text}\nAnswer: {q.answer}" for q in answered
    )

    return f"""
Discovery session for: {session.context.company} ({session.context.industry})
Use case: {session.context.use_case}
Tech stack: {session.context.tech_stack}
Stage: {session.context.stage}
{f"Additional context: {session.context.notes}" if session.context.notes else ""}

--- Q&A from the call ---
{qa_block}

Write a discovery summary with these four sections:
1. Key Findings (3-5 bullet points — what you learned)
2. Technical Requirements (what they need from a solution)
3. Risks & Concerns (blockers, red flags, open questions)
4. Recommended Next Steps (specific, time-bound actions)

After the four sections, write a 2-3 sentence narrative overview suitable for sharing.
""".strip()


def generate_summary(session: Session) -> DiscoverySummary:
    """Generate and return a DiscoverySummary (does not mutate session)."""
    mode_label = "Solutions Architect" if session.mode.value == "pre_sales" else "Technical Account Manager"
    provider = router.get_provider(quality_required=True)
    system = _build_system(mode_label)
    user = _build_user(session)

    response = provider.complete(system, user, temperature=0.4)
    raw = response.content

    # Parse sections out of the free-text response
    key_findings = _extract_bullets(raw, "Key Findings")
    technical_requirements = _extract_bullets(raw, "Technical Requirements")
    risks = _extract_bullets(raw, "Risks")
    next_steps = _extract_bullets(raw, "Next Steps")

    return DiscoverySummary(
        key_findings=key_findings,
        technical_requirements=technical_requirements,
        risks_and_concerns=risks,
        recommended_next_steps=next_steps,
        raw_text=raw,
    )


def _extract_bullets(text: str, section_name: str) -> list[str]:
    """Extract bullet points from a named section of free-form LLM output."""
    lines = text.split("\n")
    in_section = False
    bullets = []

    for line in lines:
        stripped = line.strip()
        if section_name.lower() in stripped.lower() and (stripped.startswith("#") or stripped[0].isdigit()):
            in_section = True
            continue
        if in_section:
            # Stop at next numbered section heading
            if stripped and stripped[0].isdigit() and "." in stripped[:3]:
                break
            if stripped.startswith("#"):
                break
            if stripped.startswith(("-", "*", "•")) or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == "."):
                bullet = stripped.lstrip("-*•0123456789. ").strip()
                if bullet:
                    bullets.append(bullet)

    return bullets if bullets else [f"(See full summary below)"]
