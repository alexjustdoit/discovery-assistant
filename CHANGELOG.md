# Changelog

## [Proposed — v1.0.0]

### Cross-page navigation
Add contextual nav shortcuts on each working page (Discovery Playbook, Touchpoint Log, Discovery Summary) so users can jump between pages for the active engagement without going through the sidebar or returning to Home.

### Delete a question
Allow removing a generated question from the playbook. Useful when AI generates something irrelevant to the specific engagement.

### Engagement mode indicator
Surface the pre-sales / post-sales mode visibly on the playbook and summary pages so context isn't lost once you're inside an engagement.

### Demo data review
Audit the two demo engagements (Meridian Financial SA, Evergreen Health TAM) to ensure questions, notes, touchpoints, and summaries read like authentic SA/TAM output. First thing any recruiter or hiring manager sees.

### Home page value prop
Rewrite the hero copy to lead with the problem and workflow, not a feature list. Relevant for portfolio/interview context.

### README rewrite
Lead with the problem and the thinking behind the tool. Restructure so the architecture and design decisions are visible, not just setup instructions.

---

## [0.4.0] — 2026-03-30

### Changed
- **Terminology refresh** — language updated to reflect long-term customer relationships: "Session" → "Engagement", "Question Bank" → "Discovery Playbook", "Meeting Log" → "Touchpoint Log" across all pages, nav, buttons, and copy
- Sidebar tagline updated: "Customer engagement intelligence for SAs and TAMs"
- Home page copy updated to match new terminology throughout

---

## [0.3.0] — 2026-03-30

### Added
- **Context-aware question update prompt** — after editing session context, users choose to regenerate unanswered questions for the new context, append net-new questions, or keep existing; answered questions always preserved
- **Follow-up quick-add** — "＋" button next to each follow-up probe promotes it directly into the question bank for that category; flagged as new
- **Inline question editing** — "✏" popover on every question lets users edit question text in place; saved immediately; reflected in summary and email generation
- **3 new tests** — `regenerate_unanswered_questions`: preserves answered, does not mutate session, passes answered texts to avoid duplication

---

## [0.2.0] — 2026-03-30

### Added
- **Home page** — landing experience with demo session cards and direct navigation into Question Bank, Meeting Log, or Discovery Summary; shows user-created sessions with a New Session CTA
- **Meeting Log** — log meeting touchpoints (date, title, attendees, notes) per session; timeline sorted newest-first; inline edit and delete
- **Meeting model** — `Meeting` added to `Session`; backward-compatible with existing session files
- **Session editing** — edit all context fields inline in Question Bank without leaving the page; mode locked after creation
- **Add custom question per-category** — compact input at the bottom of each category expander
- **Refresh Questions** — generates additional AI questions without touching answered ones; new questions visually flagged with a border and "✦ New" label
- **Demo sessions** — two pre-built sessions seeded at startup: Meridian Financial (pre-sales SA, mid-discovery) and Evergreen Health Systems (post-sales TAM, renewal at-risk with full summary and 3-meeting arc); idempotent seeding preserves user edits
- **Follow-up email draft** — generates a customer-ready post-call email from the summary via Claude Haiku; editable, persistent, auto-cleared on summary edit
- **Inline summary editing** — all four summary sections and the narrative editable before export
- **Streamlit Cloud deployment** — `st.secrets` injected into `os.environ` at startup; `secrets.toml.example` template included
- **Test coverage expanded to 42 tests** — email generation, additional question generation, demo session seeding, Meeting model, new Session fields

### Changed
- Navigation: Home is now the default landing page; Meeting Log added between Question Bank and Discovery Summary
- Demo sessions include meeting logs (2 for Meridian, 3 for Evergreen)
- Saved Sessions: shows last updated date instead of created date
- README: local setup split into Windows native, Mac/Linux, and WSL2 sections

### Fixed
- `_build_export` called before definition in `Discovery_Summary.py` — would crash when a summary existed

---

## [0.1.0] — 2026-03-29

### Added
- **New Session** — input customer context, select pre-sales (SA) or post-sales (TAM) mode, generate a categorized AI question bank
- **Question Bank** — questions grouped by category with follow-up probes; mark asked, capture notes, auto-save; progress bar
- **Discovery Summary** — AI-synthesized key findings, technical requirements, risks, and next steps; regenerate and export as Markdown
- **Saved Sessions** — browse, open, and delete past sessions
- **LLM routing** — Ollama (local) or GPT-5.4-nano / Claude Haiku via API; configurable via `.env`
- **Session persistence** — JSON storage in `data/sessions/`
- **21 tests** — models, store, question generation, summary generation (all LLM calls mocked)
- Pre-sales categories: Technical Fit, Integrations & Architecture, Security & Compliance, Stakeholder Mapping, POC Scoping, Competitive
- Post-sales categories: Expansion Signals, Health & Risk, Adoption Gaps, Renewal Readiness, Stakeholder Changes
