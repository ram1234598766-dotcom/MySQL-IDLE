#!/usr/bin/env python3
"""Build Windows icon and installer artwork from the supplied product logo."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGO_SOURCE = ASSETS / "mysqlidle-logo.png"

NAVY = (11, 24, 42)
DEEP_NAVY = (5, 14, 27)
BLUE = (37, 99, 235)
CYAN = (34, 211, 238)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)


def _font(size: int, bold: bool = False):
    candidates = (
        [r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
        if bold
        else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    )
    candidates += (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_mark(size: int) -> Image.Image:
    """Generate Windows icon sizes from the original supplied 96x96 logo."""
    with Image.open(LOGO_SOURCE) as source:
        if source.size != (96, 96):
            raise ValueError(f"Expected original 96x96 logo, got {source.size}.")
        return source.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


def _centered_text(
    draw: ImageDraw.ImageDraw, center_x: int, top: int, text: str, font, fill
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text((center_x - width // 2, top), text, font=font, fill=fill)


def _wizard_image() -> Image.Image:
    """Draw the Inno Setup side panel while keeping the user logo unchanged."""
    width, height = 164, 314
    image = Image.new("RGB", (width, height), NAVY)
    pixels = image.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(
            round(DEEP_NAVY[i] * (1 - t) + NAVY[i] * t) for i in range(3)
        )
        for x in range(width):
            pixels[x, y] = color

    draw = ImageDraw.Draw(image)
    draw.arc((-72, 8, 214, 282), 205, 335, fill=(28, 57, 88), width=2)
    draw.arc((-50, 32, 192, 255), 205, 335, fill=(20, 45, 72), width=2)
    draw.ellipse((38, 20, 126, 108), outline=(38, 85, 123), width=2)

    logo = _render_mark(72)
    image.paste(logo, ((width - 72) // 2, 28), logo)
    draw = ImageDraw.Draw(image)
    _centered_text(draw, width // 2, 118, "MySQL IDLE", _font(16, True), WHITE)
    _centered_text(draw, width // 2, 143, "SQL WORKSPACE", _font(8, True), CYAN)

    draw.rounded_rectangle((32, 171, 132, 174), radius=1, fill=BLUE)
    for x0, x1, label in ((12, 57, "QUERY"), (60, 105, "BROWSE"), (108, 153, "EXPORT")):
        draw.rounded_rectangle(
            (x0, 191, x1, 213), radius=5,
            fill=(18, 39, 61), outline=(39, 76, 108), width=1,
        )
        _centered_text(
            draw, (x0 + x1) // 2, 198, label, _font(6, True), (155, 240, 248)
        )

    draw.rounded_rectangle((20, 235, 144, 240), radius=2, fill=(46, 74, 102))
    draw.rounded_rectangle((20, 247, 117, 252), radius=2, fill=(36, 60, 86))
    draw.rounded_rectangle((20, 259, 132, 264), radius=2, fill=(36, 60, 86))
    draw.ellipse((20, 281, 27, 288), fill=CYAN)
    draw.text((34, 279), "MySQL + MariaDB", font=_font(7, True), fill=MUTED)
    return image


def _wizard_small() -> Image.Image:
    image = Image.new("RGB", (55, 55), WHITE)
    mark = _render_mark(47)
    image.paste(mark, ((55 - 47) // 2, (55 - 47) // 2), mark)
    return image


def main() -> None:
    if not LOGO_SOURCE.is_file():
        raise FileNotFoundError(f"Required app logo is missing: {LOGO_SOURCE}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = _render_mark(256)
    icon.save(
        ASSETS / "mysqlidle.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    _wizard_image().save(ASSETS / "wizard-image.bmp", format="BMP")
    _wizard_small().save(ASSETS / "wizard-small.bmp", format="BMP")
    print("Generated Windows ICO and installer artwork from assets/mysqlidle-logo.png.")


if __name__ == "__main__":
    main()
