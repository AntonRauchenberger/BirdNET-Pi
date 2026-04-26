"""
Controls which screen is active and handles the transition between them.
"""

import os

from renderer import render
from display_driver import create_device


def __main__():
    device = create_device()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bird_name = "Common chaffinch (Fringilla coelebs)"
    state_data = {
        "bird_name": bird_name,
        "bird_image_path": os.path.join(base_dir, "scripts", "gui", "assets", "images", "birds", bird_name + ".png"),
    }
    render(device=device, state_data=state_data, screen="analyze")

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    __main__()