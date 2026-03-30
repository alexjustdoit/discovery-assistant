"""
Generate a post-call follow-up email from a session summary.
Uses Claude Haiku (quality_required=True) — customer-facing output.
"""
from __future__ import annotations

from pydantic import BaseModel

from data.models import DiscoveryMode, Session
from llm.router import router


class _EmailDraft(BaseModel):
    subject: str
    body: str


def _build_system(mode: DiscoveryMode) -> str:
    if mode == DiscoveryMode.PRE_SALES:
        return (
            "You are an expert Solutions Architect writing a follow-up email after a pre-sales discovery call. "
            "Your emails are professional, concise, and demonstrate that you were genuinely listening. "
            "You recap key themes, confirm next steps clearly, and close with momentum. "
            "Never sound salesy. Sound like a trusted technical advisor."
        )
    return (
        "You are an expert Technical Account Manager writing a follow-up email after a customer discovery call. "
        "Your emails are warm, consultative, and action-oriented. "
        "You recap what you heard, confirm any commitments made, and close with clear next steps. "
        "Sound like a partner, not a vendor."
    )


def _build_user(session: Session) -> str:
    s = session.summary
    ctx = session.context

    findings = "\n".join(f"- {f}" for f in s.key_findings)
    next_steps = "\n".join(f"- {n}" for n in s.recommended_next_steps)
    risks = "\n".join(f"- {r}" for r in s.risks_and_concerns)

    answered = session.answered_questions()
    open_questions = [q.text for q in session.questions if not q.asked]
    open_block = ""
    if open_questions[:3]:
        open_block = "\nOpen questions not yet covered:\n" + "\n".join(f"- {q}" for q in open_questions[:3])

    return f"""
Write a follow-up email after a discovery call with {ctx.company}.

Context:
- Industry: {ctx.industry}
- Stage: {ctx.stage}
- Use case: {ctx.use_case}

Key findings from the call:
{findings}

Risks / concerns surfaced:
{risks}

Agreed next steps:
{next_steps}
{open_block}

Guidelines:
- Subject line should be specific, not generic ("Following up on our call" is bad)
- Opening: brief thanks, reference what was discussed (not a generic opener)
- Body: 2-3 short paragraphs — recap themes, restate next steps with owners/timing if known, one open question if relevant
- Close: warm but action-oriented, propose or confirm the next meeting
- Tone: professional but human, not corporate or salesy
- Length: concise — under 200 words for the body
""".strip()


def generate_followup_email(session: Session) -> str:
    """Generate a follow-up email draft. Returns the full email as a string (Subject + body)."""
    if session.summary is None:
        raise ValueError("Cannot generate email without a summary — generate the discovery summary first.")

    provider = router.get_provider(quality_required=True)
    system = _build_system(session.mode)
    user = _build_user(session)

    draft, _ = provider.complete_structured(system, user, _EmailDraft)
    return f"Subject: {draft.subject}\n\n{draft.body}"
