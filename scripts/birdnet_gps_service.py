#!/usr/bin/env python3
"""Runs GPS updates as a standalone background service."""

import logging
import signal
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from gps.service import GPSService
else:
    from .gps.service import GPSService


log = logging.getLogger(__name__)
_gps_service: GPSService | None = None


def _handle_shutdown(sig_num, _stack_frame):
    log.info("Caught shutdown signal %d, stopping GPS service...", sig_num)
    if _gps_service is not None:
        _gps_service.stop()


def main() -> None:
    global _gps_service

    log.info("Starting BirdNET GPS service")

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    _gps_service = GPSService()

    try:
        _gps_service.run()
    except Exception:
        log.exception("GPS service failed")
        raise

    log.info("BirdNET GPS service stopped")


def setup_logging() -> None:
    logger = logging.getLogger()
    formatter = logging.Formatter("[%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


if __name__ == "__main__":
    setup_logging()
    main()
