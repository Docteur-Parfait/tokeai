"""
Load and expose application configuration from environment variables.
All sensitive keys (e.g. GEMINI_API_KEY) are read from .env via python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of src/)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_project_root / ".env")


def get_gemini_api_key() -> str | None:
    """Return the Gemini API key from environment, or None if not set."""
    return os.getenv("GEMINI_API_KEY")


def get_logs_dir() -> Path:
    """Return the path to the logs directory (project root / logs)."""
    return _project_root / "logs"
