"""
Prints the GUI on the display and handles all interactions with the display driver.
"""

from PIL import Image, ImageDraw
from luma.emulator.device import pygame as luma_pygame


WIDTH = 250
HEIGHT = 122


def create_device():
    device = luma_pygame(width=WIDTH, height=HEIGHT)
    return device


def render(device):
    image = Image.new("RGB", (WIDTH, HEIGHT), "black")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, WIDTH - 1, HEIGHT - 1], outline="white")
    device.display(image)


def __main__():
    device = create_device()
    render(device)

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    __main__()
