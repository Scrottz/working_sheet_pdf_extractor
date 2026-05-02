import logging
import sys

_FMT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(funcName)s | %(message)s"
_FORMATTER = logging.Formatter(_FMT)


def setup_logger(console_level: int = logging.INFO, root_level: int = logging.DEBUG) -> None:

    root = logging.getLogger()

    root.setLevel(root_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_FORMATTER)
    handler.setLevel(console_level)
    root.addHandler(handler)

def get_logger(name: str = None) -> logging.Logger:
    return logging.getLogger(name)
