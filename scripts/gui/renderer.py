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
        Text(0.4 * WIDTH + 5, 30, bird_scientific_name, font_size=12, color="black"),
        Text(0.4 * WIDTH + 5, 47, "Confidence", font_size=12, color="black"),
        Rectangle(0.4 * WIDTH + 5, 60, 90, 10, outline=1, fill=None),
        Rectangle(0.4 * WIDTH + 5, 60, confidence * 90, 10, outline=1, fill="black"),
        Text(0.4 * WIDTH + 5, 70, f"{confidence * 100:.0f} %", font_size=12, color="black"),
        Line(0.4 * WIDTH, 85, WIDTH - 5, 85, color="black", width=1),
        Text(0.4 * WIDTH + 5, 87, f"{state_data.get('timestamp', '')}", font_size=12, color="black"),
    ]

    for component in components:
        component.draw(draw, image)

    return image


def _get_header_components(header_text):
    components = [
        Rectangle(0, 0, WIDTH, 20, fill="black"),
        CenteredText(WIDTH, 2, header_text, font_size=16, color="white"),
    ]
    return components

def _get_pagination_components(current_page, total_pages=3):
    components = []
    dot_spacing = 12
    start_x = 10

    for i in range(total_pages):
        is_active = (i == current_page - 1)
        components.append(StatusDot(cx=start_x + i * dot_spacing, cy=HEIGHT - 10, r=3, fill="black" if is_active else "white", outline="black"))

    return components

def _get_footer_components(footer_text):
    components = [
        Divider(WIDTH, HEIGHT - 22, color="black", width=1),
        CenteredText(WIDTH, HEIGHT - 17, footer_text, font_size=12, color="black"),
        *_get_pagination_components(current_page=1, total_pages=3),
    ]
    return components


def render_sync_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    wlan_ssid = str(state_data.get("wlan_ssid", "Unknown Wi-Fi"))
    status = str(state_data.get("status", "Unknown Status"))
    last_sync = str(state_data.get("last_sync", "Unknown Time"))
    entries_to_sync = int(state_data.get("entries_to_sync", 0) or 0)

    components = [
        *_get_header_components("SYNC"),
        *_get_footer_components(footer_text="OK: Start sync"),
        Text(10, 27, f"WLAN: {wlan_ssid}", font_size=16, color="black"),
        Text(10, 42, f"Status: {status}", font_size=16, color="black"),
        Text(10, 57, f"Last Sync: {last_sync}", font_size=16, color="black"),
        Text(10, 72, f"Entries to Sync: {entries_to_sync}", font_size=16, color="black"),
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
        case "sync":
            image = render_sync_screen(state_data)
        case _:
            image = render_analyze_screen(state_data)

    device.display(image)


def __main__():
    pass