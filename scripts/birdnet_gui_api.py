#!/usr/bin/env python3
"""Runs the GUI FastAPI as a standalone process."""

import logging
import signal
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from gui.api.api_manager import APIManager
else:
    from .gui.api.api_manager import APIManager

log = logging.getLogger(__name__)

running = True


def _handle_shutdown(sig_num, _stack_frame):
    global running
    log.info('Caught shutdown signal %d, stopping GUI FastAPI service...', sig_num)
    running = False


def main():
    log.info('Starting BirdNET GUI FastAPI service')

    host = "0.0.0.0"
    port = 2026

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    api_manager = APIManager(host, port)
    api_manager.run(host, port)


    log.info('GUI FastAPI service shutting down, putting display to sleep')
    log.info('GUI FastAPI service stopped')


def setup_logging():
    logger = logging.getLogger()
    formatter = logging.Formatter("[%(name)s][%(levelname)s] %(message)s")
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


if __name__ == "__main__":
    setup_logging()
    main()
