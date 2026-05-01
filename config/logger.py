"""
config/logger.py
Logging estructurado para el sistema de trading.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "trading_bot", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(log_dir / f"trading_{datetime.now():%Y%m%d}.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


logger = setup_logger()
