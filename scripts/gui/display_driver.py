"""
Prints the GUI on the display and handles all interactions with the display driver.
"""

import os
import sys
import importlib

WIDTH = 250
HEIGHT = 122


def _add_local_waveshare_driver_path():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    waveshare_lib = os.path.join(base_dir, "e-Paper", "RaspberryPi_JetsonNano", "python", "lib")
    if os.path.isdir(waveshare_lib) and waveshare_lib not in sys.path:
        sys.path.insert(0, waveshare_lib)


class EmulatorDevice:
    backend = "emulator"

    def __init__(self):
        luma_pygame = importlib.import_module("luma.emulator.device").pygame
        self._device = luma_pygame(width=WIDTH, height=HEIGHT)

    def display(self, image):
        self._device.display(image)

    def sleep(self):
        # Keep API-compatible with hardware device.
        return None


class Waveshare2in13V4Device:
    backend = "waveshare"

    def __init__(self, clear=True):
        _add_local_waveshare_driver_path()
        epd2in13_V4 = importlib.import_module("waveshare_epd.epd2in13_V4")

        self._driver = epd2in13_V4
        self._epd = epd2in13_V4.EPD()
        self._epd.init()
        if clear:
            self._epd.Clear(0xFF)

    def display(self, image):
        # E-Paper expects a 1-bit image buffer.
        bw_image = image.convert("1")
        self._epd.display(self._epd.getbuffer(bw_image))

    def sleep(self):
        self._epd.sleep()


def create_device(backend="auto", clear=True):
    backend = str(backend or "auto").lower()

    if backend == "emulator":
        return EmulatorDevice()

    if backend == "waveshare":
        return Waveshare2in13V4Device(clear=clear)

    if backend == "auto":
        try:
            return Waveshare2in13V4Device(clear=clear)
        except Exception:
            return EmulatorDevice()

    raise ValueError("Invalid backend. Use one of: auto, emulator, waveshare")


if __name__ == "__main__":
    pass