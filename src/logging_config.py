"""Structured logging configuration with rotation."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with rotation."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class TimingLogger:
    """Context manager for timing code blocks."""

    def __init__(self, logger: logging.Logger, stage: str):
        self.logger = logger
        self.stage = stage
        self.start_time = 0.0

    def __enter__(self):
        import time

        self.start_time = time.perf_counter()
        self.logger.info(f"Stage started: {self.stage}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        elapsed = time.perf_counter() - self.start_time
        if exc_type:
            self.logger.error(f"Stage failed: {self.stage} | elapsed={elapsed:.3f}s | error={exc_val}")
            return False
        self.logger.info(f"Stage completed: {self.stage} | elapsed={elapsed:.3f}s")
        return True
