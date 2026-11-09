# Triage: Phase 0.1 Simplification

## Keep (no changes)

| Path | Decision | Reason |
|---|---|---|
| .env | keep | Environment variables, needed for dev |
| .env.example | keep | Template for env vars |
| .gitignore | keep | Git ignore rules |
| backend/.gitignore | keep | Backend-specific ignore rules |
| backend/app/crypto.py | keep | Encryption for tokens, Phase 0 work |
| backend/app/config.py | keep | Config management, Phase 0 work |
| backend/app/core/errors.py | keep | Error types, used by auth |
| backend/app/core/logging.py | keep | Logging setup, Phase 0 work |
| backend/app/auth.py (to be created) | keep | Google OAuth login/callback/session |
| backend/app/db/__init__.py | keep | Database module marker |
| backend/tests/test_crypto.py | keep | Existing crypto tests |
| package.json | keep | Workspace root config |
| apps/web/** | keep | Next.js web app, untouched for now |

## Simplify (modify, keep intent)

| Path | Decision | Reason |
|---|---|---|
| backend/app/main.py | simplify | Keep FastAPI app; remove MCP/AI endpoints; add create_all(); simplify to 4 tables |
| backend/app/db/models.py | simplify | Replace with 4 tables only: users, categories, threads, drafts |
| backend/app/db/session.py | simplify | Replace with sync engine + SessionLocal; no Alembic |
| backend/app/config.py | simplify | Keep existing; add DATABASE_URL, remove Alembic/Docker settings |
| backend/ai_pipeline/config.py | simplify | Reduce to model names, limits, prompt version; remove budgets |
| backend/ai_pipeline/llm/factory.py | simplify | Keep get_llm(), add call_with_retry() for 429; remove async complexity |
| backend/tests/conftest.py | simplify | Update fixtures for 4-table schema; remove MCP server fixtures |

## Delete (remove from main path, tag before-simplify preserves them)

| Path | Decision | Reason |
|---|---|---|
| backend/alembic/** | delete | No Alembic; using create_all() |
| backend/alembic/env.py | delete | Alembic config |
| backend/alembic/versions/000_initial.py | delete | Alembic migration |
| docker-compose.yml | delete | No Docker Compose for dev; SQLite local |
| backend/app/services/corrections.py | delete | Correction tracking moved to simple PATCH route |
| backend/app/services/categories.py | delete | Categories moved to simple routes |
| backend/app/core/__init__.py | delete | Core module no longer needed |
| backend/ai_pipeline/mcp_server/** | delete | MCP server not in main path |
| backend/ai_pipeline/mcp_server/__init__.py | delete | MCP server |
| backend/ai_pipeline/mcp_server/__main__.py | delete | MCP server |
| backend/ai_pipeline/mcp_server/server.py | delete | MCP server |
| backend/ai_pipeline/mcp_server/roles.py | delete | MCP roles |
| backend/ai_pipeline/mcp_server/backend/__init__.py | delete | MCP backend |
| backend/ai_pipeline/mcp_server/backend/base.py | delete | MCP abstract base |
| backend/ai_pipeline/mcp_server/backend/fake.py | delete | FakeBackend (will replace with FakeGmail) |
| backend/ai_pipeline/mcp_server/backend/gmail.py | delete | Gmail MCP backend (will simplify) |
| backend/ai_pipeline/mcp_server/fixtures/__init__.py | delete | MCP fixtures |
| backend/ai_pipeline/mcp_server/fixtures/threads.json | delete | MCP fixtures |
| backend/ai_pipeline/mcp_server/hash_utility.py | delete | Hash utils (not needed, no approval protocol) |
| backend/ai_pipeline/mcp_client/__init__.py | delete | MCP client |
| backend/ai_pipeline/mcp_client/client.py | delete | MCP client |
| backend/ai_pipeline/tracing/** | delete | Tracing (not needed for MVP) |
| backend/ai_pipeline/tracing/__init__.py | delete | Tracing |
| backend/ai_pipeline/tracing/callbacks.py | delete | Tracing callbacks |
| backend/ai_pipeline/sync.py | delete | Old sync module (will rewrite) |
| backend/ai_pipeline/classify.py | delete | Old classify module (will rewrite) |
| backend/ai_pipeline/categories.py | delete | Old categories module |
| backend/ai_pipeline/text_processing.py | delete | Old text processing |
| backend/ai_pipeline/__main__.py | delete | Old CLI entry |
| backend/ai_pipeline/cli.py | delete | Old CLI (will rewrite) |
| backend/ai_pipeline/llm/__init__.py | delete | LLM module marker (will recreate) |
| backend/ai_pipeline/llm/factory.py | delete | Old LLM factory (will rewrite) |

## Tracked files summary

Total tracked files: 87
- Keep: 13
- Simplify: 9
- Delete: 65

## Test against git ls-files

Run: `git ls-files | wc -l` to verify total tracked count.
Run the verification script in Phase 0.1 step 3.
