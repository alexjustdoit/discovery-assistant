# Discovery Assistant

AI-powered technical discovery for pre-sales (SA) and post-sales (TAM) workflows.

Paste in context about a customer or prospect, get a tailored question bank, capture notes during the call, and generate a shareable discovery summary.

## Features

- **Pre-sales mode (SA):** Technical fit, integrations & architecture, security & compliance, stakeholder mapping, POC scoping, competitive
- **Post-sales mode (TAM):** Expansion signals, health & risk, adoption gaps, renewal readiness, stakeholder changes
- **AI question generation** — context-aware, categorized, with follow-up probes
- **Discovery summary** — synthesizes your notes into key findings, technical requirements, risks, and next steps
- **Markdown export** — shareable summary + full Q&A notes
- **Session persistence** — all sessions saved locally as JSON

## Stack

Python · Streamlit · Pydantic · OpenAI GPT-5.4-nano · Claude Haiku 4.5 · Ollama (local)

LLM routing: `USE_LOCAL_LLM=true` → Ollama (free/local) · `false` → GPT-5.4-nano for questions, Claude Haiku for summaries

## Setup (WSL2)

```bash
git clone https://github.com/alexjustdoit/discovery-assistant.git
cd discovery-assistant
cp .env.example .env   # fill in your API keys
pip install -r requirements.txt
streamlit run app/streamlit_app.py --server.address 0.0.0.0
```

Access via WSL2 IP on port 8501. To find your WSL2 IP:

```bash
hostname -I | awk '{print $1}'
```

Then open `http://<WSL2-IP>:8501` in your Windows browser.

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
USE_LOCAL_LLM=true          # true = Ollama, false = OpenAI + Claude API
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

When `USE_LOCAL_LLM=false`, `OPENAI_API_KEY` is required. `ANTHROPIC_API_KEY` is optional — if set, summaries use Claude Haiku; otherwise falls back to OpenAI.

## Running Tests

```bash
pytest tests/ -v
```

21 tests covering models, session persistence, question generation, and summary generation (all LLM calls mocked).

## Pages

| Page | Description |
|---|---|
| New Session | Input context and generate discovery questions |
| Question Bank | Work through questions, mark asked, capture notes |
| Discovery Summary | AI-generated debrief + markdown export |
| Saved Sessions | Browse and manage past sessions |
