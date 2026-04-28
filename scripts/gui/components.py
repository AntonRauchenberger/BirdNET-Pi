import os
from PIL import Image as PILImage, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "assets/fonts/FSEX300.ttf")


def _load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


class Component:
    """Base class for all GUI components."""

    def draw(self, draw, canvas=None):
        raise NotImplementedError


class Text(Component):
    """Text at an absolute position."""

    def __init__(self, x, y, text, color=0, font_size=10):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.font_size = font_size

    def draw(self, draw, canvas=None):
        draw.text((self.x, self.y), self.text, fill=self.color, font=_load_font(self.font_size), antialiasing=False)


class CenteredText(Component):
    """Text centered horizontally within canvas_w at a fixed y."""

    def __init__(self, canvas_w, y, text, color=0, font_size=10):
        self.canvas_w = canvas_w
        self.y = y
        self.text = text
        self.color = color
        self.font_size = font_size

    def draw(self, draw, canvas=None):
        font = _load_font(self.font_size)
        bbox = draw.textbbox((0, 0), self.text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (self.canvas_w - text_w) // 2
        draw.text((x, self.y), self.text, fill=self.color, font=font, antialiasing=False)


class Rectangle(Component):
    """Rectangle with optional outline and fill."""

    def __init__(self, x, y, w, h, outline=0, fill=None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.outline = outline
        self.fill = fill

    def draw(self, draw, canvas=None):
        draw.rectangle(
            [self.x, self.y, self.x + self.w, self.y + self.h],
            outline=self.outline, fill=self.fill,
        )


class Circle(Component):
    """Circle defined by center (cx, cy) and radius r."""

    def __init__(self, cx, cy, r, outline=0, fill=None):
        self.cx, self.cy, self.r = cx, cy, r
        self.outline = outline
        self.fill = fill

    def draw(self, draw, canvas=None):
        draw.ellipse(
            [self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r],
            outline=self.outline, fill=self.fill,
        )


class Line(Component):
    """Straight line from (x1, y1) to (x2, y2)."""

    def __init__(self, x1, y1, x2, y2, color=0, width=1):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.color = color
        self.width = width

    def draw(self, draw, canvas=None):
        draw.line([self.x1, self.y1, self.x2, self.y2], fill=self.color, width=self.width)


class Divider(Component):
    """Full-width horizontal dividing line at a fixed y."""

    def __init__(self, canvas_w, y, color=0, width=1):
        self.canvas_w = canvas_w
        self.y = y
        self.color = color
        self.width = width

    def draw(self, draw, canvas=None):
        draw.line([0, self.y, self.canvas_w, self.y], fill=self.color, width=self.width)


class ProgressBar(Component):
    """Horizontal progress bar. value in [0, max_value]."""

    def __init__(self, x, y, w, h, value, max_value=100, fill=0, outline=0, bg=None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.value = value
        self.max_value = max_value
        self.fill = fill
        self.outline = outline
        self.bg = bg

    def draw(self, draw, canvas=None):
        draw.rectangle(
            [self.x, self.y, self.x + self.w, self.y + self.h],
            outline=self.outline, fill=self.bg,
        )
        ratio = max(0.0, min(1.0, self.value / self.max_value))
        filled_w = int(self.w * ratio)
        if filled_w > 0:
            draw.rectangle(
                [self.x, self.y, self.x + filled_w, self.y + self.h],
                fill=self.fill,
            )


class StatusDot(Component):
    """Small filled circle used as a status indicator."""

    def __init__(self, cx, cy, r=4, fill=0, outline=None):
        self.cx, self.cy, self.r = cx, cy, r
        self.fill = fill
        self.outline = outline if outline is not None else fill

    def draw(self, draw, canvas=None):
        draw.ellipse(
            [self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r],
            fill=self.fill, outline=self.outline,
        )


class Label(Component):
    """Text with a filled background rectangle (badge style)."""

    def __init__(self, x, y, text, text_color=255, bg_color=0, padding=2, font_size=10):
        self.x, self.y = x, y
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.padding = padding
        self.font_size = font_size

    def draw(self, draw, canvas=None):
        font = _load_font(self.font_size)
        bbox = draw.textbbox((0, 0), self.text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        p = self.padding
        draw.rectangle(
            [self.x, self.y, self.x + text_w + 2 * p, self.y + text_h + 2 * p],
            fill=self.bg_color,
        )
        draw.text((self.x + p, self.y + p), self.text, fill=self.text_color, font=font, antialiasing=False)


class Icon(Component):
    """Pastes a PIL image at (x, y) scaled to fit within (w, h)."""

    def __init__(self, x, y, w, h, image):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.image = image

    def draw(self, draw, canvas=None):
        if canvas is None or self.image is None:
            return
        img = self.image.convert("RGBA")
        img.thumbnail((self.w, self.h), PILImage.Resampling.LANCZOS)
        canvas.paste(img, (self.x, self.y), img)


class ScaledImage(Component):
    """
    Pastes a PIL image centered within a bounding box, scaled to fit while
    preserving the aspect ratio. Draws a placeholder rectangle when image is None.
    """

    def __init__(self, x, y, max_w, max_h, image, outline=0):
        self.x, self.y = x, y
        self.max_w, self.max_h = max_w, max_h
        self.image = image
        self.outline = outline

    def draw(self, draw, canvas=None):
        if self.image is None or canvas is None:
            draw.rectangle(
                [self.x, self.y, self.x + self.max_w, self.y + self.max_h],
                outline=self.outline,
            )
            return
        img = self.image.convert("RGBA")
        img.thumbnail((self.max_w, self.max_h), PILImage.Resampling.LANCZOS)
        paste_x = self.x + (self.max_w - img.width) // 2
        paste_y = self.y + (self.max_h - img.height) // 2
        canvas.paste(img, (paste_x, paste_y), img)

