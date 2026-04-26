"""
Draws the GUI and handles all rendering related tasks.
"""

import os

from PIL import Image, ImageDraw

from components import CenteredText, Divider, ScaledImage

WIDTH = 250
HEIGHT = 122


def _get_bird_image(state_data):
    image = state_data.get("bird_image")
    if isinstance(image, Image.Image):
        return image.convert("RGBA")

    image_path = state_data.get("bird_image_path")
    if image_path:
        try:
            return Image.open(image_path).convert("RGBA")
        except Exception:
            return None

    return None


def render_analyze_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    bird_name = str(state_data.get("bird_name", "Unknown Bird"))
    bird_img = _get_bird_image(state_data)

    image_top = 4
    image_bottom = HEIGHT - 22
    max_width = WIDTH - 8
    max_height = image_bottom - image_top

    components = [
        ScaledImage(4, image_top, max_width, max_height, bird_img, outline=0),
        Divider(WIDTH, image_bottom, color=0),
        CenteredText(WIDTH, image_bottom + 4, bird_name, color=0, font_size=10),
    ]

    for component in components:
        component.draw(draw, image)

    return image


def render(device, state_data=None, screen="analyze"):
    if state_data is None:
        state_data = {}

    match screen:
        case "analyze":
            image = render_analyze_screen(state_data)
        case _:
            image = render_analyze_screen(state_data)

    device.display(image)


def __main__():
    pass