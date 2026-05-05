#!/usr/bin/env python3
"""Runs the display GUI as a standalone process."""

import json
import logging
import os
import signal
import socket
import sys
from types import SimpleNamespace

from gui.manager import GUIManager


log = logging.getLogger(__name__)

running = True
DISPLAY_GUI_SOCKET = '/tmp/birdnet_display_gui.sock'


def _handle_shutdown(sig_num, _stack_frame):
    global running
    log.info('Caught shutdown signal %d, stopping GUI service...', sig_num)
    running = False


def _to_detection(detection):
    try:
        return SimpleNamespace(
            common_name=detection.get('common_name', ''),
            scientific_name=detection.get('scientific_name', ''),
            confidence=float(detection.get('confidence', 0.0)),
        )
    except (ValueError, TypeError) as e:
        log.warning('Failed to parse detection entry %s: %s', detection, e)
        return None


def _receive_live_results(manager):
    if os.path.exists(DISPLAY_GUI_SOCKET):
        log.debug('Removing stale socket at %s', DISPLAY_GUI_SOCKET)
        os.remove(DISPLAY_GUI_SOCKET)

    log.info('Binding to socket %s', DISPLAY_GUI_SOCKET)
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.bind(DISPLAY_GUI_SOCKET)
        sock.settimeout(1.0)
        log.info('GUI service is listening for live analysis results')

        while running:
            try:
                message = sock.recv(65535)
            except socket.timeout:
                continue
            except OSError as e:
                log.error('Socket receive error: %s', e)
                break

            try:
                payload = json.loads(message.decode('utf-8'))
                detections = [d for d in (_to_detection(det) for det in payload.get('detections', [])) if d is not None]
                log.debug('Received %d detection(s), rendering on display', len(detections))
                manager.render_live_analyze_result(detections)
            except ValueError as e:
                log.warning('Failed to decode message payload: %s', e)
                continue
            except Exception as e:
                log.exception('Unexpected error while processing live result: %s', e)
                continue

    if os.path.exists(DISPLAY_GUI_SOCKET):
        os.remove(DISPLAY_GUI_SOCKET)
        log.debug('Removed socket at %s', DISPLAY_GUI_SOCKET)


def main():
    log.info('Starting BirdNET display GUI service')
    manager = GUIManager(backend="waveshare", clear=False)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    _receive_live_results(manager)

    log.info('GUI service shutting down, putting display to sleep')
    manager.device.sleep()
    log.info('GUI service stopped')


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
