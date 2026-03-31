# Changelog

## [0.5.0] — 2026-03-30

### Added
- **Home page** — landing experience with demo session cards (mode, stage, question progress, meeting count) and direct navigation into Question Bank, Meeting Log, or Discovery Summary; shows user-created sessions below with a New Session CTA
- **Meeting Log** — log meeting touchpoints (date, title, attendees, notes) against any session; timeline sorted newest-first; inline edit and delete; log form auto-opens when no meetings exist yet
- **Meeting model** — `Meeting` (date, title, attendees, notes) added to `Session`; backward-compatible with existing session files

### Changed
- Navigation order: Home is now the default landing page
- Demo sessions now include meeting logs: Meridian Financial (2 meetings — intro call, technical deep-dive) and Evergreen Health (3 meetings — renewal kickoff, QBR, discovery deep-dive with Maria Santos)
- README: local setup split into three sections (Windows native, Mac/Linux, WSL2)

### Fixed
- Test count in README corrected from 21 to 42

---

## [0.4.0] — 2026-03-30

### Added
- **Follow-up email draft** — "Draft Follow-up Email" on the Discovery Summary page generates a customer-ready post-call email from the session summary using Claude Haiku; editable text area; Save / Regenerate / Clear controls; draft persists to `session.email_draft`; auto-cleared when summary is edited
- **Inline summary editing** — "Edit summary" expander on Discovery Summary; all four list sections (key findings, technical requirements, risks, next steps) and the full narrative are editable before export; leading dashes stripped on save
- **Streamlit Cloud deployment** — `st.secrets` injected into `os.environ` before `config.py` loads; works on both local and cloud without changes to config; `.streamlit/secrets.toml.example` template added; `secrets.toml` gitignored
- **Test coverage expanded to 42 tests** — email generation (return format, quality routing, summary guard, mode-specific prompts, prompt content), `generate_additional_questions` (fewer per category, no mutation, existing questions in prompt), `seed_demo_sessions` (copies files, idempotent, preserves user edits, missing dir), `email_draft` model field (default, roundtrip, backward compat)

### Fixed
- `_build_export` in `Discovery_Summary.py` was called before it was defined — would crash any time a summary existed; moved to top of file

---

## [0.3.0] — 2026-03-30

### Added
- **Session editing** — "Edit session context" expander in Question Bank; all `SessionContext` fields editable inline without leaving the page; mode is intentionally locked (changing it would invalidate the question bank)
- **Add custom question per-category** — compact text input at the bottom of each category expander; question is added to that category immediately on submit
- **Refresh Questions** — generates additional AI questions using `generate_additional_questions()`, which passes existing question texts in the prompt to avoid duplication and generates 2 per category (vs 4 for initial generation); never modifies answered questions
- **New question visual distinction** — questions added via Refresh or per-category Add are wrapped in a bordered container with a "✦ New" caption; category headers show a `· N new` count; distinction persists for the current page visit, resets on session switch
- **Demo sessions** — two pre-built JSON sessions in `data/demo_sessions/` (committed to git), seeded into `data/sessions/` at app startup via `seed_demo_sessions()` in `store.py`; seeding is idempotent (preserves user edits)
  - **Meridian Financial** — pre-sales SA, FinTech, Initial Discovery, 4/24 questions answered
  - **Evergreen Health Systems** — post-sales TAM, Healthcare, Renewal Q2 at-risk, 20/20 answered with full AI-generated summary

### Changed
- Saved Sessions: shows "Updated [date]" instead of "Created [date]"
- `generate_questions` refactored to accept `questions_per_category` and `existing_texts` parameters; `generate_additional_questions` added as a companion function

---

## [0.1.0] — 2026-03-29

### Added
- **New Session** — input company, industry, use case, tech stack, stage, and optional notes; select pre-sales (SA) or post-sales (TAM) mode; generates a categorized question bank via AI
- **Question Bank** — questions grouped by category with expandable follow-up probes; checkbox to mark asked, text area for notes; auto-saves on change; progress bar; "Generate Summary" CTA
- **Discovery Summary** — AI-synthesized key findings, technical requirements, risks and concerns, and recommended next steps; Regenerate and Export as Markdown controls
- **Saved Sessions** — browse all sessions with mode, stage, progress, and created date; Open and Delete per session
- **LLM routing** — `USE_LOCAL_LLM=true` routes to Ollama (local/free); `false` routes to GPT-5.4-nano for question generation and Claude Haiku for summaries; falls back to OpenAI if no Anthropic key
- **Session persistence** — sessions stored as JSON in `data/sessions/` (gitignored)
- **21 tests** — models, session persistence, question generation, summary generation (all LLM calls mocked)
- Pre-sales categories: Technical Fit, Integrations & Architecture, Security & Compliance, Stakeholder Mapping, POC Scoping, Competitive
- Post-sales categories: Expansion Signals, Health & Risk, Adoption Gaps, Renewal Readiness, Stakeholder Changes
