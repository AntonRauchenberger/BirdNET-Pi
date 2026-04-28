"""
Controls which screen is active and handles the transition between them.
"""

import argparse
import os
import time

from renderer import render
from display_driver import create_device


def __main__():
    parser = argparse.ArgumentParser(description="BirdNET-Pi GUI test renderer")
    parser.add_argument("--backend", choices=["auto", "emulator", "waveshare"], default=os.getenv("GUI_BACKEND", "auto"))
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the e-paper display before rendering")
    parser.add_argument("--clear", action="store_true", help="Clear the e-paper display")
    args = parser.parse_args()

    device = create_device(backend=args.backend, clear=not args.no_clear)

    if args.clear and hasattr(device, "clear"):
        device.clear()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bird_name = "Common chaffinch (Fringilla coelebs)"
    state_data = {
        "bird_name": bird_name,
        "bird_image_path": os.path.join(base_dir, "scripts", "gui", "assets", "images", "birds", bird_name + ".png"),
        "confidence": 0.85,
        "timestamp": "2024-06-01 12:34:56",
    }
    render(device=device, state_data=state_data, screen="analyze")

    if getattr(device, "backend", "") == "waveshare":
        # Keep image visible briefly, then put panel to sleep.
        time.sleep(2)
        device.sleep()
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        device.sleep()

if __name__ == "__main__":
    __main__()