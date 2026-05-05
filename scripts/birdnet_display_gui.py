#!/usr/bin/env python3
"""Runs the display GUI as a standalone process."""

import json
import os
import signal
import socket
from types import SimpleNamespace

from gui.manager import GUIManager


running = True
DISPLAY_GUI_SOCKET = '/tmp/birdnet_display_gui.sock'


def _handle_shutdown(sig_num, _stack_frame):
    global running
    running = False


def _to_detection(detection):
    return SimpleNamespace(
        common_name=detection.get('common_name', ''),
        scientific_name=detection.get('scientific_name', ''),
        confidence=float(detection.get('confidence', 0.0)),
    )


def _receive_live_results(manager):
    if os.path.exists(DISPLAY_GUI_SOCKET):
        os.remove(DISPLAY_GUI_SOCKET)

    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.bind(DISPLAY_GUI_SOCKET)
        sock.settimeout(1.0)

        while running:
            try:
                message = sock.recv(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                payload = json.loads(message.decode('utf-8'))
                detections = [_to_detection(det) for det in payload.get('detections', [])]
                manager.render_live_analyze_result(detections)
            except (ValueError, TypeError):
                continue

    if os.path.exists(DISPLAY_GUI_SOCKET):
        os.remove(DISPLAY_GUI_SOCKET)


def main():
    manager = GUIManager(backend="waveshare", clear=False)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    _receive_live_results(manager)

    manager.device.sleep()


if __name__ == "__main__":
    main()
