# python
import logging
import sys
from typing import Optional

_FMT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(funcName)s | %(message)s"
_FORMATTER = logging.Formatter(_FMT)

_configured = False


def setup_logger(console_level: Optional[int] = logging.INFO, root_level: int = logging.DEBUG) -> None:
    """
    Central configuration: console-only logging.
    - console_level: None = no console handler, otherwise the level for StreamHandler
    - root_level: level for the root logger
    """
    global _configured
    root = logging.getLogger()

    # Remove existing handlers so repeated setup is idempotent
    for h in list(root.handlers):
        try:
            root.removeHandler(h)
        except Exception:
            pass

    root.setLevel(root_level)

    if console_level is not None:
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(_FORMATTER)
        ch.setLevel(console_level)
        root.addHandler(ch)

    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger by name. Perform a default setup if not configured yet.
    """
    if not _configured:
        setup_logger()
    return logging.getLogger(name)
