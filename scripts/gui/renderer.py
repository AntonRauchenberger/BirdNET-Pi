"""
Draws the GUI and handles all rendering related tasks.
"""

from PIL import Image, ImageDraw

from components import *

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

    confidence = float(state_data.get("confidence", 0.0) or 0.0)
    confidence = max(0.0, min(1.0, confidence))
    bird_fullname = str(state_data.get("bird_name", "Unknown Bird"))
    bird_common_name = bird_fullname.split(" (")[0]
    bird_scientific_name = bird_fullname.split(" (")[1][:-1] if " (" in bird_fullname else ""

    bird_img = _get_bird_image(state_data)

    image_top = 2
    image_bottom = HEIGHT - 2
    max_width = int(WIDTH * 0.4 - 2)
    max_height = image_bottom - image_top

    components = [
        ScaledImage(4, image_top, max_width, max_height, bird_img, outline=0),
        Line(0.4 * WIDTH, 10, 0.4 * WIDTH, HEIGHT - 10, color="black", width=1),
        Text(0.4 * WIDTH + 5, 15, bird_common_name, font_size=16, color="black"),
        Text(0.4 * WIDTH + 5, 30, bird_scientific_name, font_size=8, color="black"),
        Text(0.4 * WIDTH + 5, 50, "Konfidenz", font_size=8, color="black"),
        Rectangle(0.4 * WIDTH + 5, 60, 90, 10, outline=1, fill=None),
        Rectangle(0.4 * WIDTH + 5, 60, confidence * 90, 10, outline=1, fill="black"),
        Text(0.4 * WIDTH + 5, 72, f"{confidence * 100:.0f} %", font_size=8, color="black"),
        Line(0.4 * WIDTH, 85, WIDTH - 5, 85, color="black", width=1),
        Text(0.4 * WIDTH + 5, 90, f"{state_data.get('timestamp', '')}", font_size=8, color="black"),
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