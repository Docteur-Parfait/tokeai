"""
JSON file logging for TokeAI.
Writes one JSON object per line to logs/app_YYYYMMDD.json.
Provides get_logger() for application code and setup_logging() to configure once at startup.
Use extra={"action_type": "extraction_url"} etc. when logging for filtering in the UI.
"""

import logging
from datetime import datetime
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from src.config import get_logs_dir

# Logger name used by the app
APP_LOGGER_NAME = "tokeai"


def _ensure_logs_dir() -> Path:
    """Create logs directory if it does not exist; return its path."""
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _log_file_path() -> Path:
    """Return path to daily log file: logs/app_YYYYMMDD.json."""
    _ensure_logs_dir()
    date_str = datetime.utcnow().strftime("%Y%m%d")
    return get_logs_dir() / f"app_{date_str}.json"


def setup_logging() -> None:
    """
    Configure the application logger: one handler writing JSON lines to logs/app_YYYYMMDD.json.
    Call once at app startup (e.g. in app.py).
    """
    root = logging.getLogger(APP_LOGGER_NAME)
    if root.handlers:
        # Already configured (e.g. Streamlit reruns)
        return
    root.setLevel(logging.DEBUG)
    log_path = _log_file_path()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    # Include message, timestamp, level, module; extra fields (e.g. action_type) are added automatically
    formatter = JsonFormatter(
        "%(message)s %(asctime)s %(levelname)s %(module)s %(name)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger for the given name (or tokeai if None).
    Use extra={"action_type": "extraction_url"} etc. when logging for filtering in the UI.
    """
    setup_logging()
    logger_name = f"{APP_LOGGER_NAME}.{name}" if name else APP_LOGGER_NAME
    return logging.getLogger(logger_name)
