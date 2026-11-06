"""Pytest configuration - load environment variables from .env before tests run."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from root directory
root_dir = Path(__file__).parent.parent
env_file = root_dir / ".env"

if env_file.exists():
    load_dotenv(env_file)
