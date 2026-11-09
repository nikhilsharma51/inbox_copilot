# Triage: Phase 0.1 Simplification

## Summary

Removed 44 tracked files (Docker, Alembic, MCP, tracing, linting configs, budget/trace code). 
Kept 43 tracked files (4 tables, FastAPI, tests, Next.js web).

## Keep (no changes)

### Workspace root
- .env | keep | Environment variables, needed for dev
- .env.example | keep | Template for env vars
- .gitignore | keep | Git ignore rules
- package.json | keep | Workspace root config

### Apps (Next.js web)
- apps/web/.gitignore | keep | Web-specific ignore
- apps/web/README.md | keep | Web documentation
- apps/web/app/favicon.ico | keep | Web asset
- apps/web/app/globals.css | keep | Web styling
- apps/web/app/layout.tsx | keep | Web layout
- apps/web/app/page.tsx | keep | Web page
- apps/web/eslint.config.mjs | keep | Web linting (unused, but no harm)
- apps/web/next.config.ts | keep | Next.js config
- apps/web/package.json | keep | Web package config
- apps/web/pnpm-lock.yaml | keep | Web lock file
- apps/web/pnpm-workspace.yaml | keep | Workspace file
- apps/web/public/file.svg | keep | Web asset
- apps/web/public/globe.svg | keep | Web asset
- apps/web/public/next.svg | keep | Web asset
- apps/web/public/vercel.svg | keep | Web asset
- apps/web/public/window.svg | keep | Web asset
- apps/web/tsconfig.json | keep | Web TypeScript config

### Backend core
- backend/.gitignore | keep | Backend-specific ignore
- backend/app/config.py | keep | Config management, Phase 0 work
- backend/app/core/errors.py | keep | Error types, used by auth
- backend/app/core/logging.py | keep | Logging setup, Phase 0 work
- backend/app/crypto.py | keep | Encryption for tokens, Phase 0 work
- backend/app/db/__init__.py | keep | Database module marker
- backend/app/db/models.py | keep | SQLAlchemy models (will be simplified to 4 tables)
- backend/app/db/session.py | keep | Sync database session manager
- backend/app/main.py | keep | FastAPI app (rewritten, no dependencies)
- backend/ai_pipeline/__init__.py | keep | AI pipeline module marker
- backend/ai_pipeline/config.py | keep | AI config (model names, limits, prompts)
- backend/pyproject.toml | keep | Python dependencies (removed Alembic, ruff, pyright)
- backend/requirement.txt | keep | Legacy requirement file
- backend/tests/conftest.py | keep | Pytest fixtures and setup
- backend/tests/test_config.py | keep | Config tests
- backend/tests/test_crypto.py | keep | Crypto tests
- backend/tests/test_fake_backend.py | keep | FakeBackend tests (will adapt for FakeGmail)
- backend/tests/test_hash_utils.py | keep | Hash tests (can be removed later)
- backend/tests/test_llm_factory.py | keep | LLM factory tests (will be rewritten)
- backend/tests/test_mcp_client.py | keep | MCP client tests (can be removed later)
- backend/tests/test_roles.py | keep | Role tests (can be removed later)
- backend/tests/verify_gmail.py | keep | Gmail verification script
- docs/triage.md | keep | This file

## Deleted (removed from main path, tag before-simplify preserves them)

### Alembic migration system
- backend/alembic/env.py | delete | Alembic config
- backend/alembic/versions/000_initial.py | delete | Alembic migration

### MCP server and client
- backend/ai_pipeline/mcp_server/__init__.py | delete | MCP server module
- backend/ai_pipeline/mcp_server/__main__.py | delete | MCP server entry
- backend/ai_pipeline/mcp_server/server.py | delete | MCP server implementation
- backend/ai_pipeline/mcp_server/backend/__init__.py | delete | MCP backend module
- backend/ai_pipeline/mcp_server/backend/base.py | delete | Abstract MailBackend
- backend/ai_pipeline/mcp_server/backend/fake.py | delete | FakeBackend (will adapt as FakeGmail)
- backend/ai_pipeline/mcp_server/backend/gmail.py | delete | Gmail MCP backend
- backend/ai_pipeline/mcp_server/fixtures/__init__.py | delete | MCP fixtures module
- backend/ai_pipeline/mcp_server/fixtures/threads.json | delete | Test fixtures (reusable as JSON)
- backend/ai_pipeline/mcp_server/hash_utility.py | delete | Hash utils for approval protocol
- backend/ai_pipeline/mcp_server/roles.py | delete | MCP role system
- backend/ai_pipeline/mcp_client/__init__.py | delete | MCP client module
- backend/ai_pipeline/mcp_client/client.py | delete | MCP client implementation

### AI pipeline old modules
- backend/ai_pipeline/__main__.py | delete | Old CLI entry
- backend/ai_pipeline/cli.py | delete | Old CLI implementation
- backend/ai_pipeline/sync.py | delete | Old sync module (will rewrite)
- backend/ai_pipeline/classify.py | delete | Old classify module (will rewrite)
- backend/ai_pipeline/categories.py | delete | Old categories module
- backend/ai_pipeline/text_processing.py | delete | Old text processing
- backend/ai_pipeline/llm/__init__.py | delete | Old LLM module marker
- backend/ai_pipeline/llm/factory.py | delete | Old LLM factory
- backend/ai_pipeline/tracing/__init__.py | delete | Tracing module
- backend/ai_pipeline/tracing/callbacks.py | delete | Tracing callbacks

### Services
- backend/app/core/__init__.py | delete | Core module no longer needed
- backend/app/services/categories.py | delete | Categories moved to simple routes
- backend/app/services/corrections.py | delete | Correction tracking moved to simple PATCH route

### Infrastructure
- docker-compose.yml | delete | No Docker Compose for dev; SQLite local

## Notes

- `before-simplify` tag preserves all deleted code for reference
- Use `git show before-simplify:backend/ai_pipeline/mcp_server/backend/fake.py` to recover FakeBackend pattern
- Use `git show before-simplify:backend/ai_pipeline/mcp_server/fixtures/threads.json` to recover test fixtures
- Next.js web app is untouched (separate frontend, can iterate independently)
- All references to deleted modules have been removed from main.py
- pyproject.toml cleaned of Alembic, ruff, pyright, import-linter dependencies and configs
- Backend now uses 4-table schema (users, categories, threads, drafts) instead of 9+
