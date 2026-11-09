import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"

if env_file.exists():
    load_dotenv(env_file)

import importlib
if 'app.config' in sys.modules:
    importlib.reload(sys.modules['app.config'])
