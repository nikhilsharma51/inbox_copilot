# AI Pipeline Setup - Dependency Resolution

## Status

Updated `pyproject.toml` with compatible LangChain versions to resolve conflicts.

## Version Compatibility

The following versions work together:
- `langchain==0.1.14` (older stable, works with core 0.1.44)
- `langchain-core==0.1.44` (compatible with langchain 0.1.14)
- `langchain-groq==0.1.4` (API wrapper for Groq)
- `mcp==1.1.3` (Model Context Protocol)
- `langchain-mcp-adapters==0.3.0` (Bridge between LangChain and MCP)

**Note:** These are "legacy" versions from late 2024, chosen for stability over cutting-edge features. When the codebase is tested and stable, you can upgrade to the latest versions with careful testing.

## Installation Steps

### 1. Clean up conflicting installation

```bash
cd backend
pip uninstall -y langchain-core langchain langchain-groq langchain-community
pip cache purge
```

### 2. Install all dependencies from pyproject.toml

```bash
pip install -e ".[dev]"
```

This installs:
- All core dependencies (FastAPI, Pydantic, SQLAlchemy, etc.)
- **New:** LangChain ecosystem (langchain, langchain-core, langchain-groq, langchain-mcp-adapters)
- **New:** CLI tools (click, rich)
- **New:** MCP server library
- Dev dependencies (pytest, ruff, pyright, psutil)

### 3. Verify installation

```bash
# Check LangChain versions
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
python -c "import langchain_core; print(f'LangChain Core: {langchain_core.__version__}')"
python -c "import langchain_groq; print(f'LangChain Groq: {langchain_groq.__version__}')"
python -c "import mcp; print(f'MCP: {mcp.__version__}')"

# Check CLI tools
python -c "import click; print('✓ Click')"
python -c "import rich; print('✓ Rich')"

# Check no import conflicts
python -c "from langchain.agents import create_react_agent; print('✓ Agents available')"
python -c "from langchain_groq import ChatGroq; print('✓ Groq available')"
```

## If You're on Windows with a .venv

The `.venv` folder at `backend/.venv` is committed (normally shouldn't be). Consider:

```bash
# Option A: Use the committed venv (skip venv setup)
# Just activate and install
cd backend
.venv\Scripts\activate
pip install -e ".[dev]"

# Option B: Create a fresh venv
cd backend
deactivate  # if currently activated
rmdir /s .venv  # Delete old one
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Then add `.venv/` to `.gitignore` if not already there.

## Troubleshooting

### Conflict: "langchain-core==1.7.4 incompatible with langchain==1.4.9"

**Cause:** Different major versions of LangChain packages installed.  
**Solution:** Use the versions in `pyproject.toml` which are all 0.1.x (compatible).

```bash
pip install langchain==0.1.14 langchain-core==0.1.44 -U
```

### Import Error: "No module named 'langchain_mcp_adapters'"

**Cause:** Package not installed.  
**Solution:**

```bash
pip install langchain-mcp-adapters==0.3.0
```

### No module named 'mcp'

**Cause:** MCP not installed.  
**Solution:**

```bash
pip install mcp==1.1.3
```

### On Windows: "ModuleNotFoundError: No module named 'fcntl'"

**Cause:** fcntl is Unix-only; MCP needs workaround.  
**Solution:** Use WSL2 for development (as recommended in the roadmap), or pin `mcp==1.0.0` (older version without Windows issues).

## Next Steps

1. Run tests to verify setup:
   ```bash
   pytest backend/tests/ -v
   ```

2. Start implementing Deliverable 1: `ai_pipeline/config.py`

3. Check that imports work:
   ```bash
   python -c "from ai_pipeline.config import get_ai_config; print(get_ai_config())"
   ```

## Documentation

- **Installed Versions:** `docs/versions.md` (create after first successful test)
- **LangChain Docs:** https://python.langchain.com/docs/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Groq API:** https://console.groq.com/docs

