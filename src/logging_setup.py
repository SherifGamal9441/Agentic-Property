"""
Per-run file logging setup.

Call setup_file_logging() once at the start of a script to create
a timestamped .txt log file under logs/. All subsequent logging.getLogger()
calls from src.* nodes will write to this file automatically.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

_LOG_DIR = Path("logs")
_HANDLER: logging.FileHandler | None = None
_LOG_PATH: Path | None = None


def setup_file_logging(log_dir: str = "logs") -> Path:
    """
    Create a timestamped log file and attach a FileHandler to the root logger.

    Args:
        log_dir: Directory to store log files (created if missing).

    Returns:
        Path to the created log file.
    """
    global _HANDLER, _LOG_PATH

    dir_path = Path(log_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _LOG_PATH = dir_path / f"agent_run_{timestamp}.txt"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _HANDLER = logging.FileHandler(str(_LOG_PATH), encoding="utf-8")
    _HANDLER.setFormatter(fmt)
    _HANDLER.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.addHandler(_HANDLER)
    # Bump root logger from default WARNING to INFO if not already configured
    if root.level == logging.WARNING:
        root.setLevel(logging.INFO)

    return _LOG_PATH


def get_log_path() -> Path | None:
    """Return the path to the current run's log file, or None if not set up."""
    return _LOG_PATH
