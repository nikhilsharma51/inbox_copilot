 <div align="center">

# Inbox Copilot

**An AI email assistant that sorts your Gmail, drafts replies, and never sends anything without your click.**

Connect your Gmail account and Inbox Copilot classifies and summarizes your threads, flags the ones that need a reply, and writes draft responses from a one-line instruction. You review, edit, and press Send.

Built with **FastAPI, LangChain, Groq, SQLAlchemy, Gmail API, and Next.js**, Inbox Copilot focuses on a small, readable AI pipeline and a human-in-the-loop approval step.

![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20LangChain%20%7C%20Groq%20%7C%20Next.js-2563eb)
![Python](https://img.shields.io/badge/Language-Python-3776AB)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%20%7C%20TypeScript-black)
![Status](https://img.shields.io/badge/Status-In%20development-orange)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

</div>

---

## Project status

Inbox Copilot is under active development. This table shows the current implementation status.

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Project setup, database, encrypted token storage | Done |
| 1 | Google sign-in, Gmail sync (metadata only) | Done |
| 2 | Email classification pipeline (category, summary, needs-reply, priority) | In progress |
| 3 | Reply drafting and the approval-gated Send button | Planned |
| 4 | "Ask your inbox" LangChain agent | Planned |
| 5 | Web interface (Next.js) and API integration | In progress |
| 6 | Evaluation, safety tests, deployment | Planned |

Everything described below as a feature is labelled with its status.

## Overview

Email triage is repetitive: read, decide whether it matters, decide whether it needs a reply, write the reply. Most of that work follows a pattern a language model can handle, but sending mail on your behalf is a decision that should stay with you.

Inbox Copilot splits the work accordingly. A pipeline sorts and summarizes incoming mail, a drafter writes replies you can edit, and an agent answers questions about your inbox. The frontend provides the interface for interacting with these capabilities while keeping consequential actions under your control.

Only one code path can send an email, and it requires you to click.

## Key features

- **Gmail sync** (done) — pulls your recent threads into a local database. Stores subject, sender, snippet, and dates; email bodies are fetched live and never stored.
- **Encrypted credentials** (done) — the Google refresh token is encrypted at rest, and access tokens are minted on demand.
- **AI classification** (in progress) — each thread gets a category, a short summary, a needs-reply flag, a priority, and a confidence score, using structured output validated by Pydantic.
- **Low-confidence handling** (in progress) — uncertain or failed classifications go to a "needs review" state instead of being guessed.
- **Web interface** (in progress) — Next.js frontend for interacting with the inbox and integrating backend API functionality.
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

### One path to send

The agent has no send tool. Recipients are chosen by code from the thread, not by the model or the browser. A single API route sends a draft, and it flips the draft's status with a conditional update so a double click cannot send twice.

## Tech stack

| Layer | Technologies |
| --- | --- |
| API | Python, FastAPI |
| AI | LangChain, Groq (Llama models), Pydantic |
| Email | Gmail API, Google OAuth 2.0 |
| Database and ORM | SQLAlchemy 2; SQLite locally, Neon (PostgreSQL) when deployed |
| Security | Fernet-encrypted refresh tokens, signed session cookies |
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS |
| Package manager | pnpm |
| Testing | pytest, a fake mailbox, a fake LLM |

## Architecture

```text
                       Gmail
                         |
                         v
                    Sync service
                         |
                         v
                    Threads table
                         |
                         v
               Classification pipeline
                         |
              Clean -> Classify -> Validate
                         |
                         v
             Category, Summary, Priority,
                  Needs-reply flag

                         |
                         v
              FastAPI Backend
                         |
                    REST API
                         |
                         v
               Next.js Frontend
                         |
              Browse and manage inbox
                         |
             +-----------+-----------+
             |                       |
             v                       v
        Reply drafting          Inbox agent
             |                       |
             v                       v
        Review and edit       Search / Read tools
             |
             v
        Send button
             |
             v
      POST /api/drafts/{id}/send
             |
             v
           Gmail
```

## Run locally

### Prerequisites

- Python 3.12
- Node.js (compatible with your Next.js version)
- pnpm
- A Google Cloud project with the Gmail API enabled and an OAuth client (Web application)
- A Groq API key

### Backend setup

1. Clone the repository and create a virtual environment:

   ```bash
   cd backend
   python -m venv .venv
   ```

   Activate it:

   ```powershell
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

   Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your values. Generate the two secrets with:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Create the local database:

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

### Frontend setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   pnpm install
   ```

3. Create `.env.local` and configure the backend API URL:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Start the development server:

   ```bash
   pnpm dev
   ```

The frontend will be available at `http://localhost:3000`.

> Start the backend and frontend in separate terminals. Never commit `.env`, `.env.local`, token files, or real email data.

## Project structure

```text
inbox-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── auth.py
│   │   ├── gmail.py
│   │   ├── sync.py
│   │   └── routes/
│   ├── ai_pipeline/
│   │   ├── llm.py
│   │   ├── schemas.py
│   │   ├── preprocess.py
│   │   ├── classify.py
│   │   ├── draft.py
│   │   ├── tools.py
│   │   ├── agent.py
│   │   ├── cli.py
│   │   └── prompts/
│   ├── data/
│   ├── scripts/
│   └── tests/
│
├── frontend/
│   ├── app/                 # Next.js App Router
│   ├── public/
│   ├── package.json
│   └── ...
│
└── docs/
```

## Engineering decisions

- **Plain functions over a framework for fixed steps:** classification and drafting are single calls, so there is nothing for an agent to decide.
- **Metadata-only storage:** bodies are fetched from Gmail when needed, which keeps stored data small and privacy-friendly.
- **Idempotent background work:** the classifier selects threads that are not yet classified and commits per thread, so re-runs and crashes are harmless.
- **Code, not the model, controls anything with consequences:** recipients, sending, and per-user data access are enforced in server code.
- **SQLite locally, Neon in production, no migration tool:** a four-table schema created at startup keeps development simple; schema changes are tracked by hand in `docs/schema-changes.md`.
- **Separate frontend and backend:** Next.js handles the user interface while FastAPI owns authentication, data access, business logic, and AI processing.

## Roadmap

- Finish the classification pipeline and a manual category-correction endpoint.
- Build the Next.js inbox interface and integrate it with the FastAPI backend.
- Draft generation and the approval-gated Send route.
- The "ask your inbox" agent with read-only tools.
- Complete the frontend experience for browsing, classifying, drafting, and sending emails.
- A small labelled evaluation set with published accuracy, plus prompt-injection tests.
- Deployment on Neon, Render, and Vercel.
- Optional: expose the read-only tools through an MCP server.

## Limitations

- Email excerpts are sent to Groq for processing.
- While the Google app is in Testing mode, sign-in tokens expire after about seven days and need reconnecting.
- Free-tier model limits make large mailboxes classify slowly.

## License

Released under the [MIT License](LICENSE).
