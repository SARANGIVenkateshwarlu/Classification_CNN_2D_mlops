"""Structured logging utility."""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "solar_panel_classifier",
    level: int = logging.INFO,
    log_file: Path = None,
    format_string: str = None,
) -> logging.Logger:
    """Configure a structured logger with console and optional file output."""
    if format_string is None:
        format_string = (
            "[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d — %(message)s"
        )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
