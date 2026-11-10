<div align="center">

# Inbox Copilot

**An AI email assistant that sorts your Gmail, drafts replies, and never sends anything without your click.**

Connect your Gmail account and Inbox Copilot classifies and summarizes your threads, flags the ones that need a reply, and writes draft responses from a one-line instruction. You review, edit, and press Send.

Built with **FastAPI, LangChain, Groq, SQLAlchemy, and the Gmail API**, Inbox Copilot focuses on a small, readable AI pipeline and a human-in-the-loop approval step.

![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20LangChain%20%7C%20Groq%20%7C%20Gmail%20API-2563eb)
![Python](https://img.shields.io/badge/Language-Python-3776AB)
![Status](https://img.shields.io/badge/Status-In%20development-orange)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

</div>

---

## Project status

Inbox Copilot is under active development. This table shows what works today.

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Project setup, database, encrypted token storage | Done |
| 1 | Google sign-in, Gmail sync (metadata only) | Done |
| 2 | Email classification pipeline (category, summary, needs-reply, priority) | In progress |
| 3 | Reply drafting and the approval-gated Send button | Planned |
| 4 | "Ask your inbox" LangChain agent | Planned |
| 5 | Web interface (Next.js) | Planned |
| 6 | Evaluation, safety tests, deployment | Planned |

Everything described below as a feature is labelled with its status.

## Overview

Email triage is repetitive: read, decide whether it matters, decide whether it needs a reply, write the reply. Most of that work follows a pattern a language model can handle, but sending mail on your behalf is a decision that should stay with you.

Inbox Copilot splits the work accordingly. A pipeline sorts and summarizes incoming mail, a drafter writes replies you can edit, and an agent answers questions about your inbox. Only one code path can send an email, and it requires you to click.

## Key features

- **Gmail sync** (done) — pulls your recent threads into a local database. Stores subject, sender, snippet, and dates; email bodies are fetched live and never stored.
- **Encrypted credentials** (done) — the Google refresh token is encrypted at rest, and access tokens are minted on demand.
- **AI classification** (in progress) — each thread gets a category, a short summary, a needs-reply flag, a priority, and a confidence score, using structured output validated by Pydantic.
- **Low-confidence handling** (in progress) — uncertain or failed classifications go to a "needs review" state instead of being guessed.
- **Reply drafting** (planned) — write a one-line instruction like "say yes, ask for the agenda" and get an editable draft.
- **Human-approved sending** (planned) — drafts are only sent when you press Send on that exact draft.
- **Inbox agent** (planned) — a LangChain agent with read-only search tools that answers questions like "Which emails need a reply?"
- **Prompt-injection awareness** (planned) — email content is treated as untrusted data throughout.

## Technical highlights

### A pipeline first, an agent where it fits

Classifying an email and drafting a reply have a fixed shape, so they are plain Python functions with one model call each. A LangChain agent is used only for the open-ended "ask your inbox" feature, where the model genuinely has to decide which tool to call next. This keeps the AI code easy to read, test, and debug.

### Structured output with validation

The classifier asks the model for a typed object and then validates it in code: the category must be one of the user's categories, priority must be 1 to 4, confidence must be between 0 and 1, and summaries are length-capped. A failed validation is retried once, then routed to review rather than crashing the run.

### Built for free-tier limits

Groq's free tier has tight per-minute token limits. The pipeline classifies one thread per call, trims and cleans bodies first, pauses between calls, retries on 429 responses, and commits after every thread, so a stopped run resumes where it left off.

### Cleaning email before the model sees it

Before classification, email text is converted from HTML (hidden elements dropped), Unicode-normalized, stripped of quoted replies and signatures, and redacted for one-time codes and long digit sequences. Redaction happens before truncation.

### One path to send (planned)

The agent has no send tool. Recipients are chosen by code from the thread, not by the model or the browser. A single API route sends a draft, and it flips the draft's status with a conditional update so a double click cannot send twice.

## Tech stack

| Layer | Technologies |
| --- | --- |
| API | Python, FastAPI |
| AI | LangChain, Groq (Llama models), Pydantic |
| Email | Gmail API, Google OAuth 2.0 |
| Database and ORM | SQLAlchemy 2; SQLite locally, Neon (PostgreSQL) when deployed |
| Security | Fernet-encrypted refresh tokens, signed session cookies |
| Frontend (planned) | Next.js, React, TypeScript, Tailwind CSS |
| Testing | pytest, a fake mailbox, a fake LLM |

## Architecture

```text
Gmail ---> sync ---> threads table
                         |
                         v
        Pipeline: clean text -> classify (1 LLM call) -> category, summary,
                                                         needs_reply, priority

You: "say yes, ask for the agenda"
        |
        v
Drafter: thread + instruction -> 1 LLM call -> draft (recipients chosen by code)
        |
        v
Review and edit ---> Send button ---> POST /api/drafts/{id}/send ---> Gmail

You: "Which emails need a reply?"
        |
        v
Agent (LangChain): search / list / read tools + save draft (cannot send)
```

## Run locally

### Prerequisites

- Python 3.12
- A Google Cloud project with the Gmail API enabled and an OAuth client (Web application)
- A Groq API key

### Setup

1. Clone the repository and create a virtual environment:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your values. Generate the two secrets with:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Create the local database (SQLite by default):

   ```bash
   python scripts/reset_db.py
   ```

4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Try the pipeline without touching your real inbox by using the built-in fake mailbox:

   ```bash
   MAILBOX_MODE=fake python -m ai_pipeline.cli classify
   ```

> The web interface is not built yet; for now the project runs through the API and the command line. Never commit `.env`, token files, or real email data.

## Project structure

```text
inbox-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Environment settings
│   │   ├── db.py            # Engine and sessions
│   │   ├── models.py        # Database tables
│   │   ├── auth.py          # Google OAuth, sessions, token encryption
│   │   ├── gmail.py         # Gmail client and fake mailbox
│   │   ├── sync.py          # Gmail to database sync
│   │   └── routes/          # API endpoints
│   ├── ai_pipeline/         # All AI code
│   │   ├── llm.py           # Model setup and retry on rate limits
│   │   ├── schemas.py       # Pydantic output schemas
│   │   ├── preprocess.py    # HTML cleanup, redaction, truncation
│   │   ├── classify.py      # Classification
│   │   ├── draft.py         # Draft writing (planned)
│   │   ├── tools.py         # Agent tools (planned)
│   │   ├── agent.py         # LangChain agent (planned)
│   │   ├── cli.py           # Run the pipeline from the terminal
│   │   └── prompts/         # Versioned prompt files
│   ├── data/                # Synthetic fixtures and eval set
│   ├── scripts/             # Database reset script
│   └── tests/
├── web/                     # Next.js app (planned)
└── docs/
```

## Engineering decisions

- **Plain functions over a framework for fixed steps:** classification and drafting are single calls, so there is nothing for an agent to decide.
- **Metadata-only storage:** bodies are fetched from Gmail when needed, which keeps stored data small and privacy-friendly.
- **Idempotent background work:** the classifier selects threads that are not yet classified and commits per thread, so re-runs and crashes are harmless.
- **Code, not the model, controls anything with consequences:** recipients, sending, and per-user data access are enforced in server code.
- **SQLite locally, Neon in production, no migration tool:** a four-table schema created at startup keeps development simple; schema changes are tracked by hand in `docs/schema-changes.md`.

## Roadmap

- Finish the classification pipeline and a manual category-correction endpoint.
- Draft generation and the approval-gated Send route.
- The "ask your inbox" agent with read-only tools.
- Web interface for browsing, drafting, and sending.
- A small labelled evaluation set with published accuracy, plus prompt-injection tests.
- Deployment on Neon, Render, and Vercel.
- Optional: expose the read-only tools through an MCP server.

## Limitations

- Email excerpts are sent to Groq for processing.
- While the Google app is in Testing mode, sign-in tokens expire after about seven days and need reconnecting.
- Free-tier model limits make large mailboxes classify slowly.

## License

Released under the [MIT License](LICENSE).
