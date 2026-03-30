# Discovery Assistant

AI-powered technical discovery for pre-sales (SA) and post-sales (TAM) workflows.

Paste in context about a customer or prospect, get a tailored question bank, capture notes during the call, and generate a shareable summary and follow-up email — all in one place.

## Features

- **Pre-sales mode (SA):** Technical fit, integrations & architecture, security & compliance, stakeholder mapping, POC scoping, competitive
- **Post-sales mode (TAM):** Expansion signals, health & risk, adoption gaps, renewal readiness, stakeholder changes
- **AI question generation** — context-aware, categorized, with follow-up probes
- **Session editing** — update context mid-session, add custom questions per-category, refresh with additional AI questions (never overwrites answered questions)
- **Discovery summary** — AI-synthesized key findings, technical requirements, risks, and next steps; fully editable before sharing
- **Follow-up email draft** — generates a ready-to-send post-call email from the summary; editable and persistent
- **Markdown export** — full summary + Q&A notes
- **Demo sessions** — two pre-loaded realistic sessions (Meridian Financial SA, Evergreen Health TAM) ready to explore on first launch
- **Session persistence** — sessions saved as JSON; browse, resume, or delete from Saved Sessions

## Stack

Python · Streamlit · Pydantic · OpenAI GPT-5.4-nano · Claude Haiku 4.5 · Ollama (local)

LLM routing: `USE_LOCAL_LLM=true` → Ollama (free/local) · `false` → GPT-5.4-nano for questions, Claude Haiku for summaries and email drafts

## Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set **Main file path:** `app/streamlit_app.py`
4. Open **Advanced settings → Secrets** and paste:

```toml
USE_LOCAL_LLM = "false"
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
```

5. Deploy — demo sessions load automatically on first run

> Sessions are stored on Streamlit Cloud's ephemeral filesystem and reset on each restart. For a portfolio demo this is fine — the demo sessions always re-seed.

## Local Setup (WSL2 / Mac)

```bash
git clone https://github.com/alexjustdoit/discovery-assistant.git
cd discovery-assistant
cp .env.example .env          # fill in your API keys
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**WSL2 only:** to access from Windows browser, run with `--server.address 0.0.0.0` and find your WSL2 IP:

```bash
streamlit run app/streamlit_app.py --server.address 0.0.0.0
hostname -I | awk '{print $1}'   # open http://<this-ip>:8501 in Windows
```

> In new terminal sessions, always activate the venv first: `source venv/bin/activate`

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
USE_LOCAL_LLM=true          # true = Ollama (free/local), false = OpenAI + Claude API
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

When `USE_LOCAL_LLM=false`, `OPENAI_API_KEY` is required. `ANTHROPIC_API_KEY` is optional — if set, summaries and email drafts use Claude Haiku; otherwise falls back to OpenAI.

## Running Tests

```bash
pytest tests/ -v
```

21 tests covering models, session persistence, question generation, and summary generation (all LLM calls mocked).

## Pages

| Page | Description |
|---|---|
| New Session | Input context and generate the initial question bank |
| Question Bank | Work through questions, capture notes, add custom questions, refresh with AI |
| Discovery Summary | AI-generated debrief, inline editing, follow-up email draft, markdown export |
| Saved Sessions | Browse, resume, and delete past sessions |
