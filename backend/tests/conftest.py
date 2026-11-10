import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test_client_id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test_client_secret")
os.environ.setdefault("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
os.environ.setdefault("SESSION_SECRET", "test_session_secret_for_signing_sessions")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("MAILBOX_MODE", "fake")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "srWrhCu6XlhSER2abmn1rmbWD7VDYLIIsqyhOFkbkfs=")

if env_file.exists():
    load_dotenv(env_file)

import importlib
if 'app.config' in sys.modules:
    importlib.reload(sys.modules['app.config'])
