"""
Draws the GUI and handles all rendering related tasks.
"""

from PIL import Image, ImageDraw

try:
    from .components import (
        CenteredText,
        Divider,
        Line,
        Rectangle,
        ScaledImage,
        StatusDot,
        Text,
    )
except ImportError:
    from components import (
        CenteredText,
        Divider,
        Line,
        Rectangle,
        ScaledImage,
        StatusDot,
        Text,
    )

import os

WIDTH = 250
HEIGHT = 122


def _get_bird_image(bird_common_name, bird_scientific_name):
    formated_common_name = bird_common_name.lower()
    formated_scientific_name = bird_scientific_name.lower()

    image_path = os.path.join(
        os.path.dirname(__file__),
        "assets", "images", "birds",
        f"{formated_common_name} ({formated_scientific_name}).png",
    )

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
    bird_common_name = str(state_data.get("bird_common_name", "Unknown Bird"))
    bird_scientific_name = str(state_data.get("bird_scientific_name", ""))

    bird_img = _get_bird_image(bird_common_name, bird_scientific_name)

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

def _get_footer_components(footer_text, current_page=1, total_pages=5):
    components = [
        Divider(WIDTH, HEIGHT - 22, color="black", width=1),
        CenteredText(WIDTH, HEIGHT - 17, footer_text, font_size=12, color="black"),
        *_get_pagination_components(current_page=current_page, total_pages=total_pages),
    ]
    return components


def render_start_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    last_detected_bird = str(state_data.get("last_detected_bird", "No detections yet"))
    last_detected_confidence = str(state_data.get("last_detected_confidence", "0"))
    total_detections = str(state_data.get("total_detections", "0"))
    active_since_date = str(state_data.get("active since_date", "Unknown Date"))
    active_since_days = str(state_data.get("active since_days", "0"))
    system_name = str(state_data.get("system_name", "BirdNET-Pi"))

    components = [
        *_get_header_components(system_name),
        *_get_footer_components(footer_text="OK: Refresh", current_page=1),
        Text(10, 25, "LAST DETECTION", font_size=12, color="black"),
        Text(10, 35, f"{last_detected_bird}", font_size=16, color="black"),
        Text(WIDTH - 35, 35, f"{last_detected_confidence}%", font_size=16, color="black"),
        Line(8, 55, WIDTH - 8, 55, color="black", width=1),
        Line(WIDTH / 2, 55, WIDTH / 2, HEIGHT - 22, color="black", width=1),
        Text(10, 58, "TOTAL DETECTIONS", font_size=12, color="black"),
        Text(10, 69, f"{total_detections}", font_size=16, color="black"),
        Text(WIDTH / 2 + 10, 58, "ACTIVE SINCE", font_size=12, color="black"),
        Text(WIDTH / 2 + 10, 69, f"{active_since_date}", font_size=16, color="black"),
        Text(WIDTH / 2 + 10, 84, f"{active_since_days} days", font_size=12, color="black"),
    ]

    for component in components:
        component.draw(draw, image)

    return image

def render_live_analyze_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    live_analyze_active = bool(state_data.get("live_analyze_active", False))

    components = [
        *_get_header_components("Live Analyze"),
        *_get_footer_components(footer_text="OK: Switch ON/OFF", current_page=2),
        Text(8, 35, f"Show live results: {'ON' if live_analyze_active else 'OFF'}", font_size=16, color="black"),
    ]

    if live_analyze_active:
        components.append(CenteredText(WIDTH, 63, "Waiting for detection ...", font_size=12, color="black"))

    for component in components:
        component.draw(draw, image)

    return image

def render_list_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    page_size = 4
    bird_list_elements = []
    bird_list = state_data.get("bird_list", [])
    total_pages = max(1, (len(bird_list) + page_size - 1) // page_size)
    current_page = int(state_data.get("current_page", 1) or 1)
    current_page = max(1, min(total_pages, current_page))

    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    visible_birds = bird_list[start_index:end_index]

    scrollbar_x = WIDTH - 12
    scrollbar_y = 32
    scrollbar_height = 58
    thumb_height = max(12, scrollbar_height // total_pages)
    max_thumb_offset = max(0, scrollbar_height - thumb_height)
    thumb_offset = 0 if total_pages == 1 else int(((current_page - 1) / (total_pages - 1)) * max_thumb_offset)

    for idx, bird in enumerate(visible_birds):
        common_name = bird.get("common_name", "Unknown")
        amount = bird.get("amount", 0)

        bird_list_elements.append(Text(10, 27 + idx * 17, f"{common_name}", font_size=16, color="black"))
        bird_list_elements.append(Text(WIDTH - 45, 27 + idx * 17, f"x{amount}", font_size=16, color="black"))

    components = [
        *_get_header_components("MY BIRDS"),
        *_get_footer_components(footer_text="OK: Next page", current_page=3),
        Rectangle(scrollbar_x, scrollbar_y, 5, scrollbar_height, outline="black", fill="white"),
        Rectangle(scrollbar_x, scrollbar_y + thumb_offset, 5, thumb_height, outline="black", fill="black"),
        *bird_list_elements,
    ]

    for component in components:
        component.draw(draw, image)

    return image


def render_sync_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    wlan_ssid = str(state_data.get("wlan_ssid", "Unknown Wi-Fi"))
    app_url = str(state_data.get("app_url", "Unknown URL"))
    status = str(state_data.get("status", "Unknown Status"))
    entries_to_sync = int(state_data.get("entries_to_sync", 0) or 0)

    components = [
        *_get_header_components("SYNC"),
        *_get_footer_components(footer_text="OK: Hotspot ON/OFF", current_page=4),
        Text(8, 29, f"Status: {status}", font_size=16, color="black"),
        Text(8, 44, f"WLAN: {wlan_ssid}", font_size=16, color="black"),
        Text(8, 59, f"App-URL: {app_url}", font_size=16, color="black"),
        Text(8, 74, f"Entries to sync: {entries_to_sync}", font_size=16, color="black"),
    ]

    for component in components:
        component.draw(draw, image)

    return image


def render_gps_screen(state_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    status = str(state_data.get("status", "OFF"))
    latitude = str(state_data.get("latitude", "Unknown Latitude"))
    longitude = str(state_data.get("longitude", "Unknown Longitude"))
    last_update = str(state_data.get("last_update", "Unknown Time"))

    components = [
        *_get_header_components("GPS"),
        *_get_footer_components(footer_text="OK: GPS ON/OFF", current_page=5),
        Text(8, 29, f"Status: {status}", font_size=16, color="black"),
        Text(8, 44, f"Latitude: {latitude}", font_size=16, color="black"),
        Text(8, 59, f"Longitude: {longitude}", font_size=16, color="black"),
        Text(8, 74, f"Updated: {last_update}", font_size=16, color="black"),
    ]

    for component in components:
        component.draw(draw, image)

    return image


def render(device, state_data=None, screen="ANALYZE"):
    if state_data is None:
        state_data = {}

    screen_name = screen
    if hasattr(screen, "value"):
        screen_name = screen.value
    elif hasattr(screen, "name"):
        screen_name = screen.name

    screen_name = str(screen_name).upper()

    match screen_name:
        case "ANALYZE_RESULT":
            image = render_analyze_screen(state_data)
        case "LIVE_ANALYZE":
            image = render_live_analyze_screen(state_data)
        case "LIST":
            image = render_list_screen(state_data)
        case "SYNC":
            image = render_sync_screen(state_data)
        case "GPS":
            image = render_gps_screen(state_data)
        case "START":
            image = render_start_screen(state_data)
        case _:
            image = render_start_screen(state_data)

    device.display(image)


def __main__():
    pass