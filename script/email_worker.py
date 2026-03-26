"""Worker entrypoint for roster assurance follow-up scheduler.

Run this on a short interval (or keep running) to process due emails:
    python -m script.email_worker
"""
from __future__ import annotations

import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils.scheduler import db
from utils.scheduler.service import run_forever, run_once


def configure_logging(level: str = "INFO") -> None:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "scheduler.log"

    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler, logging.StreamHandler()])


def main() -> None:
    parser = argparse.ArgumentParser(description="Roster Assurance Scheduler Worker")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    parser.add_argument("--interval", type=int, default=300, help="Poll interval in seconds (default: 300)")
    args = parser.parse_args()

    configure_logging()
    db.init_db()

    if args.once:
        run_once()
    else:
        run_forever(poll_interval_seconds=args.interval)


if __name__ == "__main__":
    main()

