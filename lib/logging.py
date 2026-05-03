import logging
import sys

FMT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(funcName)s | %(message)s"
FORMATTER = logging.Formatter(FMT)


def setup_logger(console_level: int = logging.INFO, root_level: int = logging.DEBUG) -> None:
    root = logging.getLogger()

    root.setLevel(root_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(FORMATTER)
    handler.setLevel(console_level)
    root.addHandler(handler)

def get_logger(name: str = None) -> logging.Logger:
    return logging.getLogger(name)
