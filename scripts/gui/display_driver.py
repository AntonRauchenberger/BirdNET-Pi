"""
Prints the GUI on the display and handles all interactions with the display driver.
"""

from luma.emulator.device import pygame as luma_pygame

WIDTH = 250
HEIGHT = 122


def create_device():
    device = luma_pygame(width=WIDTH, height=HEIGHT)
    return device


if __name__ == "__main__":
    pass