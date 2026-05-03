"""
Prints the GUI on the display and handles all interactions with the display driver.
"""

import os
import sys
import importlib
import importlib.util

WIDTH = 250
HEIGHT = 122


def _configure_lgpio_pin_factory() -> bool:
    """Try switching gpiozero to lgpio backend for more reliable edge detection."""
    if importlib.util.find_spec("lgpio") is None:
        return False

    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

    try:
        gpiozero = importlib.import_module("gpiozero")
        lgpio_module = importlib.import_module("gpiozero.pins.lgpio")
        gpiozero.Device.pin_factory = lgpio_module.LGPIOFactory()
        return True
    except Exception:
        return False


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
        self._init_driver(clear=clear)

    def _init_driver(self, clear=True):
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

    def clear(self):
        self._epd.Clear(0xFF)

    def sleep(self):
        self._epd.sleep()


def create_device(backend="auto", clear=True):
    backend = str(backend or "auto").lower()

    if backend == "emulator":
        return EmulatorDevice()

    if backend == "waveshare":
        try:
            return Waveshare2in13V4Device(clear=clear)
        except RuntimeError as exc:
            # Retry with lgpio if RPi.GPIO edge detection fails.
            if "Failed to add edge detection" in str(exc) and _configure_lgpio_pin_factory():
                return Waveshare2in13V4Device(clear=clear)
            raise

    if backend == "auto":
        try:
            return Waveshare2in13V4Device(clear=clear)
        except Exception:
            return EmulatorDevice()

    raise ValueError("Invalid backend. Use one of: auto, emulator, waveshare")


if __name__ == "__main__":
    pass